import time

from unittest import mock
from datetime import timedelta
from copy import deepcopy

from django.contrib import auth
from django.utils.timezone import now
from otpauth import OtpAuth

from myutils.api.tests import APIClient, APITestCase
from myutils.shortcuts import rand_str
from options.options import SysOptions

from .models import AdminType, ProblemPermission, User
from myutils.constants import ContestRuleType

# ===============================验证码公共类CaptchaTest========================
class CaptchaTest(APITestCase):
    def _set_captcha(self, session):
        captcha = rand_str(4)
        # session存放生成的验证码
        session["_django_captcha_key"] = captcha
        # session存放生成的验证码时间
        session["_django_captcha_expires_time"] = int(time.time()) + 30
        session.save()
        return captcha


# =================注释User的models中的object调用的Mamager()类 ：PermissionDecoratorTest和UserRegisterAPITest 通过测试
# ==================不需要objects的测试===============================
class PermissionDecoratorTest(APITestCase):
    # 通过：注意要注销object调用的Mamager()类 才能通过
    # 测试权限装饰器是否生效
    def setUp(self):
        # 初始化数据，使用模拟请求响应工具包mock进行测试
        self.regular_user = User.objects.create(username="regular_user")
        self.admin = User.objects.create(username="admin")
        self.super_admin = User.objects.create(username="super_admin")
        self.request = mock.MagicMock()
        self.request.user.is_authenticated = mock.MagicMock()

    def test_login_required(self):
        # 使用Django里面内置的方法验证用户登录
        self.request.user.is_authenticated.return_value = False

    def test_admin_required(self):
        pass

    def test_super_admin_required(self):
        pass


class UserRegisterAPITest(CaptchaTest):
    # 用户注册类
    def setUp(self):
        print("Testing", self._testMethodName)
        self.client = APIClient()
        self.register_url = self.reverse("user_register_api")
        self.captcha = rand_str(4)

        self.data = {"username": "test_user", "password": "testuserpassword",
                     "real_name": "real_name", "email": "test@example.com",
                     "captcha": self._set_captcha(self.client.session)}

    def test_register_with_correct_info(self):
        # 常规正常注册信息的测试，根据命名空间对应的url进行注册请求
        response = self.client.post(self.register_url, data=self.data)
        self.assertDictEqual(response.data, {"error": None, "data": "Succeeded"})

    def test_username_already_exists(self):
        # 用户名是否已经存在，继承正确信息再请求注册会提示报错
        self.test_register_with_correct_info()

        self.data["captcha"] = self._set_captcha(self.client.session)
        self.data["email"] = "test1@test.com"
        response = self.client.post(self.register_url, data=self.data)
        self.assertDictEqual(response.data, {"error": "error", "data": "Username already exists"})

    def test_email_already_exists(self):
        # 测试邮件是否已存在
        self.test_register_with_correct_info()

        self.data["captcha"] = self._set_captcha(self.client.session)
        self.data["username"] = "test_user1"
        response = self.client.post(self.register_url, data=self.data)
        self.assertDictEqual(response.data, {"error": "error", "data": "Email already exists"})

    def test_website_config_limit(self):
        # 测试网站是否能够进行注册
        SysOptions.allow_register = False
        resp = self.client.post(self.register_url, data=self.data)
        self.assertDictEqual(resp.data, {"error": "error", "data": "Register function has been disabled by admin"})

    def test_invalid_captcha(self):
        # 测试验证码是否有效，胡乱给一个”××××“
        self.data["captcha"] = "****"
        response = self.client.post(self.register_url, data=self.data)
        self.assertDictEqual(response.data, {"error": "error", "data": "Invalid captcha"})

        # 弹出验证码键值
        self.data.pop("captcha")
        response = self.client.post(self.register_url, data=self.data)
        print(response.data["error"])   # data里面的数据是invalid-captcha，不是None，断言正确
        self.assertTrue(response.data["error"] is not None)


class AdminUserTest(APITestCase):
    def setUp(self):
        print("Testing", self._testMethodName)
        self.user = self.create_super_admin(login=True)
        self.username = self.password = "test"
        self.regular_user = self.create_user(username=self.username, password=self.password, login=False)
        self.url = self.reverse("user_admin_api")
        # 首先初始化设置数据为常规用户的数据，因为管理员用户的数据实在普通的用户信息的基础上进行修改的
        # 对于问题权限起码有属于自己的
        self.data = {"id": self.regular_user.id, "username": self.username, "real_name": "test_name",
                     "email": "test@qq.com", "admin_type": AdminType.REGULAR_USER,
                     "problem_permission": ProblemPermission.OWN, "open_api": True,
                     "two_factor_auth": False, "is_disabled": False}

    def test_user_list(self):
        # 测试用户列表
        print(self.url)     # /api/admin/user， 注意这个是在管理员的url里面找的
        response = self.client.get(self.url)
        self.assertSuccess(response)

    def test_edit_user_successfully(self):
        # 测试编辑用户是否成功，使用put方法
        response = self.client.put(self.url, data=self.data)
        self.assertSuccess(response)
        resp_data = response.data["data"]
        self.assertEqual(resp_data["username"], self.username)
        self.assertEqual(resp_data["email"], "test@qq.com")
        self.assertEqual(resp_data["open_api"], True)
        self.assertEqual(resp_data["two_factor_auth"], False)
        self.assertEqual(resp_data["is_disabled"], False)
        self.assertEqual(resp_data["problem_permission"], ProblemPermission.NONE)

        self.assertTrue(self.regular_user.check_password("test"))

    def test_edit_user_password(self):
        # 测试更新用户的密码，使用put请求
        data = self.data
        new_password = "testpassword"
        data["password"] = new_password
        response = self.client.put(self.url, data=data)
        self.assertSuccess(response)
        # 更新用户密码之后，分别使用旧的、新的密码检查，
        # 使用的方法是用户集成AbstractBase的密码检查方法
        user = User.objects.get(id=self.regular_user.id)
        self.assertFalse(user.check_password(self.password))
        self.assertTrue(user.check_password(new_password))

    def test_edit_user_tfa(self):
        # 用户的双因素登录
        data = self.data
        # 默认是空的None，所以使用断言通过
        self.assertIsNone(self.regular_user.tfa_token)
        # 设置双因素验证标志为true
        data["two_factor_auth"] = True
        # 使用put方法更新数据
        response = self.client.put(self.url, data=data)
        self.assertSuccess(response)
        resp_data = response.data["data"]
        # 用户的双因素登录字段tfa_token如果为None， 就会产生一个新的值
        self.assertTrue(resp_data["two_factor_auth"])
        # 验证tfa_token是否为非空
        token = User.objects.get(id=self.regular_user.id).tfa_token
        self.assertIsNotNone(token)

        # 修改新的双因素验证
        response = self.client.put(self.url, data=data)
        self.assertSuccess(response)
        resp_data = response.data["data"]
        # 如果双因素令牌tfa_token的值不为空， 就保持value的值不变
        self.assertTrue(resp_data["two_factor_auth"])
        self.assertEqual(User.objects.get(id=self.regular_user.id).tfa_token, token)

    def test_edit_user_openapi(self):
        # 前后端传值的api接口，类似于two_factor_auth的检查， open_api is a boolean
        data = self.data
        self.assertIsNone(self.regular_user.open_api_appkey)
        data["open_api"] = True
        response = self.client.put(self.url, data=data)
        self.assertSuccess(response)
        # 返回的数据成功，查询数据库断言成功
        resp_data = response.data["data"]
        # 如果open_api_appkey的值为None，就产生一个新的值
        self.assertTrue(resp_data["open_api"])
        key = User.objects.get(id=self.regular_user.id).open_api_appkey
        self.assertIsNotNone(key)

        response = self.client.put(self.url, data=data)
        self.assertSuccess(response)
        resp_data = response.data["data"]
        # 如果openapi_app_key不为None的话，保持它的值不变
        self.assertTrue(resp_data["open_api"])
        self.assertEqual(User.objects.get(id=self.regular_user.id).open_api_appkey, key)

    def test_import_users(self):
        # 后台管理员导入用户数据
        data = {"users": [["user1", "pass1", "eami1@e.com"],
                          ["user2", "pass3", "eamil3@e.com"]]
                }
        resp = self.client.post(self.url, data)
        self.assertSuccess(resp)
        # 成功的创建了两个用户（usr）
        self.assertEqual(User.objects.all().count(), 4)

    def test_import_duplicate_user(self):
        # 如果是重复的话就不会被导入，例如下面的user1和user1相同就不会被导入
        data = {"users": [["user1", "pass1", "eami1@e.com"],
                          ["user1", "pass1", "eami1@e.com"]]
                }
        resp = self.client.post(self.url, data)
        self.assertFailed(resp, "DETAIL:  Key (username)=(user1) already exists.")
        # 没有用户被导入
        self.assertEqual(User.objects.all().count(), 2)

    def test_delete_users(self):
        # 测试删除用户
        self.test_import_users()
        # base on ‘test_import_user()’
        # 现将user1和user2的id查找出来，然后使用“，”将id拼接起来，最后再拼接到请求删除的URL上面，发送请求即可
        user_ids = User.objects.filter(username__in=["user1", "user2"]).values_list("id", flat=True)
        user_ids = ",".join([str(id) for id in user_ids])
        resp = self.client.delete(self.url + "?id=" + user_ids)
        self.assertSuccess(resp)
        # 删除的用户数目等于两个
        self.assertEqual(User.objects.all().count(), 2)


class GenerateUserAPITest(APITestCase):
    # 创建用户
    def setUp(self):
        print("Testing", self._testMethodName)
        # 调用myutils里面的方法
        self.create_super_admin()
        self.url = self.reverse("generate_user_api")
        self.data = {
            "number_from": 100, "number_to": 105,
            "prefix": "pre", "suffix": "suf",
            "default_email": "test@test.com",
            "password_length": 8
        }

    def test_error_case(self):
        # 用户创建失败的情况
        data = deepcopy(self.data)
        # 设置数据的前缀和后缀
        data["prefix"] = "t" * 16
        data["suffix"] = "s" * 14
        resp = self.client.post(self.url, data=data)
        self.assertEqual(resp.data["data"], "Username should not more than 32 characters")

        data2 = deepcopy(self.data)
        data2["number_from"] = 106
        resp = self.client.post(self.url, data=data2)
        self.assertEqual(resp.data["data"], "Start number must be lower than end number")

    @mock.patch("account.views.viadmin.xlsxwriter.Workbook")
    def test_generate_user_success(self, mock_workbook):
        # 测试成功产生用户
        resp = self.client.post(self.url, data=self.data)
        self.assertSuccess(resp)
        mock_workbook.assert_called()


class OpenAPIAppkeyAPITest(APITestCase):
    # 前后端的开放接口
    def setUp(self):
        print("Testing", self._testMethodName)
        self.user = self.create_super_admin()
        self.url = self.reverse("open_api_appkey_api")

    def test_reset_appkey(self):
        # 重置接口令牌
        resp = self.client.post(self.url, data={})
        self.assertFailed(resp)

        self.user.open_api = True
        self.user.save()
        resp = self.client.post(self.url, data={})
        self.assertSuccess(resp)
        self.assertEqual(resp.data["data"]["appkey"], User.objects.get(username=self.user.username).open_api_appkey)


class TwoFactorAuthAPITest(APITestCase):
    def setUp(self):
        #初始化
        print("Testing", self._testMethodName)
        self.url = self.reverse("two_factor_auth_api")
        # 创建用户，满足登录情况
        self.create_user("test", "test123")

    def _get_tfa_code(self):
        # 获得验证码
        # 先查找数据库对应的用户，生成一个二维码
        user = User.objects.first()
        code = OtpAuth(user.tfa_token).totp()
        if len(str(code)) < 6:
            code = (6 - len(str(code))) * "0" + str(code)
        return code

    def test_get_image(self):
        # 获取二维码图像
        resp = self.client.get(self.url)
        self.assertSuccess(resp)

    def test_open_tfa_with_invalid_code(self):
        # 无效的验证码
        self.test_get_image()
        # 先使用test_get_image的get请求生成一张二维码图片存放到数据库里面去，然后下面乱设置一个code，
        # 使用post请求，肯定会报错
        resp = self.client.post(self.url, data={"code": "000000"})
        self.assertDictEqual(resp.data, {"error": "error", "data": "Invalid code"})

    def test_open_tfa_with_correct_code(self):
        # 有效的验证码
        self.test_get_image()
        # 使用生成的code去请求
        code = self._get_tfa_code()
        resp = self.client.post(self.url, data={"code": code})
        self.assertSuccess(resp)
        user = User.objects.first()
        self.assertEqual(user.two_factor_auth, True)

    def test_close_tfa_with_invalid_code(self):
        # 使用无效的验证码关闭双因素验证
        self.test_open_tfa_with_correct_code()
        resp = self.client.put(self.url, data={"code": "000000"})
        self.assertDictEqual(resp.data, {"error": "error", "data": "Invalid code"})

    def test_close_tfa_with_correct_code(self):
        # 使用有效的验证码关闭双因素验证
        self.test_open_tfa_with_correct_code()
        code = self._get_tfa_code()
        resp = self.client.put(self.url, data={"code": code})
        self.assertSuccess(resp)
        user = User.objects.first()
        self.assertEqual(user.two_factor_auth, False)


class UserChangeEmailAPITest(APITestCase):
    def setUp(self):
        print("Testing", self._testMethodName)
        self.url = self.reverse("user_change_email_api")
        self.user = self.create_user("test", "test123")
        self.new_mail = "test@example.com"
        self.data = {"password": "test123", "new_email": self.new_mail}

    def test_change_email_success(self):
        # 正确数据修改邮箱
        resp = self.client.post(self.url, data=self.data)
        self.assertSuccess(resp)

    def test_wrong_password(self):
        # 错误的密码修改不了邮箱
        self.data["password"] = "aaaa"
        resp = self.client.post(self.url, data=self.data)
        self.assertDictEqual(resp.data, {"error": "error", "data": "Wrong password"})

    def test_duplicate_email(self):
        u = self.create_user("aa", "bb", login=False)
        u.email = self.new_mail
        u.save()
        resp = self.client.post(self.url, data=self.data)
        self.assertDictEqual(resp.data, {"error": "error", "data": "The email is owned by other account"})


class UserChangePasswordAPITest(APITestCase):
    def setUp(self):
        print("Testing", self._testMethodName)
        self.url = self.reverse("user_change_password_api")

        # 首先创建一个用户
        self.username = "test_user"
        self.old_password = "testuserpassword"
        self.new_password = "new_password"
        self.user = self.create_user(username=self.username, password=self.old_password, login=False)

        self.data = {"old_password": self.old_password, "new_password": self.new_password}

    def _get_tfa_code(self):
        # 获取双因素代码
        # 正向查询：一对多，查找第一条
        user = User.objects.first()
        code = OtpAuth(user.tfa_token).totp()
        if len(str(code)) < 6:
            code = (6 - len(str(code))) * "0" + str(code)
        return code

    def test_login_required(self):
        # 测试修改密码时要先登录的要求
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.data, {"error": "permission-denied", "data": "Please login first"})

    def test_valid_old_password(self):
        # 首先登录，断言通过，然后post请求修改密码
        self.assertTrue(self.client.login(username=self.username, password=self.old_password))
        response = self.client.post(self.url, data=self.data)
        # 断言通过，使用新密码登录也通过
        self.assertEqual(response.data, {"error": None, "data": "Succeeded"})
        self.assertTrue(self.client.login(username=self.username, password=self.new_password))

    def test_invalid_old_password(self):
        # 首先使用旧密码登录成功
        self.assertTrue(self.client.login(username=self.username, password=self.old_password))
        # 修改密码的时候需要旧密码，但是使用一个错误的旧密码自然就不能更新
        self.data["old_password"] = "invalid"
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.data, {"error": "error", "data": "Invalid old password"})

    def test_tfa_code_required(self):
        # 测试要求使用双因素来修改密码
        self.user.two_factor_auth = True
        self.user.tfa_token = "tfa_token"
        self.user.save()
        self.assertTrue(self.client.login(username=self.username, password=self.old_password))
        # 自己新产生一个自然不能通过
        self.data["tfa_code"] = rand_str(6)
        resp = self.client.post(self.url, data=self.data)
        self.assertEqual(resp.data, {"error": "error", "data": "Invalid two factor verification code"})

        # 必须使用数据库存放的双因素验证码验证才可以
        self.data["tfa_code"] = self._get_tfa_code()
        resp = self.client.post(self.url, data=self.data)
        self.assertSuccess(resp)


class UserLoginAPITest(APITestCase):
    def setUp(self):
        print("Testing", self._testMethodName)
        self.username = self.password = "test"
        # 首先设置为login为False
        self.user = self.create_user(username=self.username, password=self.password, login=False)
        self.login_url = self.reverse("user_login_api")

    def _set_tfa(self):
        # 开启双因素验证，注意这里生成的双因素验证码直接就根据对应的用户保存到数据库里面了
        self.user.two_factor_auth = True
        tfa_token = rand_str(32)
        self.user.tfa_token = tfa_token
        self.user.save()
        return tfa_token

    def test_login_with_correct_info(self):
        # 使用正确的信息登录
        response = self.client.post(self.login_url,
                                    data={"username": self.username, "password": self.password})
        self.assertDictEqual(response.data, {"error": None, "data": "Succeeded"})

        # 应为user是要继承Django的超类，抽象AbstractBaseUser的，所以还要调用内置的auth方法验证是否通过
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated())

    def test_login_with_correct_info_upper_username(self):
        # 用户名如果是大写的话也要验证，因为实际的情况大小写其实是不分的，例如注册github的时候使用
        # toohoo发现被注册，尝试使用TOOHOO时，也发现被注册了，下面就是这个逻辑，所以使用toohoo和TOOHOO登录都可以
        resp = self.client.post(self.login_url, data={"username": self.username.upper(), "password": self.password})
        self.assertDictEqual(resp.data, {"error": None, "data": "Succeeded"})
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated())

    def test_login_with_wrong_info(self):
        # 使用错误的信息登录
        response = self.client.post(self.login_url,
                                    data={"username": self.username, "password": "invalid_password"})
        self.assertDictEqual(response.data, {"error": "error", "data": "Invalid username or password"})

        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated())

    def test_tfa_login(self):
        # 测试使用双因素验证登录，调用_set_tfa()生成双因素验证码
        token = self._set_tfa()
        # 使用一次性验证工具加工一下
        code = OtpAuth(token).totp()
        # code字符串化之后的长度若小于6，不足的长度就用0补齐，最后再次拼接字符串化的code，就保证验证码大于6位数
        if len(str(code)) < 6:
            code = (6 - len(str(code))) * "0" + str(code)
        # 直接请求，因为双因素验证码已经保存到数据库里面了
        response = self.client.post(self.login_url,
                                    data={"username": self.username,
                                          "password": self.password,
                                          "tfa_code": code})
        self.assertDictEqual(response.data, {"error": None, "data": "Succeeded"})

        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated())

    def test_tfa_login_wrong_code(self):
        # 使用错误的双因素验证码qqqqqq，6位数
        self._set_tfa()
        response = self.client.post(self.login_url,
                                    data={"username": self.username,
                                          "password": self.password,
                                          "tfa_code": "qqqqqq"})
        self.assertDictEqual(response.data, {"error": "error", "data": "Invalid two factor verification code"})

        # 错误的用户
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated())

    def test_tfa_login_without_code(self):
        # 没有双因素验证码的情况登录需要双因素码的情况
        self._set_tfa()
        response = self.client.post(self.login_url,
                                    data={"username": self.username,
                                          "password": self.password})
        self.assertDictEqual(response.data, {"error": "error", "data": "tfa_required"})

        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated())

    def test_user_disabled(self):
        # 测试账户被禁止的情况
        self.user.is_disabled = True
        self.user.save()
        resp = self.client.post(self.login_url, data={"username": self.username,
                                                      "password": self.password})
        self.assertDictEqual(resp.data, {"error": "error", "data": "Your account has been disabled"})


class UserProfileAPITest(APITestCase):
    def setUp(self):
        print("Testing", self._testMethodName)
        self.url = self.reverse("user_profile_api")

    def test_get_profile_without_login(self):
        # 没登录获取数据
        resp = self.client.get(self.url)
        self.assertDictEqual(resp.data, {"error": None, "data": None})

    def test_get_profile(self):
        # 登录获取数据
        self.create_user("test", "test123")
        resp = self.client.get(self.url)
        self.assertSuccess(resp)

    def test_update_profile(self):
        # 更新用户信息
        self.create_user("test", "test123")
        update_data = {"real_name": "zemal", "submission_number": 233, "language": "en-US"}
        resp = self.client.put(self.url, data=update_data)
        self.assertSuccess(resp)
        data = resp.data["data"]
        self.assertEqual(data["real_name"], "zemal")
        self.assertEqual(data["submission_number"], 0)
        self.assertEqual(data["language"], "en-US")


class UserRankAPITest(APITestCase):
    # 用户排名，不需要登录
    def setUp(self):
        print("Testing", self._testMethodName)
        self.url = self.reverse("user_rank_api")
        # 首先创建连个未登录的用户
        self.create_user("test1", "test123", login=False)
        self.create_user("test2", "test123", login=False)
        # 设置用户test1和用户test2的配置信息
        test1 = User.objects.get(username="test1")
        profile1 = test1.userprofile
        profile1.submission_number = 10
        profile1.accepted_number = 10
        profile1.total_score = 240
        profile1.save()

        test2 = User.objects.get(username="test2")
        profile2 = test2.userprofile
        profile2.submission_number = 15
        profile2.accepted_number = 10
        profile2.total_score = 700
        profile2.save()

    def test_get_acm_rank(self):
        resp = self.client.get(self.url, data={"rule": ContestRuleType.ACM})
        self.assertSuccess(resp)
        data = resp.data["data"]["results"]
        # acm 大家都是10道题，自然是test1排在前
        self.assertEqual(data[0]["user"]["username"], "test1")
        self.assertEqual(data[1]["user"]["username"], "test2")

    def test_get_oi_rank(self):
        resp = self.client.get(self.url, data={"rule": ContestRuleType.OI})
        self.assertSuccess(resp)
        data = resp.data["data"]["results"]
        # OI test2排在前面
        self.assertEqual(data[0]["user"]["username"], "test2")
        self.assertEqual(data[1]["user"]["username"], "test1")

    def test_admin_role_filted(self):
        # 管理员角色过滤功能
        self.create_admin("admin", "admin123")
        # 查询数据库，并设配置管理员信息
        admin = User.objects.get(username="admin")
        profile1 = admin.userprofile
        profile1.submission_number = 20
        profile1.accepted_number = 5
        profile1.total_score = 300
        profile1.save()
        # 管理员登录之后，也可以参加排名和查询
        resp = self.client.get(self.url, data={"rule": ContestRuleType.ACM})
        self.assertSuccess(resp)
        self.assertEqual(len(resp.data["data"]), 2)

        resp = self.client.get(self.url, data={"rule": ContestRuleType.OI})
        self.assertSuccess(resp)
        self.assertEqual(len(resp.data["data"]), 2)


class ProfileProblemDisplayIDRefreshAPITest(APITestCase):
    def setUp(self):
        pass

# 注意这里进行的DuplicateUserCheckAPITest和TFARequiredCheckAPITest和的url要与命名空间的相一致，
# 具体就是要在urls.pyl里面更改， 这样才能通过
class DuplicateUserCheckAPITest(APITestCase):
    # 重复用户检查测试
    def setUp(self):
        print("Testing", self._testMethodName)
        user = self.create_user("test", "test123", login=False)
        user.email = "test@test.com"
        user.save()
        self.url = self.reverse("check_username_or_email")

    def test_duplicate_username(self):
        resp = self.client.post(self.url, data={"username": "test"})
        data = resp.data["data"]
        self.assertEqual(data["username"], True)
        # 下面是上面的简写
        resp = self.client.post(self.url, data={"username": "Test"})
        self.assertEqual(resp.data["data"]["username"], True)

    def test_ok_username(self):
        # 数据库里面是test，但是这里是test1，自然不会重复，结果返回默认false
        resp = self.client.post(self.url, data={"username": "test1"})
        data = resp.data["data"]
        self.assertFalse(data["username"])

    def test_duplicate_email(self):
        # 邮箱重复
        resp = self.client.post(self.url, data={"email": "test@test.com"})
        self.assertEqual(resp.data["data"]["email"], True)
        resp = self.client.post(self.url, data={"email": "Test@Test.com"})
        self.assertTrue(resp.data["data"]["email"])

    def test_ok_email(self):
        # 邮箱没重复
        resp = self.client.post(self.url, data={"email": "aa@test.com"})
        self.assertFalse(resp.data["data"]["email"])


class TFARequiredCheckAPITest(APITestCase):
    # 双因素要求检查测试，通过
    def setUp(self):
        # APITestCase里面定义的是创建的用户是登录状态，这里改成False，结果返回的肯定是要先登录
        self.url = self.reverse("tfa_required_check")
        self.create_user("test", "test123", login=True)

    def test_not_required_tfa(self):
        # 测试不进行双因素要求：根据url(命名空间）访问对应的view,需要的字段直接给data，不过数据库里面没有设置
        resp = self.client.post(self.url, data={"username": "test"})
        self.assertSuccess(resp)
        # 断言data里面的result为false
        print(resp.data["data"]["result"])
        self.assertEqual(resp.data["data"]["result"], False)

    def test_required_tfa(self):
        user = User.objects.first()
        # 默认不开启双因素验证，但是设置为True之后，自然返回true
        user.two_factor_auth = True
        user.save()
        resp = self.client.post(self.url, data={"username": "test"})
        self.assertEqual(resp.data["data"]["result"], True)


@mock.patch("account.views.vicqbpmssoj.send_email_async.delay")
class ApplyResetPasswordAPITest(CaptchaTest):
    # 数据库的字段一定要设置正确
    def setUp(self):
        self.create_user("test", "test123", login=False)
        # 查询数据库第一条，配置信息并保存
        user = User.objects.first()
        user.email = "test@example.com"
        user.save()
        self.url = self.reverse("apply_reset_password_api")
        self.data = {"email": "test@example.com", "captcha": self._set_captcha(self.client.session)}

    def _refresh_captcha(self):
        # 点击一下更新验证码
        self.data["captcha"] = self._set_captcha(self.client.session)

    def test_apply_reset_password(self, send_email_delay):
        # 通过
        resp = self.client.post(self.url, data=self.data)
        self.assertSuccess(resp)
        # s断言end_email_delay方法被调用
        send_email_delay.assert_called()

    def test_apply_reset_password_twice_in_20_mins(self, send_email_delay):
        # 二次重置密码，已通过，之前数据库字段设置错误出错
        self.test_apply_reset_password()
        # 重新模拟一下发送邮件
        send_email_delay.reset_mock()
        # 刷新一下验证码
        self._refresh_captcha()
        # 再次请求数据
        resp = self.client.post(self.url, data=self.data)
        self.assertDictEqual(resp.data, {"error": "error", "data": "You can only reset password once per 20 minutes"})
        send_email_delay.assert_not_called()

    def test_apply_reset_password_again_after_20_mins(self, send_email_delay):
        # 再次出问题，断言成功，之前数据库字段设置错误出错
        self.test_apply_reset_password()
        # 查询数据库第一条，配置信息
        user = User.objects.first()
        # 设置现在的时间已经向后延迟21minutes了，超时，返回错误提示信息
        user.reset_password_token_expire_time = now() - timedelta(minutes=21)
        user.save()
        # 返回出错信息的时候刷新一下验证吗，人性化
        self._refresh_captcha()
        self.test_apply_reset_password()


class ResetPasswordAPITest(CaptchaTest):
    # 重置密码
    def setUp(self):
        # 创建用户并设置用户的各种属性
        self.create_user("test", "test123", login=False)
        self.url = self.reverse("reset_password_api")
        user = User.objects.first()
        user.reset_password_token = "icqbpmssoj?"
        user.reset_password_token_expire_time = now() + timedelta(minutes=20)
        user.save()
        self.data = {"token": user.reset_password_token,
                     "captcha": self._set_captcha(self.client.session),
                     "password": "test456"}

    def test_reset_password_with_correct_token(self):
        # 通过,注意要将URL映射的命名空间的设置
        # 先将data数据传过去保存到数据库，然后使用client请求登录
        resp = self.client.post(self.url, data=self.data)
        self.assertSuccess(resp)
        self.assertTrue(self.client.login(username="test", password="test456"))

    def test_reset_password_with_invalid_token(self):
        # 使用无效的而令牌重置密码，通过
        self.data["token"] = "aaaaaaaaaaa"
        resp = self.client.post(self.url, data=self.data)
        self.assertDictEqual(resp.data, {"error": "error", "data": "Token does not exist"})

    def test_reset_password_with_expired_token(self):
        # 使用失效的令牌重置密码，通过， 值得注意的是数据库的字段一定要设置正确
        user = User.objects.first()
        # 在失效时间30秒，token失效
        user.reset_password_token_expire_time = now() - timedelta(seconds=30)
        # print(user.reset_password_token_expire_time)
        user.save()
        resp = self.client.post(self.url, data=self.data)
        self.assertDictEqual(resp.data, {"error": "error", "data": "Token has expired"})


# ============，SessionManagementAPITest，存在问题，还是有些不能通过，需要继续下功夫=======
class SessionManagementAPITest(APITestCase):
    def setUp(self):
        self.create_user("test", "test123")
        self.url = self.reverse("session_management_api")
        # 启动一个请求来提供session 数据
        login_url = self.reverse("user_login_api")
        # print(login_url)    #/api/login
        # print(self.url)     #/api/sessions

        # 类似于浏览器的登录
        self.client.post(login_url, data={"username": "test", "password": "test123"})

    def test_get_sessions(self):
        # 出问题
        # 根据self.url进行get请求，保存数据到resp
        resp = self.client.get(self.url)
        self.assertSuccess(resp)       # error=None，错误就没有抛出
        data = resp.data["data"]
        print(data)     #[]
        # 这个有问题，我要的是一个session，而不是一个[]空的列表,应为我有一个用户登录了，
        # 应该要保存至少一个session吧，说明登录那块也有问题
        # 已经解决，设置中间件middleware即可解决
        self.assertEqual(len(data), 1)

    # def test_delete_session_key(self):
    #     resp = self.client.delete(self.url + "?session_key=" + self.session_key)
    #     self.assertSuccess(resp)

    # 删除不合秘钥的session
    def test_delete_session_with_invalid_key(self):
        # 通过
        resp = self.client.delete(self.url + "?session_key=aaaaaaaaaa")
        self.assertDictEqual(resp.data, {"error": "error", "data": "Invalid session_key"})

