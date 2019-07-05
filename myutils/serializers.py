#!/usr/bin/env python
# -*-encoding:UTF-8-*-


from rest_framework import serializers

from options.options import SysOptions


class InvalidLanguage(serializers.ValidationError):
    # 无效的语言选择，此类作为报错的基础类，供下面的方法调用
    def __init__(self, name):
        super().__init__(detail=f"{name} is not a valid language")


class LanguageNameChoiceField(serializers.CharField):
    # 提交代码的时候进行的语言选择字段
    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        if data and data not in SysOptions.language_names:
            raise InvalidLanguage(data)
        return data


class SPJLanguageNameChoiceField(serializers.CharField):
    # 特殊评判的语言选择字段
    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        if data and data not in SysOptions.spj_language_names:
            raise InvalidLanguage(data)
        return data


class LanguageNameMultiChoiceField(serializers.ListField):
    # 多重语言选择
    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        for item in data:
            if item not in SysOptions.language_names:
                raise InvalidLanguage(item)
        return data


class SPJLanguageNameMultiChoiceField(serializers.ListField):
    # 特殊评判语言的多重选择
    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        for item in data:
            if item not in SysOptions.spj_language_names:
                raise InvalidLanguage(item)
        return data
