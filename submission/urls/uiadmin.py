#!/usr/bin/env python
# -*-encoding:UTF-8-*-

from django.conf.urls import url

from ..views.viadmin import SubmissionRejudgeAPI

# 管理员重新评判
urlpatterns = [
    url(r"^submission/rejudge?$", SubmissionRejudgeAPI.as_view(), name="submission_rejudge_api"),
]
