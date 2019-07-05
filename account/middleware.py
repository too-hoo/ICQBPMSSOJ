#!/usr/bin/env python
# -*-encoding:UTF-8-*-

# 这个中间件非常关键，例如记录session等信息和配置信息
# 如果没用这个中间件，在测试的时候就知道使用不了session和ip等信息
# 同时还要将其配置到settings的中间件哪里
from django.conf import settings
from django.db import connection
from django.utils.timezone import now
from django.utils.deprecation import MiddlewareMixin

from myutils.api import JSONResponse
from account.models import User


class APITokenAuthMiddleware(MiddlewareMixin):
    # 调用接口的令牌验证中间件类
    def process_request(self, request):
        # 解析请求
        appkey = request.META.get("HTTP_APPKEY")
        if appkey:
            try:
                # 根据传入的appkey获取数据库的中的用户
                request.user = User.objects.get(open_api_appkey=appkey, open_api=True, is_disabled=False)
                request.csrf_processing_done = True
                # 验证方法为api_key
                request.auth_method = "api_key"
            except User.DoesNotExist:
                pass


class SessionRecordMiddleware(MiddlewareMixin):
    # session记录中间件
    def process_request(self, request):
        # 解析请求
        request.ip = request.META.get(settings.IP_HEADER, request.META.get("REMOTE_ADDR"))
        # 请求的用户，就是登录，在浏览器那边的用户，登录验证，并设置session
        if request.user.is_authenticated():
            session = request.session
            # session代理信息和IP配置
            session["user_agent"] = request.META.get("HTTP_USER_AGENT", "")
            session["ip"] = request.ip
            # 更新最新的活动事件为现在
            session["last_activity"] = now()
            # 用户sessions是从request里面获取得到的
            user_sessions = request.user.session_keys
            # user_sessions是一个list，没有就向里面append
            if session.session_key not in user_sessions:
                user_sessions.append(session.session_key)
                request.user.save()


class AdminRoleRequiredMiddleware(MiddlewareMixin):
    # 管理员角色要求中间件
    def process_request(self, request):
        # 解析请求信息
        path = request.path_info
        if path.startswith("/admin/") or path.startswith("/api/admin/"):
            # 虽然请求的是admin，但是你不是admin，当然不能通过,需要先登录
            if not (request.user.is_authenticated() and request.user.is_admin_role()):
                return JSONResponse.response({"error": "login-required", "data": "Please login in first"})


class LogSqlMiddleware(MiddlewareMixin):
    # sql日志的中间件
    def process_response(self, request, response):
        # 解析请求，设置字体颜色
        print("\033[94m", "#" * 30, "\033[0m")
        time_threshold = 0.03
        # 在默认的链接代理里面查找
        for query in connection.queries:
            if float(query["time"]) > time_threshold:
                print("\033[93m", query, "\n", "-" * 30, "\033[0m")
            else:
                print(query, "\n", "-" * 30)
        return response
