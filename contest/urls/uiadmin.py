#!/usr/bin/env python
# -*-encoding:UTF-8-*-
from django.conf.urls import url

from ..views.viadmin import ContestAnnouncementAPI, ContestAPI, ACMContestHelper, DownloadContestSubmissions

# 管理员管理竞赛映射文件
urlpatterns = [
    url(r"^contest/?$", ContestAPI.as_view(), name="contest_admin_api"),
    url(r"^contest/announcement/?$", ContestAnnouncementAPI.as_view(), name="contest_announcement_admin_api"),

    # 需要结合前端测试
    url(r"^contest/acm_helper/?$", ACMContestHelper.as_view(), name="acm_contest_helper"),
    url(r"^download_submissions/?$", DownloadContestSubmissions.as_view(),name="acm_contest_helper"),
]