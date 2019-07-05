from django.test import TestCase

import hashlib
from unittest import mock

from django.conf import settings
from django.utils import timezone

from options.options import SysOptions
from myutils.api.tests import APITestCase
from .models import JudgeServer


class SMTPConfigTest(APITestCase):
    # 邮件配置测试
    def setUp(self):
        self.user = self.create_super_admin()
        self.url = self.reverse("smtp_admin_api")
        self.password = "testtest"

    def test_create_smtp_config(self):
        # 测试创建邮件配置信息，返回resp供调用
        data = {"server": "smtp.test.com", "email": "test@test.com", "port": 465,
                "tls": True, "password": self.password}
        resp = self.client.post(self.url, data=data)
        # print(resp.data)     #{'error': None, 'data': None}
        self.assertSuccess(resp)
        self.assertTrue("password" not in resp.data)
        return resp

    def test_edit_without_password(self):
        # 测试没有密码的情况下编辑邮件
        self.test_create_smtp_config()
        data = {"server": "smtp1.test.com", "email": "test2@test.com", "port": 465,
                "tls": True}
        resp = self.client.put(self.url, data=data)
        self.assertSuccess(resp)

    def test_edit_without_password1(self):
        # 有提供密码字段，但是值为NULL，说明密码不是决定因素，不要也可以
        self.test_create_smtp_config()
        data = {"server": "smtp.test.com", "email": "test@test.com", "port": 465,
                "tls": True, "password": ""}
        resp = self.client.put(self.url, data=data)
        self.assertSuccess(resp)

    def test_edit_with_password(self):
        # 配置新密码同样没影响 testtest -> newpassword
        self.test_create_smtp_config()
        data = {"server": "smtp1.test.com", "email": "test2@test.com", "port": 465,
                "tls": True, "password": "newpassword"}
        resp = self.client.put(self.url, data=data)
        self.assertSuccess(resp)

    @mock.patch("conf.views.send_email")
    def test_test_smtp(self, mocked_send_email):
        # 测试发送邮件
        url = self.reverse("smtp_test_api")
        self.test_create_smtp_config()
        # 邮箱地址: test@test.com
        resp = self.client.post(url, data={"email": "test@test.com"})
        self.assertSuccess(resp)
        mocked_send_email.assert_called_once()


class WebsiteConfigAPITest(APITestCase):
    # 网站信息配置
    def test_create_website_config(self):
        # 测试城建网站信息配置，要求是有管理员权限
        self.create_super_admin()
        url = self.reverse("website_config_api")
        data = {"website_base_url": "http://icqbpmssoj.com", "website_name": "icqbpmssoj",
                "website_name_shortcut": "icqbpmssoj", "website_footer": "<a>test</a>",
                "allow_register": True, "submission_list_show_all": False}
        resp = self.client.post(url, data=data)
        self.assertSuccess(resp)

    def test_edit_website_config(self):
        # 测试编辑网站的配置，
        # 单独配置footer，清空内容，经过clean之后仅仅返回安全的html标签了，css，js都会被过滤掉
        self.create_super_admin()
        url = self.reverse("website_config_api")
        data = {"website_base_url": "http://icqbpmssoj.com", "website_name": "icqbpmssoj",
                "website_name_shortcut": "icqbpmssoj", "website_footer": "<img onerror=alert(1) src=#>",
                "allow_register": True, "submission_list_show_all": False}
        resp = self.client.post(url, data=data)
        self.assertSuccess(resp)
        self.assertEqual(SysOptions.website_footer, "<img src=\"#\" />")

    def test_get_website_config(self):
        # do not need to login
        url = self.reverse("website_info_api")
        resp = self.client.get(url)
        self.assertSuccess(resp)


class JudgeServerHeartbeatTest(APITestCase):
    # 判题服务器心跳测试
    def setUp(self):
        self.url = self.reverse("judge_server_heartbeat_api")
        self.data = {"hostname": "testhostname", "judger_version": "1.0.1", "cpu_core": 2,
                     "cpu": 90.5, "memory": 80.3, "action": "heartbeat", "service_url": "http://127.0.0.1"}
        # 设置口令，并使用摘要算法加密
        self.token = "test"
        self.hashed_token = hashlib.sha256(self.token.encode("utf-8")).hexdigest()
        # 设置系统的口令，和请求头数据
        SysOptions.judge_server_token = self.token
        self.headers = {"HTTP_X_JUDGE_SERVER_TOKEN": self.hashed_token, settings.IP_HEADER: "1.2.3.4"}

    def test_new_heartbeat(self):
        # 测试新的心跳，传入数据，解析请求头
        resp = self.client.post(self.url, data=self.data, **self.headers)
        self.assertSuccess(resp)
        # 查询judgeServer的数据库
        server = JudgeServer.objects.first()
        self.assertEqual(server.ip, "127.0.0.1")

    def test_update_heartbeat(self):
        # 更新评测机版本
        self.test_new_heartbeat()
        data = self.data
        data["judger_version"] = "1.0.2"
        resp = self.client.post(self.url, data=data, **self.headers)
        self.assertSuccess(resp)
        self.assertEqual(JudgeServer.objects.get(hostname=self.data["hostname"]).judger_version, data["judger_version"])


class JudgeServerAPITest(APITestCase):
    # 评判机接口
    def setUp(self):
        # 创建评测机，他会自动生成一个ID
        self.server = JudgeServer.objects.create(**{"hostname": "testhostname", "judger_version": "1.0.4",
                                                    "cpu_core": 4, "cpu_usage": 90.5, "memory_usage": 80.3,
                                                    "last_heartbeat": timezone.now()})
        self.url = self.reverse("judge_server_api")
        self.create_super_admin()

    def test_get_judge_server(self):
        # 获取评测机的信息
        resp = self.client.get(self.url)
        self.assertSuccess(resp)
        self.assertEqual(len(resp.data["data"]["servers"]), 1)

    def test_delete_judge_server(self):
        # 方法就是先创建然后删除
        resp = self.client.delete(self.url + "?hostname=testhostname")
        self.assertSuccess(resp)
        self.assertFalse(JudgeServer.objects.filter(hostname="testhostname").exists())

    def test_disabled_judge_server(self):
        # 关闭测评机，传入True
        resp = self.client.put(self.url, data={"is_disabled": True, "id": self.server.id})
        self.assertSuccess(resp)
        self.assertTrue(JudgeServer.objects.get(id=self.server.id).is_disabled)


class LanguageListAPITest(APITestCase):
    def test_get_languages(self):
        # 获取系统语言和特殊评测语言，默认是相等的
        resp = self.client.get(self.reverse("language_list_api"))
        self.assertSuccess(resp)


class TestCasePruneAPITest(APITestCase):
    def setUp(self):
        self.url = self.reverse("prune_test_case_api")
        self.create_super_admin()

    def test_get_isolated_test_case(self):
        # 测试被隔离的测试用例
        resp = self.client.get(self.url)
        self.assertSuccess(resp)

    @mock.patch("conf.views.TestCasePruneAPI.delete_one")
    @mock.patch("conf.views.os.listdir")
    @mock.patch("conf.views.Problem")
    def test_delete_test_case(self, mocked_problem, mocked_listdir, mocked_delete_one):
        # 模拟给出数据
        valid_id = "1172980672983b2b49820be3a741b109"
        mocked_problem.return_value = [valid_id, ]
        mocked_listdir.return_value = [valid_id, ".test", "aaa"]
        resp = self.client.delete(self.url)
        self.assertSuccess(resp)
        mocked_delete_one.assert_called_once_with(valid_id)


class ReleaseNoteAPITest(APITestCase):
    # 版本更改记录
    def setUp(self):
        self.url = self.reverse("get_release_notes_api")
        self.create_super_admin()
        self.latest_data = {"update": [
            {
                "version": "2099-12-25",
                "level": 1,
                "title": "Update at 2099-12-25",
                "details": ["test get", ]
            }
        ]}

    def test_get_versions(self):
        # 获取版本信息
        resp = self.client.get(self.url)
        self.assertSuccess(resp)


class DashboardInfoAPITest(APITestCase):
    def setUp(self):
        self.url = self.reverse("dashboard_info_api")
        self.create_admin()

    def test_get_info(self):
        resp = self.client.get(self.url)
        # 获得仪表盘信息
        self.assertSuccess(resp)
        # 因为才创建一个用户用于测试，数据保存到数据库里面，断言用户数为1，通过
        self.assertEqual(resp.data["data"]["user_count"], 1)

