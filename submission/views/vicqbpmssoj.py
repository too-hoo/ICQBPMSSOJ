#!/usr/bin/env python
# -*-encoding:UTF-8-*-

import ipaddress

from account.decorators import login_required, check_contest_permission
from contest.models import ContestStatus, ContestRuleType
from judge.tasks import judge_task
from options.options import SysOptions
# from judge.dispatcher import JudgeDispatcher
from problem.models import Problem, ProblemRuleType
from myutils.api import APIView, validate_serializer
from myutils.cache import cache
from myutils.captcha import Captcha
from myutils.throttling import TokenBucket
from ..models import Submission
from ..serializers import (CreateSubmissionSerializer, SubmissionModelSerializer,
                           ShareSubmissionSerializer)
from ..serializers import SubmissionSafeModelSerializer, SubmissionListSerializer


class SubmissionAPI(APIView):
    def throttling(self, request):
        # 使用 open_api 的请求暂不做限制
        auth_method = getattr(request, "auth_method", "")
        if auth_method == "api_key":
            return
        # 流量限制
        user_bucket = TokenBucket(key=str(request.user.id),
                                  redis_conn=cache, **SysOptions.throttling["user"])
        can_consume, wait = user_bucket.consume()
        if not can_consume:
            return "Please wait %d seconds" % (int(wait))

        # ip_bucket = TokenBucket(key=request.session["ip"],
        #                         redis_conn=cache, **SysOptions.throttling["ip"])
        # can_consume, wait = ip_bucket.consume()
        # if not can_consume:
        #     return "Captcha is required"

    @check_contest_permission(check_type="problems")
    def check_contest_permission(self, request):
        # 检查参加比赛权限
        contest = self.contest
        # 测试提交信息时候必须要在比赛期间才能提交
        if contest.status == ContestStatus.CONTEST_ENDED:
            return self.error("The contest have ended")
        # 检查IP地址格式是否正确，同时还要在允许的范围之内，IP从session的获取，本地为127.0.0.1
        if not request.user.is_contest_admin(contest):
            user_ip = ipaddress.ip_address(request.session.get("ip"))
            if contest.allowed_ip_ranges:
                # 比赛要求IP地址，非空时进行检查，如果cidr网址不在允许范围就报错
                if not any(user_ip in ipaddress.ip_network(cidr, strict=False) for cidr in contest.allowed_ip_ranges):
                    return self.error("Your IP is not allowed in this contest")

    @validate_serializer(CreateSubmissionSerializer)
    @login_required
    def post(self, request):
        # 创建提交信息，
        data = request.data
        #
        hide_id = False
        if data.get("contest_id"):
            error = self.check_contest_permission(request)
            if error:
                return error
            contest = self.contest
            if not contest.problem_details_permission(request.user):

                hide_id = True
        # 检查验证码
        if data.get("captcha"):
            if not Captcha(request).check(data["captcha"]):
                return self.error("Invalid captcha")
        error = self.throttling(request)
        if error:
            return self.error(error)

        try:
            # 检查对应的提交信息中的题目是否存在
            problem = Problem.objects.get(id=data["problem_id"], contest_id=data.get("contest_id"), visible=True)
        except Problem.DoesNotExist:
            return self.error("Problem not exist")
        # 检查语言是否在允许的范围内
        if data["language"] not in problem.languages:
            return self.error(f"{data['language']} is now allowed in the problem")
        # 将提交信息写入数据库
        submission = Submission.objects.create(user_id=request.user.id,
                                               username=request.user.username,
                                               language=data["language"],
                                               code=data["code"],
                                               problem_id=problem.id,
                                               ip=request.session["ip"],
                                               contest_id=data.get("contest_id"))
        # use this for debug
        # JudgeDispatcher(submission.id, problem.id).judge()
        # 提交到判题异步队列里面去
        judge_task.delay(submission.id, problem.id)
        if hide_id:
            return self.success()
        else:
            return self.success({"submission_id": submission.id})

    @login_required
    def get(self, request):
        # 获取提交信息
        submission_id = request.GET.get("id")
        if not submission_id:
            return self.error("Parameter id doesn't exist")
        try:
            submission = Submission.objects.select_related("problem").get(id=submission_id)
        except Submission.DoesNotExist:
            return self.error("Submission doesn't exist")
        if not submission.check_user_permission(request.user):
            return self.error("No permission for this submission")

        # 提交信息存在就返回提交信息的序列化数据
        if submission.problem.rule_type == ProblemRuleType.OI or request.user.is_admin_role():
            submission_data = SubmissionModelSerializer(submission).data
        else:
            submission_data = SubmissionSafeModelSerializer(submission).data
        # 是否有权限取消共享
        submission_data["can_unshare"] = submission.check_user_permission(request.user, check_share=False)
        return self.success(submission_data)

    @validate_serializer(ShareSubmissionSerializer)
    @login_required
    def put(self, request):
        """
        share submission
        # 分享提交信息，修改提交信息
        """
        try:
            submission = Submission.objects.select_related("problem").get(id=request.data["id"])
        except Submission.DoesNotExist:
            return self.error("Submission doesn't exist")
        if not submission.check_user_permission(request.user, check_share=False):
            return self.error("No permission to share the submission")
        # 正在进行的比赛不能分享提交信息，预防作弊
        if submission.contest and submission.contest.status == ContestStatus.CONTEST_UNDERWAY:
            return self.error("Can not share submission now")
        # 比赛结束而且有权限就可以分享，设置分享就是一种对提交信息的修改
        submission.shared = request.data["shared"]
        submission.save(update_fields=["shared"])
        return self.success()


class SubmissionListAPI(APIView):
    # 用户提交信息列表显示接口
    def get(self, request):
        # 返回提交信息列表
        if not request.GET.get("limit"):
            return self.error("Limit is needed")
        # 比赛的ID为空，就报错
        if request.GET.get("contest_id"):
            return self.error("Parameter error")

        submissions = Submission.objects.filter(contest_id__isnull=True).select_related("problem__created_by")
        problem_id = request.GET.get("problem_id")
        # 默认没有设置myself，所以这里为空
        myself = request.GET.get("myself")
        result = request.GET.get("result")
        username = request.GET.get("username")
        # 提交的题目非空，就查询数据库，返回相应的提交信息
        if problem_id:
            try:
                problem = Problem.objects.get(_id=problem_id, contest_id__isnull=True, visible=True)
            except Problem.DoesNotExist:
                return self.error("Problem doesn't exist")
            submissions = submissions.filter(problem=problem)
        # myself非空且==1，活或者没有显示所有的提交信息列表的时候，仅仅过滤一下当前用户的提交信息，层层过滤
        if (myself and myself == "1") or not SysOptions.submission_list_show_all:
            submissions = submissions.filter(user_id=request.user.id)
        elif username:
            submissions = submissions.filter(username__icontains=username)
        if result:
            submissions = submissions.filter(result=result)
        # 分页返回数据
        data = self.paginate_data(request, submissions)
        data["results"] = SubmissionListSerializer(data["results"], many=True, user=request.user).data
        return self.success(data)


class ContestSubmissionListAPI(APIView):
    # 比赛提交信息显示API
    @check_contest_permission(check_type="submissions")
    def get(self, request):
        # 获取比赛提交信息
        if not request.GET.get("limit"):
            return self.error("Limit is needed")

        contest = self.contest
        # 根据比赛的id查找提交的信息
        submissions = Submission.objects.filter(contest_id=contest.id).select_related("problem__created_by")
        # 获取题目id、是否是自己，提交信息结果，用户名
        problem_id = request.GET.get("problem_id")
        myself = request.GET.get("myself")
        result = request.GET.get("result")
        username = request.GET.get("username")
        if problem_id:
            try:
                problem = Problem.objects.get(_id=problem_id, contest_id=contest.id, visible=True)
            except Problem.DoesNotExist:
                return self.error("Problem doesn't exist")
            #  找到该问题然后将包含该问题的提交信息过滤出来
            submissions = submissions.filter(problem=problem)

        # 下面其实就是按条件查询：是自己的、指定用户的、安结果查，分别得到不同的过滤结果，
        # 这一个查询都是基于按比赛id和题目id查出的基础之上的
        if myself and myself == "1":
            submissions = submissions.filter(user_id=request.user.id)
        elif username:
            submissions = submissions.filter(username__icontains=username)
        if result:
            submissions = submissions.filter(result=result)

        # filter the test submissions submitted before contest start
        # 比赛的状态开始和结束之后，将从比赛开始的那一刻起的提交信息查询出来，之前的就不要的了
        if contest.status != ContestStatus.CONTEST_NOT_START:
            submissions = submissions.filter(create_time__gte=contest.start_time)

        # 封榜的时候只能看到自己的提交
        if contest.rule_type == ContestRuleType.ACM:
            # 如果封榜后，而你又不是比赛的创建者，不能看到其他人的信息，只能看见自己的
            if not contest.real_time_rank and not request.user.is_contest_admin(contest):
                submissions = submissions.filter(user_id=request.user.id)

        # 最后分页返回查询出来的经过序列化的数据(多条)
        data = self.paginate_data(request, submissions)
        data["results"] = SubmissionListSerializer(data["results"], many=True, user=request.user).data
        return self.success(data)


class SubmissionExistsAPI(APIView):
    # 提交信息是否存在
    def get(self, request):
        if not request.GET.get("problem_id"):
            return self.error("Parameter error, problem_id is required")
        return self.success(request.user.is_authenticated() and
                            Submission.objects.filter(problem_id=request.GET["problem_id"],
                                                      user_id=request.user.id).exists())


