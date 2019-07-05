#!/usr/bin/env python
# -*-encoding:UTF-8-*-
# 设置#noqa的意思：导入的这连个文件可能在这里没有用到，但是在其他的类里面会用到，让你不要报错
from django.core.cache import cache, caches     #noqa
from django.conf import settings                #noqa

from django_redis.client.default import DefaultClient
from django_redis.cache import RedisCache
# 本工具类使用的是redis作为缓存，快而且可以存放起来，虽然比内存的慢一点，但是可以存放起来啊
# 由MyRedisCache调用


class MyRedisClient(DefaultClient):
    def __getattr__(self, item):
        client = self.get_client(write=True)
        return getattr(client,item)

    # django-redis 有限制的支持一些 Redis 原子操作, 例如 SETNX 和 INCR 命令.
    # Redis Incr 命令将 key 中储存的数字值增一，将插入到队列里面的数据逐个增加
    def redis_incr(self,key,count=1):
        """
        django 默认的incr 在key不存在的时候会抛出异常
        :param key: 传入的关键字
        :param count: 计数
        :return: 客户端递增计数
        """
        client = self.get_client(write=True)
        return client.incr(key,count)


class MyRedisCache(RedisCache):
    # 自定义redis的缓存类
    def __init__(self,server,params):
        super().__init__(server,params)  # 继承超类
        self._client_cls = MyRedisClient  # 调用客户端

    def __getattr__(self, item):
        return getattr(self.client,item)
