#!/usr/bin/env python
# -*-encoding:UTF-8-*-

from rest_framework import serializers


class UsernameSerializer(serializers.Serializer):
    # 用户名序列化器:需要实现超类的方法
    # 例如用户排名信息就调用此类
    id = serializers.IntegerField()
    username = serializers.CharField()
    real_name = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        # 初始化真实名字
        self.need_real_name = kwargs.pop("need_real_name", False)
        super().__init__(*args, **kwargs)

    def get_real_name(self, obj):
        return obj.userprofile.real_name if self.need_real_name else None
