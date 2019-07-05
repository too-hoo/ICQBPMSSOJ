#!/usr/bin/env python
# -*-encoding:UTF-8-*-

from myutils.api import serializers
from .models import JudgeServer


class EditSMTPConfigSerializer(serializers.Serializer):
    # 编辑邮件配置类
    server = serializers.CharField(max_length=128)
    port = serializers.IntegerField(default=25)
    email = serializers.CharField(max_length=256)
    password = serializers.CharField(max_length=128, required=False, allow_null=True, allow_blank=True)
    tls = serializers.BooleanField()


class CreateSMTPConfigSerializer(EditSMTPConfigSerializer):
    # 创建邮件配置类
    password = serializers.CharField(max_length=128)


class TestSMTPConfigSerializer(serializers.Serializer):
    # 测试邮件配置类
    email = serializers.EmailField()


class CreateEditWebsiteConfigSerializer(serializers.Serializer):
    # 创建编辑网站配置类
    website_base_url = serializers.CharField(max_length=128)
    website_name = serializers.CharField(max_length=64)
    website_name_shortcut = serializers.CharField(max_length=64)
    website_footer = serializers.CharField(max_length=1024 * 1024)
    allow_register = serializers.BooleanField()
    submission_list_show_all = serializers.BooleanField()


class JudgeServerSerializer(serializers.ModelSerializer):
    # 判题服务器类， 模板序列化
    status = serializers.CharField()

    class Meta:
        model = JudgeServer
        fields = "__all__"


class JudgeServerHeartbeatSerializer(serializers.Serializer):
    # 判题服务器请求响应序列化类
    hostname = serializers.CharField(max_length=128)
    judger_version = serializers.CharField(max_length=32)
    cpu_core = serializers.IntegerField(min_value=1)
    memory = serializers.FloatField(min_value=0, max_value=100)
    cpu = serializers.FloatField(min_value=0, max_value=100)
    action = serializers.ChoiceField(choices=("heartbeat", ))
    service_url = serializers.CharField(max_length=256)


class EditJudgeServerSerializer(serializers.Serializer):
    # 编辑判题服务器类
    id = serializers.IntegerField()
    is_disabled = serializers.BooleanField()





















