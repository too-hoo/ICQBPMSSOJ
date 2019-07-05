#!/usr/bin/env python
# -*-encoding:UTF-8-*-

from django.core.management.base import BaseCommand

from account.models import AdminType, ProblemPermission, User, UserProfile
from myutils.shortcuts import rand_str  # NOQA


class Command(BaseCommand):
    """
    基础的命令行解析，此工具类用来管理系统，例如使用命令来创建超级用户
    python manage.py inituser --username=root --password=root123 --action=create_super_admin
    """
    def add_arguments(self, parser):
        """
        添加参数：username、password、action
        :param parser:
        :return:
        """
        parser.add_argument("--username", type=str)
        parser.add_argument("--password", type=str)
        parser.add_argument("--action", type=str)

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]
        action = options["action"]

        # 如果不满足条件，标准输出流里面会写入错误信息
        if not(username and password and action):
            self.stdout.write(self.style.ERROR("Invalid args"))
            exit(1)

        if action == "create_super_admin":
            # 如果对应的超级用户存在，那么操作会被忽略
            if User.objects.filter(id=1).exists():
                self.stdout.write(self.style.SUCCESS(f"User {username} exists, operation ignored"))
                exit()

            # 否则就创建对应的用户
            user = User.objects.create(username=username, admin_type=AdminType.SUPER_ADMIN,
                                       problem_permission=ProblemPermission.ALL)
            user.set_password(password)
            user.save()
            UserProfile.objects.create(user=user)

            self.stdout.write(self.style.SUCCESS("User created"))
        elif action == "reset":
            try:
                # 用户存在就可以成功设置密码，否则输出错误信息并退出。
                user = User.objects.get(username=username)
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Password is rested"))
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User {username} doesnot exist, operation ignored"))
                exit(1)
        else:
            raise ValueError("Invalid action")
