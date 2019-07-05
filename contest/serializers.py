#!/usr/bin/env python
# -*-encoding:UTF-8-*-
# 比赛管理序列化类

from myutils.api import UsernameSerializer, serializers

from .models import Contest, ContestAnnouncement, ContestRuleType
from .models import ACMContestRank, OIContestRank


class CreateContestSerializer(serializers.Serializer):
    # 创建比赛
    title = serializers.CharField(max_length=128)
    description = serializers.CharField()
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    rule_type = serializers.ChoiceField(choices=[ContestRuleType.ACM, ContestRuleType.OI])
    password = serializers.CharField(allow_blank=True, max_length=32)
    visible = serializers.BooleanField()
    real_time_rank = serializers.BooleanField()
    allowed_ip_ranges = serializers.ListField(child=serializers.CharField(max_length=32), allow_empty=True)


class EditContestSerializer(serializers.Serializer):
    # 编辑提交比赛信息
    id = serializers.IntegerField()
    title = serializers.CharField(max_length=128)
    description = serializers.CharField()
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    password = serializers.CharField(allow_blank=True, allow_null=True, max_length=32)
    visible = serializers.BooleanField()
    real_time_rank = serializers.BooleanField()
    allowed_ip_ranges = serializers.ListField(child=serializers.CharField(max_length=32))


class ContestAdminSerializer(serializers.ModelSerializer):
    # 比赛管理员信息
    created_by = UsernameSerializer()
    status = serializers.CharField()
    contest_type = serializers.CharField()

    class Meta:
        model = Contest
        fields = "__all__"


class ContestSerializer(ContestAdminSerializer):
    # 比赛序列化
    class Meta:
        model = Contest
        exclude = ("password", "visible", "allowed_ip_ranges")


class ContestAnnouncementSerializer(serializers.ModelSerializer):
    # 比赛通知
    created_by = UsernameSerializer()

    class Meta:
        model = ContestAnnouncement
        fields = "__all__"


class CreateContestAnnouncementSerializer(serializers.Serializer):
    # 创建比赛通知
    contest_id = serializers.IntegerField()
    title = serializers.CharField(max_length=128)
    content = serializers.CharField()
    visible = serializers.BooleanField()


class EditContestAnnouncementSerializer(serializers.Serializer):
    # 编辑比赛通知
    id = serializers.IntegerField()
    title = serializers.CharField(max_length=128, required=False)
    content = serializers.CharField(required=False, allow_blank=True)
    visible = serializers.BooleanField(required=False)


class ContestPasswordVerifySerializer(serializers.Serializer):
    # 比赛密码验证逻辑
    contest_id = serializers.IntegerField()
    password = serializers.CharField(max_length=30, required=True)


class ACMContestRankSerializer(serializers.ModelSerializer):
    # 比赛排名
    user = serializers.SerializerMethodField()

    class Meta:
        model = ACMContestRank
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.is_contest_admin = kwargs.pop("is_contest_admin", False)
        super().__init__(*args, **kwargs)

    def get_user(self, obj):
        return UsernameSerializer(obj.user, need_real_name=self.is_contest_admin).data


class OIContestRankSerializer(serializers.ModelSerializer):
    # OI比赛排名
    user = serializers.SerializerMethodField()

    class Meta:
        model = OIContestRank
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.is_contest_admin = kwargs.pop("is_contest_admin", False)
        super().__init__(*args, **kwargs)

    def get_user(self, obj):
        return UsernameSerializer(obj.user, need_real_name=self.is_contest_admin).data


class ACMContestHelperSerializer(serializers.Serializer):
    # 比赛帮助类
    contest_id = serializers.IntegerField()
    problem_id = serializers.CharField()
    rank_id = serializers.IntegerField()
    checked = serializers.BooleanField()


