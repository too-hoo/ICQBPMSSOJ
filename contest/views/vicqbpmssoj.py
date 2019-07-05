#!/usr/bin/env python
# -*-encoding:UTF-8-*-

import io

import xlsxwriter   # 表格

from django.http import HttpResponse
from django.utils.timezone import now
from django.core.cache import cache

from problem.models import Problem
from myutils.api import APIView, validate_serializer
from myutils.constants import CacheKey
from myutils.shortcuts import datetime2str
from account.models import AdminType
from account.decorators import login_required, check_contest_permission

from myutils.constants import ContestRuleType, ContestStatus
from ..models import ContestAnnouncement, Contest, OIContestRank, ACMContestRank
from ..serializers import ContestAnnouncementSerializer
from ..serializers import ContestSerializer, ContestPasswordVerifySerializer
from ..serializers import OIContestRankSerializer, ACMContestRankSerializer


class ContestAnnouncementListAPI(APIView):
    # 创建比赛通知，使用传入的ID进行查询。前提是要有参加比赛的权限
    @check_contest_permission(check_type="announcements")
    def get(self, request):
        contest_id = request.GET.get("contest_id")
        if not contest_id:
            return self.error("Invalid parameter, contest_id is required")
        data = ContestAnnouncement.objects.select_related("created_by").filter(contest_id=contest_id, visible=True)
        # 最大的max_id
        max_id = request.GET.get("max_id")
        if max_id:
            data = data.filter(id__gt=max_id)
        # 返回比赛通知的序列化数据
        return self.success(ContestAnnouncementSerializer(data, many=True).data)


class ContestAPI(APIView):
    def get(self, request):
        id = request.GET.get("id")
        if not id:
            return self.error("Invalid parameter, id is required")
        try:
            contest = Contest.objects.get(id=id, visible=True)
        except Contest.DoesNotExist:
            return self.error("Contest does not exist")
        data = ContestSerializer(contest).data
        data["now"] = datetime2str(now())
        return self.success(data)


class ContestListAPI(APIView):
    def get(self, request):
        contests = Contest.objects.select_related("created_by").filter(visible=True)
        keyword = request.GET.get("keyword")
        rule_type = request.GET.get("rule_type")
        status = request.GET.get("status")
        if keyword:
            contests = contests.filter(title__contains=keyword)
        if rule_type:
            contests = contests.filter(rule_type=rule_type)
        if status:
            cur = now()
            if status == ContestStatus.CONTEST_NOT_START:
                contests = contests.filter(start_time__gt=cur)
            elif status == ContestStatus.CONTEST_ENDED:
                contests = contests.filter(end_time__lt=cur)
            else:
                contests = contests.filter(start_time__lte=cur, end_time__gte=cur)
        return self.success(self.paginate_data(request, contests, ContestSerializer))


class ContestPasswordVerifyAPI(APIView):
    # 用户使用密码登录参加比赛
    @validate_serializer(ContestPasswordVerifySerializer)
    @login_required
    def post(self, request):
        data = request.data
        try:
            # 使用条件查询password__isnull=False，说明需要密码
            contest = Contest.objects.get(id=data["contest_id"], visible=True, password__isnull=False)
        except Contest.DoesNotExist:
            return self.error("Contest does not exist")
        if contest.password != data["password"]:
            return self.error("Wrong password")

        # 到这里说明密码验证OK，日过请求的session里面没有accessible_contests，
        # 就将它设为控列表，否则添加比赛的ID
        if "accessible_contests" not in request.session:
            request.session["accessible_contests"] = []
        request.session["accessible_contests"].append(contest.id)
        # 参考：https://docs.djangoproject.com/en/dev/topics/http/sessions/#when-sessions-are-saved
        request.session.modified = True
        return self.success(True)


class ContestAccessAPI(APIView):
    # 参加比赛需要登录，先用装饰器检测一下，用户登录参加比赛
    @login_required
    def get(self, request):
        contest_id = request.GET.get("contest_id")
        if not contest_id:
            return self.error()
        # 返回在session里面存放的contest_id
        return self.success({"access": int(contest_id) in request.session.get("accessible_contests", [])})


class ContestRankAPI(APIView):
    # 获得比赛的排名，使用的是get方法
    def get_rank(self):
        # 根据情况获得排名
        if self.contest.rule_type == ContestRuleType.ACM:
            return ACMContestRank.objects.filter(contest=self.contest,
                                                 user__admin_type=AdminType.REGULAR_USER,
                                                 user__is_disabled=False).\
                select_related("user").order_by("-accepted_number", "total_time")
        else:
            return OIContestRank.objects.filter(contest=self.contest,
                                                user__admin_type=AdminType.REGULAR_USER,
                                                user__is_disabled=False). \
                select_related("user").order_by("-total_score")

    def column_string(self, n):
        string = ""
        while n > 0:
            n, remainder = divmod(n - 1, 26)
            string = chr(65 + remainder) + string
        return string

    # 检查申请获取比赛排名的用户是否有权限先
    @check_contest_permission(check_type="ranks")
    def get(self, request):
        # download_csv，force_refresh这些数据都是要另外传入的，单单申请比赛排名是不用到
        download_csv = request.GET.get("download_csv")
        force_refresh = request.GET.get("force_refresh")
        is_contest_admin = request.user.is_authenticated() and request.user.is_contest_admin(self.contest)
        # 根据比赛类型选择序列化器
        if self.contest.rule_type == ContestRuleType.OI:
            serializer = OIContestRankSerializer
        else:
            serializer = ACMContestRankSerializer

        if force_refresh == "1" and is_contest_admin:
            # 强行更新True和是超级用户时，返回排名，qs是question status
            qs = self.get_rank()
        else:
            # 否则使用缓存即机制，将数据输出到缓存里面
            cache_key = f"{CacheKey.contest_rank_cache}:{self.contest.id}"
            qs = cache.get(cache_key)
            if not qs:
                qs = self.get_rank()
                cache.set(cache_key, qs)

        # 请求数据有下载csv表格的请求
        if download_csv:
            data = serializer(qs, many=True, is_contest_admin=is_contest_admin).data
            # 查找出比赛问题的答题状态
            contest_problems = Problem.objects.filter(contest=self.contest, visible=True).order_by("_id")
            problem_ids = [item.id for item in contest_problems]

            # 使用io比特流
            f = io.BytesIO()
            workbook = xlsxwriter.Workbook(f)
            worksheet = workbook.add_worksheet()
            worksheet.write("A1", "User ID")
            worksheet.write("B1", "Username")
            worksheet.write("C1", "Real Name")
            if self.contest.rule_type == ContestRuleType.OI:
                # 比赛类型为OI
                worksheet.write("D1", "Total Score")
                for item in range(contest_problems.count()):
                    worksheet.write(self.column_string(5 + item) + "1", f"{contest_problems[item].title}")
                for index, item in enumerate(data):
                    worksheet.write_string(index + 1, 0, str(item["user"]["id"]))
                    worksheet.write_string(index + 1, 1, item["user"]["username"])
                    worksheet.write_string(index + 1, 2, item["user"]["real_name"] or "")
                    worksheet.write_string(index + 1, 3, str(item["total_score"]))
                    for k, v in item["submission_info"].items():
                        worksheet.write_string(index + 1, 4 + problem_ids.index(int(k)), str(v))
            else:
                # 比赛类型为ACM
                worksheet.write("D1", "AC")
                worksheet.write("E1", "Total Submission")
                worksheet.write("F1", "Total Time")
                for item in range(contest_problems.count()):
                    worksheet.write(self.column_string(7 + item) + "1", f"{contest_problems[item].title}")

                for index, item in enumerate(data):
                    worksheet.write_string(index + 1, 0, str(item["user"]["id"]))
                    worksheet.write_string(index + 1, 1, item["user"]["username"])
                    worksheet.write_string(index + 1, 2, item["user"]["real_name"] or "")
                    worksheet.write_string(index + 1, 3, str(item["accepted_number"]))
                    worksheet.write_string(index + 1, 4, str(item["submission_number"]))
                    worksheet.write_string(index + 1, 5, str(item["total_time"]))
                    for k, v in item["submission_info"].items():
                        worksheet.write_string(index + 1, 6 + problem_ids.index(int(k)), str(v["is_ac"]))

            # 关闭工作本，返回响应
            workbook.close()
            f.seek(0)
            response = HttpResponse(f.read())
            response["Content-Disposition"] = f"attachment; filename=content-{self.contest.id}-rank.xlsx"
            response["Content-Type"] = "application/xlsx"
            return response

        # 分页显示问题状态question status
        page_qs = self.paginate_data(request, qs)
        page_qs["results"] = serializer(page_qs["results"], many=True, is_contest_admin=is_contest_admin).data
        return self.success(page_qs)
