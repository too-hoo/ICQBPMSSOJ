#!/usr/bin/env python
# -*-encoding:UTF-8-*-

from django.test import TestCase
import copy
from datetime import datetime, timedelta

from django.utils import timezone

from myutils.api.tests import APITestCase

from .models import ContestAnnouncement, ContestRuleType, Contest


# 注意，还有两个ACMContestHelper和DownloadContestSubmissions 这两个类还没测试，先放下

DEFAULT_CONTEST_DATA = {"title": "contest title", "description": "contest description",
                        "start_time": timezone.localtime(timezone.now()),
                        "end_time": timezone.localtime(timezone.now()) + timedelta(days=1),
                        "rule_type": ContestRuleType.ACM,
                        "password": "123",
                        "allowed_ip_ranges": [],
                        "visible": True, "real_time_rank": True}


class ContestAdminAPITest(APITestCase):
    # 管理员管理比赛的API
    def setUp(self):
        # 创建
        self.create_super_admin()
        self.url = self.reverse("contest_admin_api")
        self.data = copy.deepcopy(DEFAULT_CONTEST_DATA)

    def test_create_contest(self):
        # 创建比赛
        response = self.client.post(self.url, data=self.data)
        self.assertSuccess(response)
        return response

    def test_create_contest_with_invalid_cidr(self):
        # 测试使用无效的cidr创建比赛
        self.data["allow_ip_ranges"] = ["127.0.0"]
        resp = self.client.post(self.url, data=self.data)
        self.assertDictEqual(resp.data, resp.data, {"error": "error", "data": "127.0.0 is not a valid cidr network"})

    def test_update_contest(self):
        # 测试更新比赛数据
        id = self.test_create_contest().data["data"]["id"]  # 返回的是一个序列化的对象，当让有一个id
        update_data = {"id": id, "title": "update title",
                       "description": "update description",
                       "password": "12345",
                       "visible": False, "real_time_rank": False}
        data = copy.deepcopy(self.data)
        data.update(update_data)
        response = self.client.put(self.url, data = data)
        self.assertSuccess(response)
        response_data = response.data["data"]
        # 将返回的数据和希望修改的数据的键进行比较
        for k in data.keys():
            # data[k] 归属与datetime时，跳出本循环继续执行
            if isinstance(data[k], datetime):
                continue
            self.assertEqual(response_data[k],data[k])

    def test_get_contest(self):
        # 根据URL请求获取数据
        self.test_create_contest()
        response = self.client.get(self.url)
        self.assertSuccess(response)

    def test_get_one_contest(self):
        # 获取一条比赛数据,先创建一条数据，然后将这条数据获得
        id = self.test_create_contest().data["data"]["id"]
        response = self.client.get("{}?id={}".format(self.url, id))
        self.assertSuccess(response)


class ContestAPITest(APITestCase):
    def setUp(self):
        # 首先创建一个超级用户，使用内部的方法，将字典数据解析创建比赛，并返回比赛对象
        user = self.create_admin()
        self.contest = Contest.objects.create(created_by=user, **DEFAULT_CONTEST_DATA)
        self.url = self.reverse("contest_api") + "?id=" + str(self.contest.id)
        print(self.url)     # /api/contest?id=1

    def test_get_contest_list(self):
        # 测试获得比赛列表
        url = self.reverse("contest_list_api")
        print(self.url)
        response = self.client.get(url + "?limit=10")
        self.assertSuccess(response)
        self.assertEqual(len(response.data["data"]["results"]), 1)

    def test_get_one_contest(self):
        resp = self.client.get(self.url)
        self.assertSuccess(resp) # id = 1

    def test_regular_user_validate_contest_password(self):
        # 测试常规用户可以验证比赛的密码。
        self.create_user("test", "test123")
        url = self.reverse("contest_password_api")
        resp = self.client.post(url,{"contest_id":self.contest.id, "password": "error_password"})
        self.assertDictEqual(resp.data, {"error": "error", "data":"Wrong password"})
        # 使用数据库存放的密码登录成功
        resp = self.client.post(url, {"contest_id": self.contest.id, "password": DEFAULT_CONTEST_DATA["password"]})
        self.assertSuccess(resp)

    def test_regular_user_access_contest(self):
        self.create_user("test", "test123")
        url = self.reverse("contest_access_api")
        # 虽然登录，但是请求方法不对，get，post方法有一个密码验证进入比赛，get方法没有
        resp = self.client.get(url + "?contest_id=" + str(self.contest.id))
        self.assertFalse(resp.data["data"]["access"])

        # 因为每次测试都会在setup里面创建一个比赛，所以这里使用创建那个比赛的ID和密码，所以及登录又使用，post
        password_url = self.reverse("contest_password_api")
        resp = self.client.post(password_url, {"contest_id": self.contest.id, "password": DEFAULT_CONTEST_DATA["password"]})
        self.assertSuccess(resp)
        print(self.url)     # /api/contest?id=1
        resp = self.client.get(self.url)
        self.assertSuccess(resp)


class ContestAnnouncementAdminAPITest(APITestCase):
    # 管理员的比赛通知
    def setUp(self):
        # 每次开头先创建一个超级用户，同时调用contest_admin_api创建一个比赛备用，预设比赛通知的数据data
        self.create_super_admin()
        self.url = self.reverse("contest_announcement_admin_api")
        contest_id = self.create_contest().data["data"]["id"]
        self.data = {"title": "test title", "content": "test content", "contest_id": contest_id, "visible": True}

    def create_contest(self):
        url = self.reverse("contest_admin_api")
        data = DEFAULT_CONTEST_DATA
        return self.client.post(url, data = data)

    def test_create_contest_announcement(self):
        response = self.client.post(self.url, data=self.data)
        self.assertSuccess(response)
        return response

    def test_delete_contest_announcement(self):
        id = self.test_create_contest_announcement().data["data"]["id"]
        response = self.client.delete("{}?id={}".format(self.url, id))
        self.assertSuccess(response)
        # 删除时候不存在
        self.assertFalse(ContestAnnouncement.objects.filter(id=id).exists())

    def test_get_contest_announcements(self):
        # 列表
        self.test_create_contest_announcement()
        response = self.client.get(self.url + "?contest_id=" + str(self.data["contest_id"]))
        self.assertSuccess(response)

    def test_get_one_contest_announcement(self):
        # 获得单个比赛通知信息
        id = self.test_create_contest_announcement().data["data"]["id"]
        response = self.client.get("{}?id={}".format(self.url, id))
        self.assertSuccess(response)


class ContestAnnouncementListAPITest(APITestCase):
    # 这个是用户的可以看到的比赛通知列表测试类
    def setUp(self):
        self.create_super_admin()
        self.url = self.reverse("contest_announcement_api")

    def create_contest_announcement(self):
        # 创建比赛通知，先创建超级用户和调用contest_admin_api创建比赛，再使用post请求创建比赛通知
        contest_id = self.client.post(self.reverse("contest_admin_api"), data=DEFAULT_CONTEST_DATA).data["data"]["id"]
        url = self.reverse("contest_announcement_admin_api")
        self.client.post(url, data={"title": "test title1", "content": "test content1", "contest_id": contest_id})
        self.client.post(url, data={"title": "test title2", "content": "test content2", "contest_id": contest_id})
        return contest_id

    def test_get_contest_announcement_list(self):
        # 先调用create_contest_announcement()创建两个比赛通知，使用get方法获取比赛通知的列表数据，
        # 传入比赛的ID查询，将创建的数据查询出来
        contest_id = self.create_contest_announcement()
        response = self.client.get(self.url, data={"contest_id": contest_id})
        self.assertSuccess(response)


class ContestRankAPITest(APITestCase):
    # 比赛排名接口测试
    def setUp(self):
        user = self.create_admin()
        # 默认创建的是ACM竞赛，其实更改默认比赛成OI也是一样
        self.acm_contest = Contest.objects.create(created_by=user, **DEFAULT_CONTEST_DATA)
        self.create_user("test", "test123")
        self.url = self.reverse("contest_rank_api")

    def get_contest_rank(self):
        # 获得acm比赛的排名，使用的是get方法
        resp = self.client.get(self.url + "?contest_id=" + self.acm_contest.id)
        self.assertSuccess(resp)

