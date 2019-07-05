#!/usr/bin/env python
# -*-encoding:UTF-8-*-

import os
import re
import datetime
import random
from base64 import b64encode
from io import BytesIO
from django.utils.crypto import get_random_string
from envelopes import Envelope


def rand_str(length=32,type="lower_hex"):
    """
    本方法生成指定长度的随机字符串或者数字，可以使用在秘钥等安全场景
    :param length: 字符串或者数字的长度
    :param type: str 代表随机字符串，num代表随机数字
    :return: 字符串
    """
    if type == "str":
        return get_random_string(length, allowed_chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
    elif type == "lower_str":
        return get_random_string(length, allowed_chars="abcdefghijklmnopqrstuvwxyz0123456789")
    elif type == "lower_hex":
        return random.choice("123456789abcdef") + get_random_string(length-1, allowed_chars="0123456789abcdef")
    else:
        return random.choice("123456789") + get_random_string(length-1, allowed_chars="0123456789")


def build_query_string(kv_data,ignore_none=True):
    # {"a":1,"b":"test"} -> "?a=1&b=test"
    # 构建查询字符串
    query_string = ""
    for k, v in kv_data.items():
        # 如果不满足查询条件，就跳过本次循环
        if ignore_none is True and kv_data[k] is None:
            continue
        if query_string != "":
            query_string += "&"
        else:
            query_string = "?"
        # 将字符串拼接在一起，最后返回
        query_string += (k + "=" + str(v))
    return query_string


def img2base64(img):
    """
    基于64bit的图片格式
    :param img:
    :return: 字符串
    """
    with BytesIO() as buf:
        img.save(buf, "gif")
        buf_str = buf.getvalue()
    # 设置前缀
    img_prefix = "data:image/png;base64,"
    b64_str = img_prefix + b64encode(buf_str).decode("utf-8")
    return b64_str


def datetime2str(value, format="iso-8601"):
    """
    返回日期时间字符串
    :param value:
    :param format:
    :return: 指定格式的时间字符串
    """
    if format.lower() == "iso-8601":
        value = value.isoformat()
        if value.endswith("+00:00"):
            value = value[:-6] + "Z"
        return value
    return value.strftime(format)


def timestamp2utcstr(value):
    """
    时区邮戳
    :param value:
    :return:
    """
    return datetime.datetime.utcfromtimestamp(value).isoformat()


def natural_sort_key(s, _nsre=re.compile(r"(\d+)")):
    """
    自然排列关键字
    对于每个text在re.split(_nsre, s),如果是数字就返回，否则将字母变成小写返回
    :param s:
    :param _nsre:
    :return:
    """
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(_nsre, s)]


def send_email(smtp_config, from_name, to_email, to_name, subject, content):
    """
    注册账号邮箱验证，
    :param smtp_config: 邮件配置
    :param from_name: 来自名称
    :param to_email: 目标邮件名
    :param to_name: 收件方
    :param subject: 主题
    :param content: 内容
    :return: 返回电子邮件的发送参数
    """
    envelope = Envelope(from_addr=(smtp_config["email"], from_name),
                        to_addr=(to_email,to_name),
                        subject=subject,
                        html_body=content)
    return envelope.send(smtp_config["server"],
                         login=smtp_config["email"],
                         password=smtp_config["password"],
                         port=smtp_config["port"],
                         tls=smtp_config["tls"])


def get_env(name, default=""):
    """
    获取系统的环境参数：例如redis的主机名和端口等
    :param name:
    :param default:
    :return: 返回获取到的系统环境
    """
    return os.environ.get(name, default)























