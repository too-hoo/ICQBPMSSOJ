#!/usr/bin/env python
# -*-encoding:UTF-8-*-

# flake8:noqa
# 数据迁移（re）

import os
import sys
import re
import json
import django
import hashlib
from json.decoder import JSONDecodeError

# 系统路径设置为ICQBPMSSOJ
sys.path.append("../")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ICQBPMSSOJ.settings")
django.setup()
from django.conf import settings
from account.models import User, UserProfile, AdminType, ProblemPermission
from problem.models import Problem, ProblemTag, ProblemDifficulty, ProblemRuleType


admin_type_map = {
    0: AdminType.REGULAR_USER,
    1: AdminType.ADMIN,
    2: AdminType.SUPER_ADMIN
}
languages_map = {
    1: "C",
    2: "C++",
    3: "Java"
}

# 邮箱注册
email_regex = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")

# pk -> name 主键是name
tags = {}
# pk -> user obj  主键是user
users = {}

problems = []


def get_input_result():
    # 获取输入结果，被下面的函数调用，可重用函数
    while True:
        resp = input()
        if resp not in ["yes", "no"]:
            print("Please input yes or no")
            continue
        # 这个返回1或者0
        return resp == "yes"


def set_problem_display_id_prefix():
    # 设置问题显示的id前缀
    while True:
        print("Please input a prefix which will be used in all the imported problem's displayID")
        print(
            "For example, if your input is 'old'(no quote), the problems' display id will be old1, old2, old3..\ninput:",
            end="")
        resp = input()
        if resp.strip():
            return resp.strip()
        else:
            print("Empty prefix detected, sure to do that? (yes/no)")
            if get_input_result():
                return ""


def get_stripped_output_md5(test_case_id, output_name):
    # 根据传入的测试样例ID和输出的文件名称，获得去掉空格后输出的md5
    # 被下面的get_test_case_score调用
    output_path = os.path.join(settings.TEST_CASE_DIR, test_case_id, output_name)
    with open(output_path, 'r') as f:
        return hashlib.md5(f.read().rstrip().encode('utf-8')).hexdigest()


def get_test_case_score(test_case_id):
    # 根据测试样例的ID获得测试样例的成绩
    info_path = os.path.join(settings.TEST_CASE_DIR, test_case_id, "info")
    # 如果不存在info文件，返回空列表，否则就加载info文件
    if not os.path.exists(info_path):
        return []
    with open(info_path, "r") as info_file:
        info = json.load(info_file)
    test_case_score = []
    need_rewrite = True
    # 读取info文件里面的额test_case对应的md5值
    for test_case in info["test_cases"].values():
        if test_case.__contains__("stripped_output_md5"):
            need_rewrite = False
        elif test_case.__contains__("striped_output_md5"):
            test_case["stripped_output_md5"] = test_case.pop("striped_output_md5")
        else:
            test_case["stripped_output_md5"] = get_stripped_output_md5(test_case_id, test_case["output_name"])
        test_case_score.append({"input_name": test_case["input_name"],
                                "output_name": test_case.get("output_name", "-"),
                                "score": 0})

    # 如果需要重新写为真，就将信息重新写到文件里面去
    if need_rewrite:
        with open(info_path, "w") as f:
            f.write(json.dumps(info))
    return test_case_score


def import_users():
    # 导入用户
    i = 0
    print("Find %d users in old data." % len(users.keys()))
    print("import users now? (yes/no)")
    # 返回1就导入用户，否则就直接退出了
    if get_input_result():
        # 遍历users里面的每一个值
        for data in users.values():
            # 如果邮箱格式不匹配，就跳过本重循环
            if not email_regex.match(data["email"]):
                print("%s will not be created due to invalid email: %s" % (data["username"], data["email"]))
                continue
            # 将值降为小写，然后查询数据库
            data["username"] = data["username"].lower()
            user, created = User.objects.get_or_create(username=data["username"])
            # 如果created = 0，说明该用户名已经存在，跳过本次循环
            if not created:
                print("%s already exists, omitted" % user.username)
                continue
            # 否则的话，设置用户各个字段值
            user.password = data["password"]
            user.email = data["email"]
            admin_type = admin_type_map[data["admin_type"]]
            user.admin_type = admin_type
            # 设置用户的等级
            if admin_type == AdminType.ADMIN:
                user.problem_permission = ProblemPermission.OWN
            elif admin_type == AdminType.SUPER_ADMIN:
                user.problem_permission = ProblemPermission.ALL
            # 保存用户数据
            user.save()
            # 相应的UserProfile表格也要插入相应的数据
            UserProfile.objects.create(user=user, real_name=data["real_name"])
            # 计数器加1
            i += 1
            print("%s imported successfully" % user.username)
        print("%d users have successfully imported\n" % i)


def import_tags():
    # 导入标签
    i = 0
    print("\nFind these tags in old data:")
    print(", ".join(tags.values()), '\n')
    print("import tags now? (yes/no)")
    if get_input_result():
        for tagname in tags.values():
            # 有就不导入，没有就到入
            tag, created = ProblemTag.objects.get_or_create(name=tagname)
            if not created:
                print("%s already exists, omitted" % tagname)
            else:
                print("%s tag created successfully" % tagname)
                i += 1
        print("%d tags have successfully imported\n" % i)
    else:
        print("Problem depends on problem_tags and users, exit..")
        exit(1)


def import_problems():
    # 到入问题
    i = 0
    print("\nFind %d problems in old data" % len(problems))
    # 获取问题的前缀标识
    prefix = set_problem_display_id_prefix()
    print("import problems using prefix: %s? (yes/no)" % prefix)
    if get_input_result():
        default_creator = User.objects.first()
        for data in problems:
            data["_id"] = prefix + str(data.pop("id"))
            # 查询数据库，如果问题存在就跳过本问题，继续进行其他的问题导入
            if Problem.objects.filter(_id=data["_id"]).exists():
                print("%s has the same display_id with the db problem" % data["title"])
                continue
            try:
                # 检查导入问题的原始作者在数据库里面是否存在，不存在的话就设置导入问题的ID到数据库作为新的用户ID
                creator_id = \
                    User.objects.filter(username=users[data["created_by"]]["username"]).values_list("id", flat=True)[0]
            except (User.DoesNotExist, IndexError):
                print("The origin creator does not exist, set it to default_creator")
                creator_id = default_creator.id
            # 设置导入问题的各个属性
            data["created_by_id"] = creator_id
            data.pop("created_by")
            data["difficulty"] = ProblemDifficulty.Mid
            # 特殊评语言判非空，就设置对应的语言
            if data["spj_language"]:
                data["spj_language"] = languages_map[data["spj_language"]]
            data["samples"] = json.loads(data["samples"])
            data["languages"] = ["C", "C++"]
            test_case_score = get_test_case_score(data["test_case_id"])
            if not test_case_score:
                print("%s test_case files don't exist, omitted" % data["title"])
                continue
            data["test_case_score"] = test_case_score
            data["rule_type"] = ProblemRuleType.ACM
            data["template"] = {}
            data.pop("total_submit_number")
            data.pop("total_accepted_number")
            tag_ids = data.pop("tags")
            # 使用**，将json数据转换成等式样式
            problem = Problem.objects.create(**data)
            problem.create_time = data["create_time"]
            # 保存问题
            problem.save()
            # 设置问题的标签
            for tag_id in tag_ids:
                tag, _ = ProblemTag.objects.get_or_create(name=tags[tag_id])
                problem.tags.add(tag)
            i += 1
            print("%s imported successfully" % data["title"])
    print("%d problems have successfully imported" % i)


if __name__ == "__main__":
    # 系统参数值的长度等于1，正常退出
    if len(sys.argv) == 1:
        print("Usage: python3 %s [old_data_path]" % sys.argv[0])
        exit(0)
    # 否者就将第一个参数的值赋值给data_path
    data_path = sys.argv[1]
    # 判断对应路径下面的文件是否存在
    if not os.path.isfile(data_path):
        print("Data file does not exist")
        exit(1)

    try:
        # 使用json加载数据
        with open(data_path, "r") as data_file:
            old_data = json.load(data_file)
    except JSONDecodeError:
        print("Data file format error, ensure it's a valid json file!")
        exit(1)
    print("Read old data successfully.\n")

    # 主要导入的数据有问题标签、用户、问题，根据不同的情况进行到诶设置，最后调用函数进行导入
    for obj in old_data:
        if obj["model"] == "problem.problemtag":
            tags[obj["pk"]] = obj["fields"]["name"]
        elif obj["model"] == "account.user":
            users[obj["pk"]] = obj["fields"]
        elif obj["model"] == "problem.problem":
            obj["fields"]["id"] = obj["pk"]
            problems.append(obj["fields"])
    import_users()
    import_tags()
    import_problems()
