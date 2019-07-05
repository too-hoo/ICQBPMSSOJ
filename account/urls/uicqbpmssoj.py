#!/usr/bin/env python
# -*-encoding:UTF-8-*-
from django.conf.urls import url

from ..views.vicqbpmssoj import (UserProfileAPI, AvatarUploadAPI, TwoFactorAuthAPI, CheckTFARequiredAPI,
                                 UserLoginAPI, UserLogoutAPI, UsernameOrEmailCheck, UserRegisterAPI,
                                 UserChangeEmailAPI, UserChangePasswordAPI, ApplyResetPasswordAPI,
                                 ResetPasswordAPI, SessionManagementAPI, UserRankAPI, ProfileProblemDisplayIDRefreshAPI,
                                 OpenAPIAppkeyAPI, SSOAPI)
from myutils.captcha.views import CaptchaAPIView

# 命名空间一定要和view里面的反转函数和模式匹配，特别实在测试的时候，一定要留意，命名空间一定要符合规则的写
urlpatterns = [
    url(r"^login/?$", UserLoginAPI.as_view(), name="user_login_api"),
    url(r"^logout/?$", UserLogoutAPI.as_view(), name="user_logout_api"),
    url(r"^captcha/?$", CaptchaAPIView.as_view(), name="show_captcha"),
    url(r"^register/?$", UserRegisterAPI.as_view(), name="user_register_api"),
    url(r"^profile/?$", UserProfileAPI.as_view(), name="user_profile_api"),
    url(r"^reset_password/?$", ResetPasswordAPI.as_view(), name="reset_password_api"),
    url(r"^change_email/?$", UserChangeEmailAPI.as_view(), name="user_change_email_api"),
    url(r"^change_password/?$", UserChangePasswordAPI.as_view(), name="user_change_password_api"),
    url(r"^apply_reset_password/?$", ApplyResetPasswordAPI.as_view(), name="apply_reset_password_api"),
    url(r"^check_username_or_email/?$", UsernameOrEmailCheck.as_view(), name="check_username_or_email"),
    url(r"^profile/fresh_display_id/?$", ProfileProblemDisplayIDRefreshAPI.as_view(), name="display_id_fresh"),
    url(r"^upload_avatar/?$", AvatarUploadAPI.as_view(), name="avatar_upload_api"),
    url(r"^tfa_required/?$", CheckTFARequiredAPI.as_view(), name="tfa_required_check"),
    url(r"^two_factor_auth/?$", TwoFactorAuthAPI.as_view(), name="two_factor_auth_api"),
    url(r"^user_rank/?$", UserRankAPI.as_view(), name="user_rank_api"),
    url(r"^open_api_appkey/?$", OpenAPIAppkeyAPI.as_view(), name="open_api_appkey_api"),
    url(r"^sso/?$", SSOAPI.as_view(), name="sso_api"),
    url(r"^sessions/?$", SessionManagementAPI.as_view(), name="session_management_api"),
]












