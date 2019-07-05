#!/usr/bin/env python
# -*-encoding:UTF-8-*-


class Choices:
    # 本类选择方法
    @classmethod
    def choices(cls):
        d = cls.__dict__
        return [d[item] for item in d.keys() if not item.startswith("__")]


class CacheKey:
    # 缓存关键字
    waiting_queue = "waiting_queue"
    contest_rank_cache = "contest_rank_cache"
    website_config = "website_config"
    option = "option"


class Difficulty(Choices):
    # 试题的难易程度
    LOW = "Low"
    MID = "Mid"
    HIGH = "High"


class ContestType:
    # 比赛类型
    PUBLIC_CONTEST = "Public"
    PASSWORD_PROTECTED_CONTEST = "Password Protected"


class ContestStatus:
    # 比赛状态
    CONTEST_UNDERWAY = "0"
    CONTEST_NOT_START = "1"
    CONTEST_ENDED = "-1"


class ContestRuleType(Choices):
    # 比赛规则类型
    ACM = "ACM"
    OI = "OI"

