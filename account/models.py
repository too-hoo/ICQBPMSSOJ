from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.conf import settings
from myutils.models import JSONField

# Create your models here.


class AdminType(object):
    REGULAR_USER = "Regular User"
    ADMIN = "Admin"
    SUPER_ADMIN = "Super Admin"


class ProblemPermission(object):
    NONE = "None"
    OWN = "Own"
    ALL = "All"


class UserManager(models.Manager):
    # 用户管理员类
    use_in_migrations = True

    def get_by_natural_key(self, username):
        return self.get(**{f"{self.model.USERNAME_FIELD}__iexact": username})


class User(AbstractBaseUser):
    # 继承抽象基础用户类
    username = models.TextField(unique=True)
    email = models.TextField(null=True)
    create_time = models.DateField(auto_now_add=True,null=True)
    # 用户类型的一种
    admin_type = models.TextField(default=AdminType.REGULAR_USER)
    problem_permission = models.TextField(default=ProblemPermission.NONE)
    reset_password_token = models.TextField(null=True)
    reset_password_token_expire_time = models.DateTimeField(null=True)
    # SSO auth token （Single Sign On）单点登录令牌
    auth_token = models.TextField(null=True)
    two_factor_auth = models.BooleanField(default=False)
    tfa_token = models.TextField(null=True)
    session_keys = JSONField(default=list)
    # open api key 开放的api 秘钥
    open_api = models.BooleanField(default=False)
    open_api_appkey = models.TextField(null=True)
    is_disabled = models.BooleanField(default=False)

    # 用户名域和请求域（邮箱）
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    # 之前因为写错：调用用户管理员，调试的时候将object 注释掉，就是进行单元测试的时候
    # 注意是objects！！！！
    objects = UserManager()

    def is_admin(self):
        # 普通管理员
        return self.admin_type == AdminType.ADMIN

    def is_super_admin(self):
        # 超级管理员
        return self.admin_type == AdminType.SUPER_ADMIN

    def is_admin_role(self):
        # 只有两种类型的管理员：普通和超级
        return self.admin_type in [AdminType.ADMIN, AdminType.SUPER_ADMIN]

    def can_mgmt_all_problem(self):
        # 能够管理所有的问题
        return self.problem_permission == ProblemPermission.ALL

    def is_contest_admin(self, contest):
        # 仅仅是比赛的管理员,自己管理自己创建的比赛，也可以是超级管理员来管理自己创建的比赛
        return self.is_authenticated() and (contest.created_by == self or self.admin_type == AdminType.SUPER_ADMIN)

    class Meta:
        db_table = "user"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # acm_problems_status examples:
    # {
    #     "problems": {
    #         "1": {
    #             "status": JudgeStatus.ACCEPTED,
    #             "_id": "1000"
    #         }
    #     },
    #     "contest_problems": {
    #         "1": {
    #             "status": JudgeStatus.ACCEPTED,
    #             "_id": "1000"
    #         }
    #     }
    # }
    acm_problems_status = JSONField(default=dict)
    # 类似于acm_problems_status，但是仅仅是添加了score字段
    oi_problems_status = JSONField(default=dict)

    real_name = models.TextField(null=True)
    # 头像的这个东西要专门留意一下
    avatar = models.TextField(default=f"{settings.AVATAR_URI_PREFIX}/default.png")
    blog = models.URLField(null=True)
    mood = models.TextField(null=True)
    github = models.TextField(null=True)
    school = models.TextField(null=True)
    major = models.TextField(null=True)
    language = models.TextField(null=True)
    # for acm
    accepted_number = models.IntegerField(default=0)
    # for oi
    total_score = models.BigIntegerField(default=0)
    submission_number = models.IntegerField(default=0)

    def add_accepted_problem_number(self):
        # ac 数目++
        self.accepted_number = models.F("accepted_number") + 1
        self.save()

    def add_submission_number(self):
        # 提交数目++
        self.submission_number = models.F("submission_number") + 1
        self.save()

    def add_score(self, this_time_score, last_time_score=None):
        # 注意：计算总分时候，应该先减掉上一次该题所得的分数，然后再加上本次所得的分数
        last_time_score = last_time_score or 0
        self.total_score = models.F("total_score") - last_time_score + this_time_score
        self.save()

    class Meta:
        db_table = "user_profile"

























