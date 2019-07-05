#!/usr/bin/env python
# -*-encoding:UTF-8-*-

import os
from django.core.cache import cache
from django.db import transaction, IntegrityError

from myutils.constants import CacheKey
from myutils.shortcuts import rand_str
from judge.languages import languages
from .models import SysOptions as SysOptionsModel


# 获取系统的评判机器的命令，非空就返回，否则就生成一个，要设置的，否则就是空的
def default_token():
    token = os.environ.get("JUDGE_SERVER_TOKEN")
    return token if token else rand_str()


class OptionKeys:
    # 系统关键字选择
    website_base_url = "website_base_url"
    website_name = "website_name"
    website_name_shortcut = "website_name_shortcut"
    website_footer = "website_footer"
    allow_register = "allow_register"
    submission_list_show_all = "submission_list_show_all"
    smtp_config = "smtp_config"
    judge_server_token = "judge_server_token"
    throttling = "throttling"
    languages = "languages"


class OprionDefaultValue:
    # 网站关键字的值
    # 基本的URL
    website_base_url = "http://127.0.0.1"
    # 网站的名称和简称和页脚
    website_name = "ICQBPMSSOJ"
    website_name_shortcut = "ICQBPMSSOJ"
    website_footer = "ICQBPMSSOJ FOOTER"
    # 允许用户注册和显示所有的提交信息
    allow_register = True
    submission_list_show_all = True
    # 邮件配置默认为空，是一个字典，等待接受传入的配置信息
    smtp_config = {}
    # 判题服务器的令牌为默认的令牌
    judge_server_token = default_token
    # 流量限制
    throttling = {"ip": {"capacity": 100, "fill_rate": 0.1, "default_capacity": 50},
                  "user": {"capacity": 20, "fill_rate": 0.03, "default_capacity": 10}}
    languages = languages


class _SysOptionsMeta(type):
    # 网站的实体类的私有方法初始化
    # mcs指元类(metaclass)，也是指的是类本身
    # 本类使用缓存的机制包括设置、删除、获取和重建
    @classmethod
    def _set_cache(mcs, option_key, option_value):
        cache.set(f"{CacheKey.option}:{option_key}", option_value, timeout=60)

    @classmethod
    def _del_cache(mcs, option_key):
        cache.delete(f"{CacheKey.option}:{option_key}")

    @classmethod
    def _get_keys(cls):
        return [key for key in OptionKeys.__dict__ if not key.startswith("__")]

    def rebuild_cache(cls):
        # 重新构建缓存
        for key in cls._get_keys():
            # get option 的时候会写cache的
            cls._get_option(key, use_cache=False)

    @classmethod
    def _init_option(mcs):
        # 当系统不存在传入的对应的键是，初始化系统选项：没有就创建，当创建不成功的时候可能出现的情况就是IntegrityError
        for item in mcs._get_keys():
            if not SysOptionsModel.objects.filter(key=item).exists():
                default_value = getattr(OprionDefaultValue, item)
                if callable(default_value):
                    default_value = default_value()
                try:
                    SysOptionsModel.objects.create(key=item, value=default_value)
                except IntegrityError:
                    pass

    @classmethod
    def _get_option(mcs, option_key, use_cache=True):
        # 获取选项，私有方法，对系统的选项的查询时候会被调用
        # 首先会尝试查看缓存，如果缓存存在对应的值就直接使用缓存返回，否则才查找数据库
        try:
            if use_cache:
                option = cache.get(f"{CacheKey.option}:{option_key}")
                if option:
                    return option
            # 首先是根据穿过来的key查找数据库，如果找到就得到value，同时设置一下缓存，方便下一次快速调用
            option = SysOptionsModel.objects.get(key=option_key)
            value = option.value
            mcs._set_cache(option_key, value)
            return value
        except SysOptionsModel.DoesNotExist:
            mcs._init_option()
            return mcs._get_option(option_key, use_cache=use_cache)

    @classmethod
    def _set_option(mcs, option_key: str, option_value):
        # 设置选项(私有),对内部的属性进行设置调用的方法
        try:
            # 原子操作，不成功就会退
            with transaction.atomic():
                option = SysOptionsModel.objects.select_for_update().get(key=option_key)
                option.value = option_value
                option.save()
                mcs._del_cache(option_key)
        except SysOptionsModel.DoesNotExist:
            mcs._init_option()
            mcs._set_option(option_key, option_value)

    @classmethod
    def _increment(mcs, option_key):
        # 增加
        try:
            # 在执行上下文里面的内容时候时，遇到错误执行回滚操作，类似mysql回滚函数
            with transaction.atomic():
                option = SysOptionsModel.objects.select_for_update().get(key=option_key)
                value = option.value + 1
                option.value = value
                option.save()
                mcs._del_cache(option_key)
        except SysOptionsModel.DoesNotExist:
            mcs._init_option()
            return mcs._increment(option_key)

    @classmethod
    def set_option(mcs, options):
        # 设置选项(非私有)
        for key, value in options:
            mcs._set_option(value, value)

    @classmethod
    def get_option(mcs, keys):
        # 获取选项
        result = {}
        for key in keys:
            result[key] = mcs._get_option(key)
        return result

    @property
    def website_base_url(cls):
        return cls._get_option(OptionKeys.website_base_url)

    @website_base_url.setter
    def website_base_url(cls, value):
        # 设置网站的base_url
        cls._set_option(OptionKeys.website_base_url, value)

    @property
    def website_name(cls):
        return cls._get_option(OptionKeys.website_name)

    @website_name.setter
    def website_name(cls, value):
        cls._set_option(OptionKeys.website_name, value)

    @property
    def website_name_shortcut(cls):
        return cls._get_option(OptionKeys.website_name_shortcut)

    @website_name_shortcut.setter
    def website_name_shortcut(cls, value):
        cls._set_option(OptionKeys.website_name_shortcut, value)

    @property
    def website_footer(cls):
        return cls._get_option(OptionKeys.website_footer)

    @website_footer.setter
    def website_footer(cls, value):
        cls._set_option(OptionKeys.website_footer, value)

    @property
    def allow_register(cls):
        return cls._get_option(OptionKeys.allow_register)

    @allow_register.setter
    def allow_register(cls, value):
        cls._set_option(OptionKeys.allow_register, value)

    @property
    def submission_list_show_all(cls):
        return cls._get_option(OptionKeys.submission_list_show_all)

    @submission_list_show_all.setter
    def submission_list_show_all(cls, value):
        cls._set_option(OptionKeys.submission_list_show_all, value)

    @property
    def smtp_config(cls):
        return cls._get_option(OptionKeys.smtp_config)

    @smtp_config.setter
    def smtp_config(cls, value):
        cls._set_option(OptionKeys.smtp_config, value)

    @property
    def judge_server_token(cls):
        return cls._get_option(OptionKeys.judge_server_token)

    @judge_server_token.setter
    def judge_server_token(cls, value):
        cls._set_option(OptionKeys.judge_server_token, value)

    @property
    def throttling(cls):
        return cls._get_option(OptionKeys.throttling)

    @throttling.setter
    def throttling(cls, value):
        cls._set_option(OptionKeys.throttling, value)

    @property
    def languages(cls):
        return cls._get_option(OptionKeys.languages)

    @languages.setter
    def languages(cls, value):
        cls._set_option(OptionKeys.languages, value)

    # 问题模块中的序列化器会用到下面的属性
    @property
    def spj_languages(cls):
        # spj的默认语言是和系统的默认语言有关
        # 遍历本类的语言属性，获取含有spj的item
        return [item for item in cls.languages if "spj" in item]

    @property
    def language_names(cls):
        return [item["name"] for item in languages]

    @property
    def spj_language_names(cls):
        return [item["name"] for item in cls.languages if "spj" in item]

    def reset_languages(cls):
        # 重新设置语言
        cls.languages = languages


class SysOptions(metaclass=_SysOptionsMeta):
    pass
