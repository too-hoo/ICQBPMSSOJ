#!/usr/bin/env python
# -*-encoding:UTF-8-*-
from django.conf.urls import url

from ..views.vicqbpmssoj import ProblemTagAPI, ProblemAPI, ContestProblemAPI, PickOneAPI

# 普通用户查看：题目标签、查看题目、pickone、查看比赛问题
urlpatterns = [
    url(r"^problem/tags/?$", ProblemTagAPI.as_view(), name="problem_tag_list_api"),
    url(r"^problem/?$", ProblemAPI.as_view(), name="problem_api"),
    url(r"^contest/problem/?$", ContestProblemAPI.as_view(), name="contest_problem_api"),
    # 需要借助前端测试
    url(r"^pickone/?$", PickOneAPI.as_view(), name="pick_one_api"),
]
