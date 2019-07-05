#!/usr/bin/env python
# -*-encoding:UTF-8-*-
from django.conf.urls import url

from ..views.viadmin import (ContestProblemAPI, ProblemAPI, TestCaseAPI,
                             MakeContestProblemPublicAPIView, CompileSPJAPI, AddContestProblemAPI,
                                ExportProblemAPI, ImportProblemAPI, FPSProblemImport)

# 管理员的比赛问题的映射路径：测试用例、特殊评判编译、题目、比赛题目、比赛题目公开、
# 公开题目添加到比赛、导入导题目、通过fps导入题目
urlpatterns = [
    url(r"^test_case/?$", TestCaseAPI.as_view(), name="test_case_api"),
    url(r"^problem/?$", ProblemAPI.as_view(), name="problem_admin_api"),
    url(r"^contest_problem/make_public/?$", MakeContestProblemPublicAPIView.as_view(), name="make_public_api"),
    url(r"^contest/add_problem_from_public/?$", AddContestProblemAPI.as_view(), name="add_contest_problem_from_public_api"),
    url(r"^contest/problem/?$", ContestProblemAPI.as_view(), name="contest_problem_admin_api"),
    # 需要借助前端测试
    url(r"^compile_spj/?$", CompileSPJAPI.as_view(), name="compile_spj"),
    url(r"^export_problem/?$", ExportProblemAPI.as_view(), name="export_problem_api"),
    url(r"^import_problem/?$", ImportProblemAPI.as_view(), name="import_problem_api"),
    url(r"^import_fps/?$", FPSProblemImport.as_view(), name="fps_problem_api"),
]


