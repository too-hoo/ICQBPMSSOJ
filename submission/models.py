from django.db import models
from myutils.models import JSONField
from myutils.shortcuts import rand_str
from problem.models import Problem
from contest.models import Contest


# Create your models here.
class JudgeStatus:
    # 测评的状态
    COMPILE_ERROR = -2
    WRONG_ANSWER = -1
    ACCEPTED = 0
    CPU_TIME_LIMIT_EXCEEDED = 1
    REAL_TIME_LIMIT_EXCEEDED = 2
    MEMORY_LIMIT_EXCEEDED = 3
    RUNTIME_ERROR = 4
    SYSTEM_ERROR = 5
    PENDING = 6
    JUDGING = 7
    PARTIALLY_ACCEPTED = 8


class Submission(models.Model):
    # 提交信息
    id = models.TextField(default=rand_str, primary_key=True, db_index=True)
    contest = models.ForeignKey(Contest, null=True)
    problem = models.ForeignKey(Problem)
    create_time = models.DateTimeField(auto_now_add=True)
    user_id = models.IntegerField(db_index=True)
    username = models.TextField()
    code = models.TextField()
    # 默认的结果是pending
    result = models.IntegerField(db_index=True, default=JudgeStatus.PENDING)
    # 下面的是从JudgeServer返回的判题信息
    info = JSONField(default=dict)
    language = models.TextField()
    # 默认不公开代码
    shared = models.BooleanField(default=False)
    # 存储该提交所用的时间和内存的使用量，方便提交列表显示
    # {time_cost:"", memory_cost:"", err_info: "", score: 0}
    statistic_info = JSONField(default=dict)
    ip = models.TextField(null=True)

    def check_user_permission(self, user, check_share=True):
        """
        检查用户的权限，是否有权限分享
        :param user: 当前用户
        :param check_share:
        :return:
        """
        return self.user_id == user.id or \
            (check_share and self.shared is True) or \
            user.is_super_admin() or \
            user.can_mgmt_all_problem() or \
            self.problem.created_by_id == user.id

    class Meta:
        db_table = "submission"
        ordering = ("-create_time",)

    def __str__(self):
        # id是字符串类型的
        return self.id




















