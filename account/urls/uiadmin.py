#!/usr/bin/env python
# -*-encoding:UTF-8-*-

from django.conf.urls import url

from ..views.viadmin import UserAdminAPI, GenerateUserAPI

urlpatterns = [
    url(r"^user/?$", UserAdminAPI.as_view(), name="user_admin_api"),
    url(r"^generate_user/?$", GenerateUserAPI.as_view(), name="generate_user_api"),
]

