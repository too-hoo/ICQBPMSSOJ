#!/usr/bin/env python
# -*-encoding:UTF-8-*-

# 这是一个神奇的装饰器类，有很多奇妙的问题等着

import functools
from problem.models import Problem
from contest.models import Contest, ContestType, ContestStatus, ContestRuleType
from myutils.api import JSONResponse, APIError
from .models import ProblemPermission


class BasePermissionDecorator(object):
    # 基础权限装饰器类型
    def __init__(self, func):
        self.func = func

    def __get__(self, obj, obj_type):
        return functools.partial(self.__call__, obj)

    def error(self, data):
        # 最常用就是在没有登录的时候出现的错误提示
        return JSONResponse.response({"error": "permission-denied", "data": data})

    def __call__(self, *args, **kwargs):
        self.request = args[1]

        # 检查一下是否有权限
        if self.check_permission():
            if self.request.user.is_disabled:
                return self.error("Your account is disabled")
            return self.func(*args, **kwargs)
        else:
            return self.error("Please login first")

    def check_permission(self):
        raise NotImplementedError()


class login_required(BasePermissionDecorator):
    # 使用超类的方法is_authenticated()判断是否登录了
    def check_permission(self):
        return self.request.user.is_authenticated()


class super_admin_required(BasePermissionDecorator):
    # 方法需要在model里面定义好is_super_admin
    def check_permission(self):
        user = self.request.user
        return user.is_authenticated() and user.is_super_admin()


class admin_role_required(BasePermissionDecorator):
    def check_permission(self):
        user = self.request.user
        return user.is_authenticated() and user.is_admin_role()


class problem_permission_required(admin_role_required):
    # 关于问题的权限:检查问题的权限和问起权限没有
    def check_permission(self):
        if not super(problem_permission_required, self).check_permission():
            return False
        if self.request.user.problem_permission == ProblemPermission.NONE:
            return False
        return True


def check_contest_permission(check_type="details"):
    """
     # 检查比赛是否有权限
    只供Class based view 使用，检查用户是否有权进入该contest, check_type 可选 details, problems, ranks, submissions
    若通过验证，在view中可通过self.contest获得该contest
    """
    def decorator(func):
        def _check_permission(*args, **kwargs):
            self = args[0]      #self 取到参数1
            request = args[1]   #self 取到参数2
            user = request.user
            # 从请求信息中取到contest_id
            if request.data.get("contest_id"):
                contest_id = request.data["contest_id"]
            else:
                contest_id = request.GET.get("contest_id")
            if not contest_id:
                return self.error("Parameter error, contest_id is required")

            try:
                # use self.contest to avoid query contest again in view.
                # 使用 self.contest 来避免再次在view里面查找contest(竞赛) # 调用django的ORM查找
                self.contest = Contest.objects.select_related("created_by").get(id=contest_id, visible=True)
            except Contest.DoesNotExist:
                return self.error("Contest %s doesn't exist" % contest_id)

            # 匿名用户（Anonymous）
            if not user.is_authenticated():
                return self.error("Please login first.")

            # 创建者和所用者
            if user.is_contest_admin(self.contest):
                return func(*args, **kwargs)

            if self.contest.contest_type == ContestType.PASSWORD_PROTECTED_CONTEST:
                # password error
                if self.contest.id not in request.session.get("accessible_contests", []):
                    return self.error("Password is required.")

            # regular user get contest problems, ranks etc. before contest started
            if self.contest.status == ContestStatus.CONTEST_NOT_START and check_type != "details":
                return self.error("Contest has not started yet.")

            # 检查用户是否有权限去获得在OI比赛中的ranks,submissions等信息
            if self.contest.status == ContestStatus.CONTEST_UNDERWAY and self.contest.rule_type == ContestRuleType.OI:
                if not self.contest.real_time_rank and (check_type == "ranks" or check_type == "submissions"):
                    return self.error(f"No permission to get {check_type}")

            return func(*args, **kwargs)
        return _check_permission
    return decorator


def ensure_created_by(obj, user):
    # 确保是由谁创建，本类主要由管理源创建比赛的时候调用，用于修改杯赛信息时候确保用户是否有权限
    # ，传入的比赛obj(contest)和用户user
    e = APIError(msg=f"{obj.__class__.__name__} does not exit") # 先定义出错信息用于抛出
    # 不是管理员自然报错，是管理员就范返回
    if not user.is_admin_role():
        raise e
    if user.is_super_admin():
        return
    # Return whether an object is an instance of a class or of a subclass thereof.
    # 返回一个对象是否是一个类的实例或者是一个子类，Problem归属与contest
    if isinstance(obj, Problem):
        # 不能管理所有问题，通知这个比赛也不是其创建的
        if not user.can_mgmt_all_problem() and obj.created_by != user:
            raise e
    elif obj.created_by != user:
        raise e
