from django.db import models
from myutils.models import JSONField

from myutils.models import RichTextField
from myutils.constants import Choices
from account.models import User
from contest.models import Contest

# Create your models here.


class ProblemTag(models.Model):
    name = models.TextField()

    class Meta:
        db_table = "problem_tag"


class ProblemRuleType(Choices):
    ACM = "ACM"
    OI = "OI"


class ProblemDifficulty(object):
    High = "High"
    Mid = "Mid"
    Low = "Low"


class Problem(models.Model):
    # 显示问题的ID
    _id = models.TextField(db_index=True)
    contest = models.ForeignKey(Contest,null=True)
    # 对于比赛的问题来说
    is_public = models.BooleanField(default=False)
    title = models.TextField()
    # Html 文本输入
    description = RichTextField()
    input_description = RichTextField()
    output_description = RichTextField()
    # [{input:"test",output:"123"},{input:"test123",output:"456"}]
    samples = JSONField()
    test_case_id = models.TextField()
    # [{"input_name":"1.in","output_name":"1.out","score":0}]
    # 测试用例的分数
    test_case_score = JSONField()
    hint = RichTextField(null=True)
    languages = JSONField()
    template = JSONField()
    create_time = models.DateTimeField(auto_now_add=True)
    # 对于最新的更新时间这里不能使用 auto_now
    last_update_time = models.DateTimeField(null=True)
    created_by = models.ForeignKey(User)
    # ms(毫秒)
    time_limit = models.IntegerField()
    # MB
    memory_limit = models.IntegerField()
    # 下面的是与特殊评判相关的字段
    spj = models.BooleanField(default=False)
    spj_language = models.TextField(null=True)
    spj_code = models.TextField(null=True)
    spj_version = models.TextField(null=True)
    spj_compile_ok = models.BooleanField(default=False)
    rule_type = models.TextField()
    visible = models.BooleanField(default=True)
    difficulty = models.TextField()
    # 问题的标签对应的是多对多的
    tags = models.ManyToManyField(ProblemTag)
    source = models.TextField(null=True)
    # 对于OI 模式
    total_score = models.IntegerField(default=0)
    submission_number = models.BigIntegerField(default=0)
    accepted_number = models.BigIntegerField(default=0)
    # 对于提交之后该题目的统计信息，格式有ac和wa
    # {JudgeStatus.ACCEPTED:3,JudgeStatus.WRONG_ANSWER:11},数字代表的是计数
    statistic_info = JSONField(default=dict)

    class Meta:
        db_table = "problem"
        unique_together = (("_id", "contest"),)
        ordering = ("create_time",)

    def add_submission_number(self):
        # 增加提交的数目
        self.submission_number = models.F("submission_number") + 1
        self.save(update_fields=["submission_number"])

    def add_ac_number(self):
        #  计数器，每次ac一题，数目+1，增加通过的数目，当self.accepted_number=1时，是首次AC
        self.accepted_number = models.F("accepted_number") + 1
        self.save(update_fields=["accepted_number"])
