#!/usr/bin/env python
# -*-encoding:UTF-8-*-

from django.conf.urls import url

from ..views.viadmin import AnnouncementAdminAPI

# 注意：映射文件的路径后面是要加?$的，但是，有的情况下面不用加
urlpatterns = [
    url(r"^announcement/?$", AnnouncementAdminAPI.as_view(), name="announcement_admin_api"),
]