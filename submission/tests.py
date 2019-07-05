from django.test import TestCase

from copy import deepcopy
from unittest import mock

from problem.models import Problem, ProblemTag
from myutils.api.tests import APITestCase
from .models import Submission

# 默认题目数据
DEFAULT_PROBLEM_DATA = {"_id": "A-110", "title": "test", "description": "<p>test</p>", "input_description": "test",
                        "output_description": "test", "time_limit": 1000, "memory_limit": 256, "difficulty": "Low",
                        "visible": True, "tags": ["test"], "languages": ["C", "C++", "Java", "Python2"], "template": {},
                        "samples": [{"input": "test", "output": "test"}], "spj": False, "spj_language": "C",
                        "spj_code": "", "test_case_id": "499b26290cc7994e0b497212e842ea85",
                        "test_case_score": [{"output_name": "1.out", "input_name": "1.in", "output_size": 0,
                                             "stripped_output_md5": "d41d8cd98f00b204e9800998ecf8427e",
                                             "input_size": 0, "score": 0}],
                        "rule_type": "ACM", "hint": "<p>test</p>", "source": "test"}

# 问题ID，用户ID，用户名，源代码，评测结果，信息，使用语言，统计信息
DEFAULT_SUBMISSION_DATA = {
    "problem_id": "1",
    "user_id": 1,
    "username": "test",
    "code": "xxxxxxxxxxxxxx",
    "result": -2,
    "info": {},
    "language": "C",
    "statistic_info": {}
}


# todo contest submission


class SubmissionPrepare(APITestCase):
    def _create_problem_and_submission(self):
        # 创建问题和提交信息，你要是超级管理员才能创建问题，同时也能提交信息ac题目
        user = self.create_admin("test", "test123", login=False)
        problem_data = deepcopy(DEFAULT_PROBLEM_DATA)
        tags = problem_data.pop("tags")
        problem_data["created_by"] = user
        # 创建题目
        self.problem = Problem.objects.create(**problem_data)
        # 标签添加
        for tag in tags:
            tag = ProblemTag.objects.create(name=tag)
            self.problem.tags.add(tag)
        self.problem.save()
        # 创建提交信息
        self.submission_data = deepcopy(DEFAULT_SUBMISSION_DATA)
        self.submission_data["problem_id"] = self.problem.id
        self.submission = Submission.objects.create(**self.submission_data)


class SubmissionListTest(SubmissionPrepare):
    def setUp(self):
        self._create_problem_and_submission()
        self.create_user("123", "345")
        self.url = self.reverse("submission_list_api")

    def test_get_submission_list(self):
        # 获取提交信息列表，限制为10条
        resp = self.client.get(self.url, data={"limit": "10"})
        self.assertSuccess(resp)


@mock.patch("submission.views.vicqbpmssoj.judge_task.delay")
class SubmissionAPITest(SubmissionPrepare):
    def setUp(self):
        # 创建问题和提交信息
        self._create_problem_and_submission()
        self.user = self.create_user("123", "test123")
        self.url = self.reverse("submission_api")

    def test_create_submission(self, judge_task):
        # post请求创建提交信息
        resp = self.client.post(self.url, self.submission_data)
        self.assertSuccess(resp)
        # 返回的信息中可以断言judge_task是被调用了的
        judge_task.assert_called()

    def test_create_submission_with_wrong_language(self, judge_task):
        # 默认是没有Python3的，更新一下提交信息使用的语言为python3
        self.submission_data.update({"language": "Python3"})
        resp = self.client.post(self.url, self.submission_data)
        self.assertFailed(resp)
        #
        self.assertDictEqual(resp.data, {"error": "error",
                                         "data": "Python3 is now allowed in the problem"})
        judge_task.assert_not_called()

