#!/usr/bin/env python
# -*-encoding:UTF-8-*-

import os
from datetime import timedelta
from importlib import import_module

import qrcode
from django.conf import settings
from django.contrib import auth
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from otpauth import OtpAuth

from problem.models import Problem
from myutils.constants import ContestRuleType
from options.options import SysOptions
from myutils.api import APIView, validate_serializer, CSRFExemptAPIView
from myutils.captcha import Captcha
from myutils.shortcuts import rand_str, img2base64, datetime2str
from ..decorators import login_required
from ..models import User, UserProfile, AdminType
from ..serializers import (ApplyResetPasswordSerializer, ResetPasswordSerializer,
                           UserChangePasswordSerializer, UserLoginSerializer,
                           UserRegisterSerializer, UsernameOrEmailCheckSerializer,
                           RankInfoSerializer, UserChangeEmailSerializer, SSOSerializer)
from ..serializers import (TwoFactorAuthCodeSerializer, UserProfileSerializer,
                           EditUserProfileSerializer, ImageUploadForm)
from ..tasks import send_email_async


class UserRegisterAPI(APIView):
    @validate_serializer(UserRegisterSerializer)
    def post(self, request):
        """
        用户注册API
        """
        if not SysOptions.allow_register:
            return self.error("Register function has been disabled by admin")

        data = request.data
        data["username"] = data["username"].lower()
        data["email"] = data["email"].lower()
        captcha = Captcha(request)
        if not captcha.check(data["captcha"]):
            return self.error("Invalid captcha")
        if User.objects.filter(username=data["username"]).exists():
            return self.error("Username already exists")
        if User.objects.filter(email=data["email"]).exists():
            return self.error("Email already exists")
        user = User.objects.create(username=data["username"], email=data["email"])
        user.set_password(data["password"])
        user.save()
        UserProfile.objects.create(user=user)
        return self.success("Succeeded")


class UserProfileAPI(APIView):
    @method_decorator(ensure_csrf_cookie)
    def get(self, request, **kwargs):
        """
        判断是否登录， 若登录返回用户信息
        """
        user = request.user
        if not user.is_authenticated():
            return self.success()
        show_real_name = False
        username = request.GET.get("username")
        try:
            if username:
                user = User.objects.get(username=username, is_disabled=False)
            else:
                user = request.user
                # api返回的是自己的信息，可以返real_name
                show_real_name = True
        except User.DoesNotExist:
            return self.error("User does not exist")
        # 序列化数据返回
        return self.success(UserProfileSerializer(user.userprofile, show_real_name=show_real_name).data)

    @validate_serializer(EditUserProfileSerializer)
    @login_required
    def put(self, request):
        # 添加用户信息
        data = request.data
        user_profile = request.user.userprofile
        for k, v in data.items():
            setattr(user_profile, k, v)
        user_profile.save()
        return self.success(UserProfileSerializer(user_profile, show_real_name=True).data)


class AvatarUploadAPI(APIView):
    request_parsers = ()

    @login_required
    def post(self, request):
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            avatar = form.cleaned_data["image"]
        else:
            return self.error("Invalid file content")
        if avatar.size > 2 * 1024 * 1024:
            return self.error("Picture is too large")
        suffix = os.path.splitext(avatar.name)[-1].lower()
        if suffix not in [".gif", ".jpg", ".jpeg", ".bmp", ".png"]:
            return self.error("Unsupported file format")

        name = rand_str(10) + suffix
        with open(os.path.join(settings.AVATAR_UPLOAD_DIR, name), "wb") as img:
            for chunk in avatar:
                img.write(chunk)
        user_profile = request.user.userprofile

        user_profile.avatar = f"{settings.AVATAR_URI_PREFIX}/{name}"
        user_profile.save()

        return self.success("Succeeded")


class TwoFactorAuthAPI(APIView):
    @login_required
    def get(self, request):
        """
        获取二维码
        """
        user = request.user
        if user.two_factor_auth:
            return self.error("2FA is already turned on")
        token = rand_str()
        user.tfa_token = token
        user.save()

        # 设置二维码的标签：网站名：用户名
        label = f"{SysOptions.website_name_shortcut}:{user.username}"
        # 生成一张img2base64二维码：qrcode和optauth结合，转换成uri的形式
        image = qrcode.make(OtpAuth(token).to_uri("totp", label, SysOptions.website_name.replace(" ", "")))
        return self.success(img2base64(image))

    @login_required
    @validate_serializer(TwoFactorAuthCodeSerializer)
    def post(self, request):
        """
        开启 2FA 模式
        """
        code = request.data["code"]
        user = request.user
        # 从数据库查找出对应的code和传过来的code比较，成功就设置双因素验证为True
        if OtpAuth(user.tfa_token).valid_totp(code):
            user.two_factor_auth = True
            user.save()
            return self.success("Succeeded")
        else:
            return self.error("Invalid code")

    @login_required
    @validate_serializer(TwoFactorAuthCodeSerializer)
    def put(self, request):
        # 修改关闭双因素验证
        code = request.data["code"]
        user = request.user
        if not user.two_factor_auth:
            return self.error("2FA is already turned off")
        if OtpAuth(user.tfa_token).valid_totp(code):
            user.two_factor_auth = False
            user.save()
            return self.success("Succeeded")
        else:
            return self.error("Invalid code")


class CheckTFARequiredAPI(APIView):
    @validate_serializer(UsernameOrEmailCheckSerializer)
    def post(self, request):
        """
        Check TFA is required
        """
        data = request.data
        # 默认tfa双因素验证是false的
        result = False
        if data.get("username"):
            try:
                user = User.objects.get(username=data["username"])
                result = user.two_factor_auth
            except User.DoesNotExist:
                pass
        return self.success({"result": result})


class UserLoginAPI(APIView):
    @validate_serializer(UserLoginSerializer)
    def post(self, request):
        """
        用户登录API
        """
        data = request.data
        user = auth.authenticate(username=data["username"], password=data["password"])
        # 如果用户名或者密码错误就什么都没有返回
        if user:
            if user.is_disabled:
                return self.error("Your account has been disabled")
            # 如果不需要双因素验证，直接就返回得了,否则向下执行
            if not user.two_factor_auth:
                auth.login(request, user)
                return self.success("Succeeded")

            # 来到这里自然说明要双因素验证
            # 如果双因素验证码不在tfa_code请求数据里面，就返回错误
            if user.two_factor_auth and "tfa_code" not in data:
                return self.error("tfa_required")

            # 来到这里，说明需要双因素验证，而且双因素验证码也满足，这里就是判断两码是否一致
            # 成功就返回secceeded，错误就返回无效的双因素验证码提示信息
            # 传过来的tfa_code不是和数据库保存的数据一致，需要使用OtpAuth的valid_totp再加工一下还原
            if OtpAuth(user.tfa_token).valid_totp(data["tfa_code"]):
                auth.login(request, user)
                return self.success("Succeeded")
            else:
                return self.error("Invalid two factor verification code")
        else:
            # 最终如果是用户名或者密码出错就返回响应的信息
            return self.error("Invalid username or password")


class UserLogoutAPI(APIView):
    def get(self, request):
        auth.logout(request)
        return self.success()


class UsernameOrEmailCheck(APIView):
    @validate_serializer(UsernameOrEmailCheckSerializer)
    def post(self, request):
        """
        检查用户名是否重复，或者邮箱重复
        对应测试方法里面的DuplicateUserCheckAPITest，urls里面的命名空间一定要一致
        """
        data = request.data
        # True means already exist.
        result = {
            "username": False,
            "email": False
        }
        if data.get("username"):
            result["username"] = User.objects.filter(username=data["username"].lower()).exists()    #True
        if data.get("email"):
            result["email"] = User.objects.filter(email=data["email"].lower()).exists()             #True
        return self.success(result)



class UserChangeEmailAPI(APIView):
    @validate_serializer(UserChangeEmailSerializer)
    @login_required
    def post(self, request):
        data = request.data
        user = auth.authenticate(username=request.user.username, password=data["password"])
        if user:
            # 一些权限验证，双因素验证，二维码是否正确
            if user.two_factor_auth:
                if "tfa_code" not in data:
                    return self.error("tfa_required")
                if not OtpAuth(user.tfa_token).valid_totp(data["tfa_code"]):
                    return self.error("Invalid two factor verification code")
            # 邮箱不区分大小写
            data["new_email"] = data["new_email"].lower()
            if User.objects.filter(email=data["new_email"]).exists():
                return self.error("The email is owned by other account")
            user.email = data["new_email"]
            user.save()
            return self.success("Succeeded")
        else:
            return self.error("Wrong password")


class UserChangePasswordAPI(APIView):
    @validate_serializer(UserChangePasswordSerializer)
    @login_required
    def post(self, request):
        """
        User change password api
        """
        data = request.data
        username = request.user.username
        user = auth.authenticate(username=username, password=data["old_password"])
        if user:
            if user.two_factor_auth:
                if "tfa_code" not in data:
                    return self.error("tfa_required")
                if not OtpAuth(user.tfa_token).valid_totp(data["tfa_code"]):
                    return self.error("Invalid two factor verification code")
            user.set_password(data["new_password"])
            user.save()
            return self.success("Succeeded")
        else:
            return self.error("Invalid old password")


class ApplyResetPasswordAPI(APIView):
    # 重置密码
    @validate_serializer(ApplyResetPasswordSerializer)
    def post(self, request):
        # 首先判断是否登录
        if request.user.is_authenticated():
            return self.error("You have already logged in, are you kidding me? ")
        # 获得请求数据
        data = request.data
        # 获得验证码
        captcha = Captcha(request)
        # 验证码不成功返回无效的验证码信息
        if not captcha.check(data["captcha"]):
            return self.error("Invalid captcha")
        try:
            # 查询数据库获得邮箱，判断是否存在
            user = User.objects.get(email__iexact=data["email"])
        except User.DoesNotExist:
            return self.error("User does not exist")
        # 如果重置密码令牌失效，或者超过20分钟，返回错误提示
        if user.reset_password_token_expire_time and 0 < int(
                (user.reset_password_token_expire_time - now()).total_seconds()) < 20 * 60:
            return self.error("You can only reset password once per 20 minutes")
        # 更新重置密码令牌和失效时间
        user.reset_password_token = rand_str()
        user.reset_password_token_expire_time = now() + timedelta(minutes=20)
        user.save()
        #
        render_data = {
            "username": user.username,
            "website_name": SysOptions.website_name,
            "link": f"{SysOptions.website_base_url}/reset-password/{user.reset_password_token}"
        }
        # render_to_string： Loads a template and renders it with a context. Returns a string.
        # 加载一个模板，转换成string，发送到对应邮箱
        email_html = render_to_string("reset_password_email.html", render_data)
        send_email_async.delay(from_name=SysOptions.website_name_shortcut,
                               to_email=user.email,
                               to_name=user.username,
                               subject=f"Reset your password",
                               content=email_html)
        return self.success("Succeeded")


class ResetPasswordAPI(APIView):
    # 重置密码
    @validate_serializer(ResetPasswordSerializer)
    def post(self, request):
        data = request.data
        captcha = Captcha(request)
        # 获得验证吗并检查
        if not captcha.check(data["captcha"]):
            return self.error("Invalid captcha")
        try:
            user = User.objects.get(reset_password_token=data["token"])
        except User.DoesNotExist:
            return self.error("Token does not exist")
        # 这里的日期比较存在问题，原因是之前数据库字段设置错误，然后报错
        if user.reset_password_token_expire_time < now():
            return self.error("Token has expired")
        # 重置密码信息
        user.reset_password_token = None
        user.two_factor_auth = False
        user.set_password(data["password"])
        user.save()
        return self.success("Succeeded")

    # 注意：！！！！------>>>>>这里的session的获取和使用要在settings里面的中间件middleware设置好account的配置才能保存session
class SessionManagementAPI(APIView):
    # session的管理：------>>>>中间件的加载是有先后顺序的，不能颠倒顺序
    @login_required
    def get(self, request):
        engine = import_module(settings.SESSION_ENGINE)
        # 保存网站session是在session_store里面的
        session_store = engine.SessionStore
        # 当前的session，从请求数据里面获得
        current_session = request.session.session_key
        # session_keys从用户的session_keys里面获得
        session_keys = request.user.session_keys
        print(session_keys)
        # 置结果为空先
        result = []
        # 是否被修改标志为false
        modified = False
        # 从为用户保存的session_keys里面查找，并调用session_store保存到session里面去
        for key in session_keys[:]:
            session = session_store(key)
            # 如果缓存的session不存在或者已经失效，_session是一个类内部函数，但是这里需要访问返回缓存里面的session
            if not session._session:
                # 将用户的session_keys里面的无效key去除
                session_keys.remove(key)
                # 设置修改为真
                modified = True
                # 跳过本次循环for，直接进入下一次
                continue

            # 否则先定义一个字典，
            s = {}
            # 如果当前的current_session和用户保存的session中的key中有相等的，设置字典s的
            # current_session为真，同时也设置一下ip、user_agent、last_activity、ssession_key.
            if current_session == key:
                s["current_session"] = True
            s["ip"] = session["ip"]
            s["user_agent"] = session["user_agent"]
            s["last_activity"] = datetime2str(session["last_activity"])
            s["session_key"] = key
            # 最后将字典类型的s数据保存到结果result列表中，直至循环结束
            result.append(s)
        # 如果修改标志被修改过为True，更新用户信息到数据库
        if modified:
            request.user.save()
        # 最后将结果返回
        return self.success(result)

    @login_required
    def delete(self, request):
        # 从request数据的中获取session_key
        session_key = request.GET.get("session_key")
        # 如果没有session就报告参数错误
        if not session_key:
            return self.error("Parameter Error")
        # 有就删除session
        request.session.delete(session_key)
        # 如果get请求的数据在请求对应的user的session_keys列表里面的话，就将该
        # session_key去掉，然后更新一下用户数据，并返回成功，否则就返回无效的session_key
        if session_key in request.user.session_keys:
            request.user.session_keys.remove(session_key)
            request.user.save()
            return self.success("Succeeded")
        else:
            return self.error("Invalid session_key")


class UserRankAPI(APIView):
    # 不用登录，根据规则就可以查看排名
    def get(self, request):
        rule_type = request.GET.get("rule")
        # 如果规则类型不在给定的选项中，默认设置为acm的，接着查询数据库对应的用户信息
        if rule_type not in ContestRuleType.choices():
            rule_type = ContestRuleType.ACM
        profiles = UserProfile.objects.filter(user__admin_type=AdminType.REGULAR_USER, user__is_disabled=False) \
            .select_related("user")
        # 如果是ACM的话，就查询提交数目大于0的，按照ac数目进行排名
        if rule_type == ContestRuleType.ACM:
            profiles = profiles.filter(submission_number__gt=0).order_by("-accepted_number", "submission_number")
        else:
            # 否则就是OI的了，查找总分大于0，按照总分大小进行排名
            profiles = profiles.filter(total_score__gt=0).order_by("-total_score")
        # 分页返回查找的数据
        return self.success(self.paginate_data(request, profiles, RankInfoSerializer))


class ProfileProblemDisplayIDRefreshAPI(APIView):
    @login_required
    def get(self, request):
        profile = request.user.userprofile
        acm_problems = profile.acm_problems_status.get("problems", {})
        oi_problems = profile.oi_problems_status.get("problems", {})
        ids = list(acm_problems.keys()) + list(oi_problems.keys())
        if not ids:
            return self.success()
        display_ids = Problem.objects.filter(id__in=ids, visible=True).values_list("_id", flat=True)
        id_map = dict(zip(ids, display_ids))
        for k, v in acm_problems.items():
            v["_id"] = id_map[k]
        for k, v in oi_problems.items():
            v["_id"] = id_map[k]
        profile.save(update_fields=["acm_problems_status", "oi_problems_status"])
        return self.success()


class OpenAPIAppkeyAPI(APIView):
    @login_required
    def post(self, request):
        user = request.user
        if not user.open_api:
            return self.error("OpenAPI function is truned off for you")
        api_appkey = rand_str()
        user.open_api_appkey = api_appkey
        user.save()
        return self.success({"appkey": api_appkey})


class SSOAPI(CSRFExemptAPIView):
    @login_required
    def get(self, request):
        token = rand_str()
        request.user.auth_token = token
        request.user.save()
        return self.success({"token": token})

    @method_decorator(csrf_exempt)
    @validate_serializer(SSOSerializer)
    def post(self, request):
        try:
            user = User.objects.get(auth_token=request.data["token"])
        except User.DoesNotExist:
            return self.error("User does not exist")
        return self.success({"username": user.username, "avatar": user.userprofile.avatar, "admin_type": user.admin_type})
