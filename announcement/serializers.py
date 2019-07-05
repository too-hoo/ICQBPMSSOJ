#!/usr/bin/env python
# -*-encoding:UTF-8-*-

from myutils.api import serializers
from myutils.api._serializers import UsernameSerializer

from .models import Announcement


class CreateAnnouncementSerializer(serializers.Serializer):
    # 创建通知
    title = serializers.CharField(max_length=64)
    content = serializers.CharField(max_length=1024 * 1024 * 8)
    visible = serializers.BooleanField()


class AnnouncementSerializer(serializers.ModelSerializer):
    # 通知序列化器
    created_by = UsernameSerializer()

    class Meta:
        model = Announcement
        fields = "__all__"


class EditAnnouncementSerializer(serializers.Serializer):
    # 编辑通知
    id = serializers.IntegerField()
    title = serializers.CharField(max_length=64)
    content = serializers.CharField(max_length=1024*1024*8)
    visible = serializers.BooleanField()



