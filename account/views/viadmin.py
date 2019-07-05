#!/usr/bin/env python
# -*-encoding:UTF-8-*-

import os
import re
import xlsxwriter

from django.db import transaction, IntegrityError
from django.db.models import Q
from django.http import HttpResponse
from django.contrib.auth.hashers import make_password

from submission.models import Submission
from myutils.api import APIView, validate_serializer
from myutils.shortcuts import rand_str

from ..decorators import super_admin_required
from ..models import AdminType, ProblemPermission, User, UserProfile
from ..serializers import EditUserSerializer, UserAdminSerializer, GenerateUserSerializer
from ..serializers import ImportUserSerializer


class UserAdminAPI(APIView):
    @validate_serializer(ImportUserSerializer)
    @super_admin_required
    def post(self, request):
        """
        导入用户数据
        """
        data = request.data["users"]

        user_list = []
        for user_data in data:
            # 字段不是3个， 第一个用户名字段大小超过32
            if len(user_data) != 3 or len(user_data[0]) > 32:
                return self.error(f"Error occurred while processing data '{user_data}'")
            user_list.append(User(username=user_data[0], password=make_password(user_data[1]), email=user_data[2]))

        try:
            # 原子操作，出错回滚
            with transaction.atomic():
                ret = User.objects.bulk_create(user_list)
                UserProfile.objects.bulk_create([UserProfile(user=user) for user in ret])
            return self.success()
        except IntegrityError as e:
            # Extract detail from exception message
            #    duplicate key value violates unique constraint "user_username_key"
            #    DETAIL:  Key (username)=(root11) already exists.       <- return this line
            return self.error(str(e).split("\n")[1])

    @validate_serializer(EditUserSerializer)
    @super_admin_required
    def put(self, request):
        """
        编辑用户的接口api：
        这里根据用户提交的数据，将数据设置保存到数据库
        """
        # 根据用户请求数据中的ID，查找数据库，看是否存在这样的用户（这里必须传入用户的ID作为唯一的标识）
        data = request.data
        try:
            user = User.objects.get(id=data["id"])
        except User.DoesNotExist:
            return self.error("User does not exist")
        # 将用户名和邮箱的字母转化成小写然后再判断，大小写不区分
        if User.objects.filter(username=data["username"].lower()).exclude(id=user.id).exists():
            return self.error("Username already exists")
        if User.objects.filter(email=data["email"].lower()).exclude(id=user.id).exists():
            return self.error("Email already exists")

        # 根据传入的数据进行赋值，注意这里的username要先保存起来备用
        pre_username = user.username
        user.username = data["username"].lower()
        user.email = data["email"].lower()
        user.admin_type = data["admin_type"]
        user.is_disabled = data["is_disabled"]

        # 普通管理员和超级管理员判断
        if data["admin_type"] == AdminType.ADMIN:
            user.problem_permission = data["problem_permission"]
        elif data["admin_type"] == AdminType.SUPER_ADMIN:
            user.problem_permission = ProblemPermission.ALL
        else:
            user.problem_permission = ProblemPermission.NONE

        if data["password"]:
            user.set_password(data["password"])

        # 如果开放api，就是data["open_api"]为True
        if data["open_api"]:
            # 保存更改之后避免重置用户的appkey，open_api是boolean
            if not user.open_api:
                user.open_api_appkey = rand_str()
        else:
            user.open_api_appkey = None
        user.open_api = data["open_api"]

        # 如果需要双因素验证
        # data["two_factor_auth"]为True时候就设置tfa_token
        if data["two_factor_auth"]:
            # 保存更改之后避免重置用户的tfa_token
            # 这里注意:是数据库中的用户two_factor_auth,而不是data的two_factor_auth,数据库中的默认是false
            if not user.two_factor_auth:
                user.tfa_token = rand_str()
        else:
            user.tfa_token = None
        user.two_factor_auth = data["two_factor_auth"]

        user.save()
        # 如果之前的用户名字和新的用户名字不同，更新提交信息里面的用户名
        if pre_username != user.username:
            Submission.objects.filter(username=pre_username).update(username=user.username)

        # 用户信息表根据对应的用户，将和User表中相同的字段：real_name也更新
        UserProfile.objects.filter(user=user).update(real_name=data["real_name"])
        return self.success(UserAdminSerializer(user).data)

    @super_admin_required
    def get(self, request):
        """
        User list api / Get user by id
        """
        user_id = request.GET.get("id")
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return self.error("User does not exist")
            return self.success(UserAdminSerializer(user).data)

        user = User.objects.all().order_by("-create_time")

        keyword = request.GET.get("keyword", None)
        if keyword:
            user = user.filter(Q(username__icontains=keyword) |
                               Q(userprofile__real_name__icontains=keyword) |
                               Q(email__icontains=keyword))
        return self.success(self.paginate_data(request, user, UserAdminSerializer))

    # 被delete方法调用
    def delete_one(self, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return f"User {user_id} does not exist"
        if Submission.objects.filter(user_id=user_id).exists():
            return f"Can't delete the user {user_id} as he/she has submissions"
        user.delete()

    @super_admin_required
    def delete(self, request):
        # 获取请求传送过来的id，使用“，”进行分割，然后逐个删除
        id = request.GET.get("id")
        if not id:
            return self.error("Invalid Parameter, id is required")
        for user_id in id.split(","):
            if user_id:
                error = self.delete_one(user_id)
                if error:
                    return self.error(error)
        return self.success()


class GenerateUserAPI(APIView):
    @super_admin_required
    def get(self, request):
        """
        download users excel
        """
        file_id = request.GET.get("file_id")
        if not file_id:
            return self.error("Invalid Parameter, file_id is required")
        if not re.match(r"^[a-zA-Z0-9]+$", file_id):
            return self.error("Illegal file_id")
        file_path = f"/tmp/{file_id}.xlsx"
        if not os.path.isfile(file_path):
            return self.error("File does not exist")
        with open(file_path, "rb") as f:
            raw_data = f.read()
        os.remove(file_path)
        response = HttpResponse(raw_data)
        response["Content-Disposition"] = f"attachment; filename=users.xlsx"
        response["Content-Type"] = "application/xlsx"
        return response

    @validate_serializer(GenerateUserSerializer)
    @super_admin_required
    def post(self, request):
        """
        产生用户
        """
        data = request.data
        # 设置数字的最大长度100-105
        number_max_length = max(len(str(data["number_from"])), len(str(data["number_to"])))
        # 用户名字长度不应该大于32个字符
        if number_max_length + len(data["prefix"]) + len(data["suffix"]) > 32:
            return self.error("Username should not more than 32 characters")
        if data["number_from"] > data["number_to"]:
            return self.error("Start number must be lower than end number")

        # 文件名字ID使用随机生成的8个字符
        file_id = rand_str(8)
        filename = f"/tmp/{file_id}.xlsx"
        # 创建工作簿
        workbook = xlsxwriter.Workbook(filename)
        # 工作簿中添加页
        worksheet = workbook.add_worksheet()
        # 每一页设置29列A：B，A1和B1分别保存用户名和密码
        worksheet.set_column("A:B", 20)
        worksheet.write("A1", "Username")
        worksheet.write("B1", "Password")
        i = 1

        # 先初始化用户列表
        user_list = []
        # 假设每次创建from100个和to105个，用户名为prenumbersuf，每创建一个用户user，都添加到user_list里面去，
        # 原值密码生成之后，使用内置方法make_password保存到生成的每一个用户里面去
        for number in range(data["number_from"], data["number_to"] + 1):
            raw_password = rand_str(data["password_length"])
            user = User(username=f"{data['prefix']}{number}{data['suffix']}", password=make_password(raw_password))
            user.raw_password = raw_password
            user_list.append(user)

        try:
            with transaction.atomic():
                # 使用原子操作，将数据同一插入到数据库里面去，同事同步User和UserProfile这两张表，
                # 同事将数据写入到工作簿的页里面去，最后返回该工作页文件的ID
                ret = User.objects.bulk_create(user_list)
                UserProfile.objects.bulk_create([UserProfile(user=user) for user in ret])
                for item in user_list:
                    worksheet.write_string(i, 0, item.username)
                    worksheet.write_string(i, 1, item.raw_password)
                    i += 1
                workbook.close()
                return self.success({"file_id": file_id})
        except IntegrityError as e:
            # Extract detail from exception message
            #    duplicate key value violates unique constraint "user_username_key"
            #    DETAIL:  Key (username)=(root11) already exists.      <- this line
            return self.error(str(e).split("\n")[1])
