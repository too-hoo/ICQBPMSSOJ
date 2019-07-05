#!/usr/bin/env python
# -*-encoding:UTF-8-*-
from django.conf.urls import url
from ..views.vicqbpmssoj import ContestRankAPI
from ..views.vicqbpmssoj import ContestAnnouncementListAPI
from ..views.vicqbpmssoj import ContestPasswordVerifyAPI, ContestAccessAPI
from ..views.vicqbpmssoj import ContestListAPI, ContestAPI


# 用户登录的api映射文件
# 可以看到contest_api和contest_list_api请求的是同样的地址
urlpatterns = [
    url(r"^contest/?$", ContestAPI.as_view(), name="contest_api"),
    url(r"^contests/?$", ContestListAPI.as_view(), name="contest_list_api"),
    url(r"^contest/password/?$", ContestPasswordVerifyAPI.as_view(), name="contest_password_api"),
    url(r"^contest/announcement/?$", ContestAnnouncementListAPI.as_view(), name="contest_announcement_api"),
    url(r"^contest/access/?$", ContestAccessAPI.as_view(), name="contest_access_api"),
    url(r"^contest_rank/?$", ContestRankAPI.as_view(), name="contest_rank_api"),
]
