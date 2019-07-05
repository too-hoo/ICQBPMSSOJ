#!/usr/bin/env python
# -*-encoding:UTF-8-*-

import copy
import os
import zipfile
from ipaddress import ip_network

import dateutil.parser
from django.http import FileResponse

from account.decorators import check_contest_permission, ensure_created_by
from account.models import User
from submission.models import Submission, JudgeStatus
from myutils.api import APIView, validate_serializer
from myutils.cache import cache
from myutils.constants import CacheKey
from myutils.shortcuts import rand_str
from myutils.tasks import delete_files
# 导入实体表
from ..models import Contest, ContestAnnouncement, ACMContestRank
from ..serializers import (ContestAnnouncementSerializer, ContestAdminSerializer,
                           CreateContestSerializer, CreateContestAnnouncementSerializer,
                           EditContestSerializer, EditContestAnnouncementSerializer,
                           ACMContestHelperSerializer, )


class ContestAPI(APIView):
    """
    比赛请求、比赛修改
    """
    @validate_serializer(CreateContestSerializer)
    def post(self, request):
        # 创建比赛，获得数据之后配置
        data = request.data
        data["start_time"] = dateutil.parser.parse(data["start_time"])
        data["end_time"] = dateutil.parser.parse(data["end_time"])
        data["created_by"] = request.user
        if data["end_time"] <= data["start_time"]:
            return self.error("Start time must occur earlier than end time")
        # 如果密码为空，创建的比赛就是公开的比赛
        if data.get("password") and data["password"] == "":
            data["password"] = None
        for ip_range in data["allowed_ip_ranges"]:
            try:
                # 使用ip_network判断传入的IP格式是否有效, Returns: -> An IPv4Network or IPv6Network object.
                ip_network(ip_range, strict=False)
            except ValueError:
                return self.error(f"{ip_range} is not a valid cidr network")
        # 一切满足条件，调用内部的方法创建比赛，**data 将数据分开赋值
        contest = Contest.objects.create(**data)
        # 返回经过经过序列化的比赛信息
        return self.success(ContestAdminSerializer(contest).data)

    @validate_serializer(EditContestSerializer)
    def put(self, request):
        # 修改比赛数据
        data = request.data
        try:
            # 根据传入的ID查找数据库，同时确保比赛是该用户创建的时候才能修改
            contest = Contest.objects.get(id=data.pop("id"))
            ensure_created_by(contest, request.user)
        except Contest.DoesNotExist:
            return self.error("Contest does not exist")
        # 重新配置信息
        data["start_time"] = dateutil.parser.parse(data["start_time"])
        data["end_time"] = dateutil.parser.parse(data["end_time"])
        if data["end_time"] <= data["start_time"]:
            return self.error("Start time must occur earlier than end time")
        # 传入的数据没有密码就默认比赛是公开的
        if not data["password"]:
            data["password"] = None
        # IP地址有效性检测
        for ip_range in data["allowed_ip_ranges"]:
            try:
                ip_network(ip_range, strict=False)
            except ValueError:
                return self.error(f"{ip_range} is not a valid cidr network")

        # 不需要实时比赛排名就删除缓存关键字
        if not contest.real_time_rank and data.get("real_time_rank"):
            cache_key = f"{CacheKey.contest_rank_cache}:{contest.id}"
            cache.delete(cache_key)

        # 对于每一个在data里面的键值对，将对应的属性更新到contest里面去，保存到数据库
        for k, v in data.items():
            setattr(contest, k, v)
        contest.save()
        # 成功之后返回将竞赛序列话的数据
        return self.success(ContestAdminSerializer(contest).data)

    def get(self, request):
        # 获取比赛数据
        contest_id = request.GET.get("id")
        if contest_id:
            try:
                contest = Contest.objects.get(id=contest_id)
                ensure_created_by(contest, request.user)
                return self.success(ContestAdminSerializer(contest).data)
            except Contest.DoesNotExist:
                return self.error("Contest does not exist")

        contests = Contest.objects.all().order_by("-create_time")
        if request.user.is_admin():
            contests = contests.filter(created_by=request.user)

        keyword = request.GET.get("keyword")
        if keyword:
            contests = contests.filter(title__contains=keyword)
        return self.success(self.paginate_data(request, contests, ContestAdminSerializer))


class ContestAnnouncementAPI(APIView):
    @validate_serializer(CreateContestAnnouncementSerializer)
    def post(self, request):
        """
        创建一个比赛的通知，这个是要在现有比赛的基础之上创建的
        解析传入的数据创建比赛通知，然后返回比赛通知序列化的数据
        """
        data = request.data
        try:
            # 获得比赛的ID和确保比赛是有该用户创建的
            contest = Contest.objects.get(id=data.pop("contest_id"))
            ensure_created_by(contest, request.user)
            data["contest"] = contest
            data["created_by"] = request.user
        except Contest.DoesNotExist:
            return self.error("Contest does not exist")
        announcement = ContestAnnouncement.objects.create(**data)
        return self.success(ContestAnnouncementSerializer(announcement).data)

    @validate_serializer(EditContestAnnouncementSerializer)
    def put(self, request):
        """
        更新比赛通知
        """
        data = request.data
        try:
            contest_announcement = ContestAnnouncement.objects.get(id=data.pop("id"))
            ensure_created_by(contest_announcement, request.user)
        except ContestAnnouncement.DoesNotExist:
            return self.error("Contest announcement does not exist")
        # 遍历每一对键值对然后更新数据到数据库
        for k, v in data.items():
            setattr(contest_announcement, k, v)
        contest_announcement.save()
        return self.success()

    def delete(self, request):
        """
        更具id删除比赛通知
        """
        contest_announcement_id = request.GET.get("id")
        if contest_announcement_id:
            if request.user.is_admin():
                ContestAnnouncement.objects.filter(id=contest_announcement_id,
                                                   contest__created_by=request.user).delete()
            else:
                ContestAnnouncement.objects.filter(id=contest_announcement_id).delete()
        return self.success()

    def get(self, request):
        """
        获得单个比赛通知或者比赛通知列表
        """
        contest_announcement_id = request.GET.get("id")
        if contest_announcement_id:
            try:
                contest_announcement = ContestAnnouncement.objects.get(id=contest_announcement_id)
                ensure_created_by(contest_announcement, request.user)
                # 返回比赛通知的序列化信息，单挑，根据创建的ID，直接查找到指定的比赛通知信息
                return self.success(ContestAnnouncementSerializer(contest_announcement).data)
            except ContestAnnouncement.DoesNotExist:
                return self.error("Contest announcement does not exist")

        contest_id = request.GET.get("contest_id")
        if not contest_id:
            return self.error("Parameter error")
        # 根据传入的比赛ID号查找到对应的用户，根据用户将其发表的所用比赛通知查出返回
        contest_announcements = ContestAnnouncement.objects.filter(contest_id=contest_id)
        if request.user.is_admin():
            contest_announcements = contest_announcements.filter(created_by=request.user)
        keyword = request.GET.get("keyword")
        if keyword:
            contest_announcements = contest_announcements.filter(title__contains=keyword)
        # many=True,说明是反悔一个列表
        return self.success(ContestAnnouncementSerializer(contest_announcements, many=True).data)


class ACMContestHelper(APIView):
    @check_contest_permission(check_type="ranks")
    def get(self, request):
        ranks = ACMContestRank.objects.filter(contest=self.contest, accepted_number__gt=0) \
            .values("id", "user__username", "user__userprofile__real_name", "submission_info")
        results = []
        for rank in ranks:
            for problem_id, info in rank["submission_info"].items():
                if info["is_ac"]:
                    results.append({
                        "id": rank["id"],
                        "username": rank["user__username"],
                        "real_name": rank["user__userprofile__real_name"],
                        "problem_id": problem_id,
                        "ac_info": info,
                        "checked": info.get("checked", False)
                    })
        results.sort(key=lambda x: -x["ac_info"]["ac_time"])
        return self.success(results)

    @check_contest_permission(check_type="ranks")
    @validate_serializer(ACMContestHelperSerializer)
    def put(self, request):
        data = request.data
        try:
            rank = ACMContestRank.objects.get(pk=data["rank_id"])
        except ACMContestRank.DoesNotExist:
            return self.error("Rank id does not exist")
        problem_rank_status = rank.submission_info.get(data["problem_id"])
        if not problem_rank_status:
            return self.error("Problem id does not exist")
        problem_rank_status["checked"] = data["checked"]
        rank.save(update_fields=("submission_info",))
        return self.success()


class DownloadContestSubmissions(APIView):
    def _dump_submissions(self, contest, exclude_admin=True):
        problem_ids = contest.problem_set.all().values_list("id", "_id")
        id2display_id = {k[0]: k[1] for k in problem_ids}
        ac_map = {k[0]: False for k in problem_ids}
        submissions = Submission.objects.filter(contest=contest, result=JudgeStatus.ACCEPTED).order_by("-create_time")
        user_ids = submissions.values_list("user_id", flat=True)
        users = User.objects.filter(id__in=user_ids)
        path = f"/tmp/{rand_str()}.zip"
        with zipfile.ZipFile(path, "w") as zip_file:
            for user in users:
                if user.is_admin_role() and exclude_admin:
                    continue
                user_ac_map = copy.deepcopy(ac_map)
                user_submissions = submissions.filter(user_id=user.id)
                for submission in user_submissions:
                    problem_id = submission.problem_id
                    if user_ac_map[problem_id]:
                        continue
                    file_name = f"{user.username}_{id2display_id[submission.problem_id]}.txt"
                    compression = zipfile.ZIP_DEFLATED
                    zip_file.writestr(zinfo_or_arcname=f"{file_name}",
                                      data=submission.code,
                                      compress_type=compression)
                    user_ac_map[problem_id] = True
        return path

    def get(self, request):
        contest_id = request.GET.get("contest_id")
        if not contest_id:
            return self.error("Parameter error")
        try:
            contest = Contest.objects.get(id=contest_id)
            ensure_created_by(contest, request.user)
        except Contest.DoesNotExist:
            return self.error("Contest does not exist")

        exclude_admin = request.GET.get("exclude_admin") == "1"
        zip_path = self._dump_submissions(contest, exclude_admin)
        delete_files.apply_async((zip_path,), countdown=300)
        resp = FileResponse(open(zip_path, "rb"))
        resp["Content-Type"] = "application/zip"
        resp["Content-Disposition"] = f"attachment;filename={os.path.basename(zip_path)}"
        return resp
