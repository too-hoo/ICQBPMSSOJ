#!/usr/bin/env python
# -*-encoding:UTF-8-*-

from django.core.urlresolvers import reverse
from django.test.testcases import TestCase
from rest_framework.test import APIClient

from account.models import AdminType, ProblemPermission, User, UserProfile


class APITestCase(TestCase):
    client_class = APIClient

    # 首先创建一个用户，登录状态为True
    def create_user(self, username, password, admin_type=AdminType.REGULAR_USER, login=True,
                    problem_permission=ProblemPermission.NONE):
        user = User.objects.create(username=username, admin_type=admin_type, problem_permission=problem_permission)
        user.set_password(password)

        UserProfile.objects.create(user=user)
        user.save()
        if login:
            self.client.login(username=username, password=password)
        return user

    # 创建一个管理员用户，为登录状态准备
    def create_admin(self, username="admin", password="admin", login=True):
        return self.create_user(username=username, password=password, admin_type=AdminType.ADMIN,
                                problem_permission=ProblemPermission.OWN,
                                login=login)

    # 创建一个超级管理员，为登录状态准备
    def create_super_admin(self, username="root", password="root", login=True):
        return self.create_user(username=username, password=password, admin_type=AdminType.SUPER_ADMIN,
                                problem_permission=ProblemPermission.ALL, login=login)

    def reverse(self, url_name, *args, **kwargs):
        # 反转验证，为内置方法
        return reverse(url_name, *args, **kwargs)

    def assertSuccess(self, response):
        # 返回的data的error值不是None的话就抛出断言错误，将响应的数据转成字符串输出：str(response.data)
        if not response.data["error"] is None:
            raise AssertionError("response with errors, response: " + str(response.data))

    def assertFailed(self, response, msg=None):
        self.assertTrue(response.data["error"] is not None)
        if msg:
            self.assertEqual(response.data["data"], msg)
