from django.db import models
from myutils.constants import ContestRuleType       # noqa
from django.utils.timezone import now
from myutils.models import JSONField

from account.models import User
from myutils.models import RichTextField
from myutils.constants import ContestStatus, ContestType

# Create your models here.


class Contest(models.Model):
    # 比赛类型字段对应的数据库表
    title = models.TextField()
    description = RichTextField()
    # 显示真实的排名或者缓存排名
    real_time_rank = models.BooleanField()
    password = models.TextField(null=True)
    # 枚举出来比赛的规则类型
    rule_type = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    create_time = models.DateTimeField(auto_now_add=True)
    last_update_time = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User)
    # 设置是否可见，false的话相当于删除
    visible = models.BooleanField(default=True)
    allowed_ip_ranges = JSONField(default=list)

    @property
    def status(self):
        if self.start_time > now():
            # 时间还没到，没开始，返回1
            return ContestStatus.CONTEST_NOT_START
        elif self.end_time < now():
            # 比赛已经结束 返回-1
            return ContestStatus.CONTEST_ENDED
        else:
            # 正在进行，返回0
            return ContestStatus.CONTEST_UNDERWAY

    @property
    def contest_type(self):
        # 比赛的类型，有公开的比赛和密码保护的比赛
        if self.password:
            return ContestType.PASSWORD_PROTECTED_CONTEST
        return ContestType.PUBLIC_CONTEST

    def problem_details_permission(self, user):
        # 返回一些关于问题的细节权限：规则类型、比赛状态、用户是否已经验证为超级用户和实时排名
        return self.rule_type == ContestRuleType.ACM or \
            self.status == ContestStatus.CONTEST_ENDED or \
            user.is_authenticated() and user.is_contest_admin(self) or \
            self.real_time_rank

    class Meta:
        db_table = "contest"
        ordering = ("-start_time",)


class AbstractContestRank(models.Model):
    # 抽象的比赛排名,这个是要被继承的
    user = models.ForeignKey(User)
    contest =models.ForeignKey(Contest)
    submission_number = models.IntegerField(default=0)

    class Meta:
        abstract = True


class ACMContestRank(AbstractContestRank):
    accepted_number = models.IntegerField(default=0)
    # 总时间仅仅是对ACM来说的，total_time = ac time + none-ac time * 20 * 60
    total_time = models.IntegerField(default=0)
    # {"23":{"is_ac":True,"ac_time":8999,"error_number":2,"is_first_ac":True}}
    # key is problem id
    submission_info = JSONField(default=dict)

    class Meta:
        db_table = "acm_contest_rank"


class OIContestRank(AbstractContestRank):
    total_score = models.IntegerField(default=0)
    # {"11",212}
    # key 就是problem id，value 是当前的分数
    submission_info = JSONField(default=dict)

    class Meta:
        db_table = "oi_contest_rank"


class ContestAnnouncement(models.Model):
    # 比赛对应的声明通知
    contest = models.ForeignKey(Contest)
    title = models.TextField()
    content = RichTextField()
    created_by = models.ForeignKey(User)
    visible = models.BooleanField(default=True)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "contest_announcement"
        ordering = ("-create_time",)
