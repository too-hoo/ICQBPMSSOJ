#!/usr/bin/env python
# -*-encoding:UTF-8-*-

import hashlib
import json
import os
import re
import shutil
import smtplib
import time
from datetime import datetime

import pytz
import requests
from django.conf import settings
from django.utils import timezone
from requests.exceptions import RequestException

from account.decorators import super_admin_required
from account.models import User
from contest.models import Contest
from judge.dispatcher import process_pending_task
from options.options import SysOptions
from problem.models import Problem
from submission.models import Submission
from myutils.api import APIView, CSRFExemptAPIView, validate_serializer
from myutils.shortcuts import send_email, get_env
from myutils.xss_filter import XSSHtml
from .models import JudgeServer
from .serializers import (CreateEditWebsiteConfigSerializer,
                          CreateSMTPConfigSerializer, EditSMTPConfigSerializer,
                          JudgeServerHeartbeatSerializer,
                          JudgeServerSerializer, TestSMTPConfigSerializer, EditJudgeServerSerializer)


class SMTPAPI(APIView):
    # 邮件功能实现接口
    @super_admin_required
    def get(self, request):
        smtp = SysOptions.smtp_config
        if not smtp:
            return self.success(None)
        smtp.pop("password")
        return self.success(smtp)

    @super_admin_required
    @validate_serializer(CreateSMTPConfigSerializer)
    def post(self, request):
        # 配置邮件信息，smtp_config默认是{}
        SysOptions.smtp_config = request.data
        return self.success()

    @super_admin_required
    @validate_serializer(EditSMTPConfigSerializer)
    def put(self, request):
        # 编辑邮件信息
        smtp = SysOptions.smtp_config
        data = request.data
        for item in ["server", "port", "email", "tls"]:
            smtp[item] = data[item]
        # 假如提供密码就设置邮箱配置的密码为请求修改的数据里面的密码，
        # 否则不做修改，保持初始配置时候的密码
        if "password" in data:
            smtp["password"] = data["password"]
        SysOptions.smtp_config = smtp
        return self.success()


class SMTPTestAPI(APIView):
    # 发送邮件测试类
    @super_admin_required
    @validate_serializer(TestSMTPConfigSerializer)
    def post(self, request):
        # 创建邮件，发送
        if not SysOptions.smtp_config:
            return self.error("Please setup SMTP config at first")
        try:
            send_email(smtp_config=SysOptions.smtp_config,
                       from_name=SysOptions.website_name_shortcut,
                       to_name=request.user.username,
                       to_email=request.data["email"],
                       subject="You have successfully configured SMTP",
                       content="You have successfully configured SMTP")
        # 成功就返回，同时捕捉错误，一般是编码错误
        except smtplib.SMTPResponseException as e:
            # guess error message encoding
            # 猜测是信息编码的错误，如果是使用qq邮箱，以gbk解码，还是出错就使用utf-8解码
            msg = b"Failed to send email"
            try:
                msg = e.smtp_error
                # qq mail
                msg = msg.decode("gbk")
            except Exception:
                msg = msg.decode("utf-8", "ignore")
            return self.error(msg)
        except Exception as e:
            msg = str(e)
            return self.error(msg)
        return self.success()


class WebsiteConfigAPI(APIView):
    # 网站配置的API
    def get(self, request):
        # 获取网站的信息，不需要登录就可以获取
        ret = {key: getattr(SysOptions, key) for key in
               ["website_base_url", "website_name", "website_name_shortcut",
                "website_footer", "allow_register", "submission_list_show_all"]}
        return self.success(ret)

    @super_admin_required
    @validate_serializer(CreateEditWebsiteConfigSerializer)
    def post(self, request):
        # 网站信息配置
        for k, v in request.data.items():
            # 单独配置footer，清空内容，经过clean之后仅仅返回安全的html标签了，css，js都会被过滤掉
            if k == "website_footer":
                with XSSHtml() as parser:
                    v = parser.clean(v)
            setattr(SysOptions, k, v)
        return self.success()


class JudgeServerAPI(APIView):
    # 判题服务器功能实现
    @super_admin_required
    def get(self, request):
        # 从数据库里面按照last_heartbeat来查询数据，获取信息
        servers = JudgeServer.objects.all().order_by("-last_heartbeat")
        # 返回系统存放的服务器口令和经过序列化的Server信息
        return self.success({"token": SysOptions.judge_server_token,
                             "servers": JudgeServerSerializer(servers, many=True).data})

    @super_admin_required
    def delete(self, request):
        # 删除Judge_Server的信息，使用URL的方式传数据就使用GET.get
        hostname = request.GET.get("hostname")
        if hostname:
            JudgeServer.objects.filter(hostname=hostname).delete()
        return self.success()

    @validate_serializer(EditJudgeServerSerializer)
    @super_admin_required
    def put(self, request):
        # 修改Judge_Server的信息：关闭测评机，使用JSON的方式传数据就是用data.get, 注意后面的False
        is_disabled = request.data.get("is_disabled", False)   # is_disabled ->True
        print(is_disabled)
        JudgeServer.objects.filter(id=request.data["id"]).update(is_disabled=is_disabled)
        if not is_disabled:
            # 解析排在队列里面的任务
            process_pending_task()
        return self.success()


class JudgeServerHeartbeatAPI(CSRFExemptAPIView):
    # 判题服务器心跳响应功能接口
    @validate_serializer(JudgeServerHeartbeatSerializer)
    def post(self, request):
        # 获取数据和请求头加密口令字段HTTP_X_JUDGE_SERVER_TOKEN
        data = request.data
        client_token = request.META.get("HTTP_X_JUDGE_SERVER_TOKEN")
        # 使用摘要算法判断口令是否相等
        if hashlib.sha256(SysOptions.judge_server_token.encode("utf-8")).hexdigest() != client_token:
            return self.error("Invalid token")

        try:
            # 配置服务其的信息
            server = JudgeServer.objects.get(hostname=data["hostname"])
            server.judger_version = data["judger_version"]
            server.cpu_core = data["cpu_core"]
            server.memory_usage = data["memory"]
            server.cpu_usage = data["cpu"]
            server.service_url = data["service_url"]
            server.ip = request.ip
            server.last_heartbeat = timezone.now()
            server.save()
        except JudgeServer.DoesNotExist:
            # 若果不存在就配置，例如刚开始hostname不存在的
            JudgeServer.objects.create(hostname=data["hostname"],
                                       judger_version=data["judger_version"],
                                       cpu_core=data["cpu_core"],
                                       memory_usage=data["memory"],
                                       cpu_usage=data["cpu"],
                                       ip=request.META["REMOTE_ADDR"],
                                       service_url=data["service_url"],
                                       last_heartbeat=timezone.now(),
                                       )
            # 新server上线 处理队列中的任务，防止没有新的提交而导致一直waiting
            # 将处于等待的（CacheKey.waiting_queue）任务加载到异步队列里面去
            process_pending_task()

        return self.success()


class LanguagesAPI(APIView):
    # 语言选择配置
    def get(self, request):
        return self.success({"languages": SysOptions.languages, "spj_languages": SysOptions.spj_languages})


class TestCasePruneAPI(APIView):
    # 测试用例修改功能接口
    # 删除没有归属题目的测试用例
    @super_admin_required
    def get(self, request):
        """
        return orphan test_case list
        # 返回孤儿测试用例（被隔离的用例）列表
        """
        ret_data = []
        # 调用get_orphan_ids返回孤儿测试用例， 最终将会被移除
        dir_to_be_removed = self.get_orphan_ids()

        # return an iterator
        for d in os.scandir(settings.TEST_CASE_DIR):
            if d.name in dir_to_be_removed:
                ret_data.append({"id": d.name, "create_time": d.stat().st_mtime})
        return self.success(ret_data)

    @super_admin_required
    def delete(self, request):
        # id就是传入的valid_id
        # 删除多余的测试用例
        test_case_id = request.GET.get("id")
        if test_case_id:
            self.delete_one(test_case_id)
            return self.success()
        # 删除孤儿测试列表的测试样例
        for id in self.get_orphan_ids():
            self.delete_one(id)
        return self.success()

    @staticmethod
    def get_orphan_ids():
        # 静态方法，获取孤儿测试用例的dir，首先获取ID
        db_ids = Problem.objects.all().values_list("test_case_id", flat=True)
        # print(db_ids)       #<QuerySet []>
        disk_ids = os.listdir(settings.TEST_CASE_DIR)
        # print(disk_ids)     #[]
        test_case_re = re.compile(r"^[a-zA-Z0-9]{32}$")
        # print(test_case_re)   # 符合正则表达式的筛选出来
        disk_ids = filter(lambda f: test_case_re.match(f), disk_ids)
        # print(disk_ids)     # <filter object at 0x7f5f0dbb96a0>
        # print(list(set(disk_ids) - set(db_ids)))      #[]  因为没有这样一个目录，所以最后返回空列表
        return list(set(disk_ids) - set(db_ids))

    @staticmethod
    def delete_one(id):
        # 删除一个孤儿测试用例，本方法被上面的delete调用
        test_case_dir = os.path.join(settings.TEST_CASE_DIR, id)
        if os.path.isdir(test_case_dir):
            shutil.rmtree(test_case_dir, ignore_errors=True)


class ReleaseNotesAPI(APIView):
    # 版本记录
    def get(self, request):
        try:
            # 链接超时：3秒
            resp = requests.get("https://icqbpmssoj/data.json?_=" + str(time.time()),
                                timeout=3)
            releases = resp.json()
        except (RequestException, ValueError):
            # 其实找不到在这里已经返回了下面的是找得到才会执行，应为上面的那个路径是虚构的，所以不会执行下面的语句
            return self.success()
        with open("docs/data.json", "r") as f:
            # 本地最新版本
            local_version = json.load(f)["update"][0]["version"]
        releases["local_version"] = local_version
        return self.success(releases)


class DashboardInfoAPI(APIView):
    # 仪表盘信息功能接口，从数据库里面查询出数据，显示在网站上面，用作提示
    def get(self, request):
        # 设置时间
        today = datetime.today()
        # 今天提交总数计数
        today_submission_count = Submission.objects.filter(
            create_time__gte=datetime(today.year, today.month, today.day, 0, 0, tzinfo=pytz.UTC)).count()
        # 最近举办的比赛计数
        recent_contest_count = Contest.objects.exclude(end_time__lt=timezone.now()).count()
        # 判题服务器的处理正常提交题目计数
        judge_server_count = len(list(filter(lambda x: x.status == "normal", JudgeServer.objects.all())))
        # 用户量计数、最近比赛计数、今天提交总数、评测机计数、环境
        return self.success({
            "user_count": User.objects.count(),
            "recent_contest_count": recent_contest_count,
            "today_submission_count": today_submission_count,
            "judge_server_count": judge_server_count,
            "env": {
                "FORCE_HTTPS": get_env("FORCE_HTTPS", default=False),
                "STATIC_CDN_HOST": get_env("STATIC_CDN_HOST", default="")
            }
        })
