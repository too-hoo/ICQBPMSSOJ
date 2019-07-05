#!/usr/bin/env python
# -*-encoding:UTF-8-*-

import random
from django.db.models import Q, Count
from myutils.api import APIView
from account.decorators import check_contest_permission
from ..models import ProblemTag, Problem, ProblemRuleType
from ..serializers import ProblemSerializer, TagSerializer, ProblemSafeSerializer
from contest.models import ContestRuleType


class ProblemTagAPI(APIView):
    # 本类提供获取题目的标签
    def get(self, request):
        # 先统计一下题目的数目， 题目的数目要大于0，查找出数据库中的标签，返回序列化数据
        tags = ProblemTag.objects.annotate(problem_count=Count("problem")).filter(problem_count__gt=0)
        return self.success(TagSerializer(tags, many=True).data)


class PickOneAPI(APIView):
    # 还没测试
    def get(self, request):
        # 查找单条题目
        problems = Problem.objects.filter(contest_id__isnull=True, visible=True)
        count = problems.count()
        if count == 0:
            return self.error("No problem to pick")
        return self.success(problems[random.randint(0, count - 1)]._id)


class ProblemAPI(APIView):
    @staticmethod
    def _add_problem_status(request, queryset_values):
        # 内置添加问题状态方法，如果是一个登录的用户，要更新他的显示信息，例如：oi_problems_status等
        if request.user.is_authenticated():
            profile = request.user.userprofile
            acm_problems_status = profile.acm_problems_status.get("problems", {})
            oi_problems_status = profile.oi_problems_status.get("problems", {})
            # paginate data，queryset_values就是经过序列化的题目数据problem_data
            # 获取result，如果结果为空，problems的状态就是query_values(problem_data)
            results = queryset_values.get("results")
            if results is not None:
                problems = results
            else:
                problems = [queryset_values, ]
            for problem in problems:
                if problem["rule_type"] == ProblemRuleType.ACM:
                    problem["my_status"] = acm_problems_status.get(str(problem["id"]), {}).get("status")
                else:
                    problem["my_status"] = oi_problems_status.get(str(problem["id"]), {}).get("status")

    def get(self, request):
        # 用户获取问题详情页：获取列表和获取单个信息
        problem_id = request.GET.get("problem_id")
        if problem_id:
            try:
                problem = Problem.objects.select_related("created_by") \
                    .get(_id=problem_id, contest_id__isnull=True, visible=True)
                problem_data = ProblemSerializer(problem).data
                # 查找出信息之后要更新添加问题信息给用户数据状态
                self._add_problem_status(request, problem_data)
                return self.success(problem_data)
            except Problem.DoesNotExist:
                return self.error("Problem does not exist")

        limit = request.GET.get("limit")
        if not limit:
            return self.error("Limit is needed")

        # 从这里开始层层搜索过滤下去，先从Problem找出基础数据，然后筛选满足条件的情况
        problems = Problem.objects.select_related("created_by").filter(contest_id__isnull=True, visible=True)
        # 按照标签筛选
        tag_text = request.GET.get("tag")
        if tag_text:
            problems = problems.filter(tags__name=tag_text)

        # 搜索的情况
        keyword = request.GET.get("keyword", "").strip()
        if keyword:
            # 安关键字搜索，类似模糊搜索
            problems = problems.filter(Q(title__icontains=keyword) | Q(_id__icontains=keyword))

        # 难度筛选
        difficulty = request.GET.get("difficulty")
        if difficulty:
            problems = problems.filter(difficulty=difficulty)
        # 根据profile 为做过的题目添加标记
        data = self.paginate_data(request, problems, ProblemSerializer)
        self._add_problem_status(request, data)
        return self.success(data)


class ContestProblemAPI(APIView):
    # 普通用户的问题API
    def _add_problem_status(self, request, queryset_values):
        # 添加问题状态
        if request.user.is_authenticated():
            profile = request.user.userprofile
            if self.contest.rule_type == ContestRuleType.ACM:
                problems_status = profile.acm_problems_status.get("contest_problems", {})
            else:
                problems_status = profile.oi_problems_status.get("contest_problems", {})
            for problem in queryset_values:
                problem["my_status"] = problems_status.get(str(problem["id"]), {}).get("status")

    @check_contest_permission(check_type="problems")
    def get(self, request):
        # 获取问题的ID，这里是传入了contest_id的，但是没有使用contest_id来接受它，因为不需要，他根据contest_id
        # 直接就找到对应的contest，应为contest_id就是contest的唯一标识
        problem_id = request.GET.get("problem_id")

        if problem_id:
            # problem_id非空就查找该题目
            try:
                problem = Problem.objects.select_related("created_by").get(_id=problem_id,
                                                                           contest=self.contest,
                                                                           visible=True)
            except Problem.DoesNotExist:
                return self.error("Problem does not exist.")
            # 检查权限是否通过,并设置问题的状态信息
            if self.contest.problem_details_permission(request.user):
                problem_data = ProblemSerializer(problem).data
                self._add_problem_status(request, [problem_data, ])
            else:
                problem_data = ProblemSafeSerializer(problem).data
            return self.success(problem_data)

        # 这里的contest的标识就是contest_id，所以传入的参数一定要附加上contest_id
        contest_problems = Problem.objects.select_related("created_by").filter(contest=self.contest, visible=True)
        if self.contest.problem_details_permission(request.user):
            data = ProblemSerializer(contest_problems, many=True).data
            self._add_problem_status(request, data)
        else:
            data = ProblemSafeSerializer(contest_problems, many=True).data
        return self.success(data)
