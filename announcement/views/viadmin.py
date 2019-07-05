from django.shortcuts import render

from account.decorators import super_admin_required
from myutils.api import APIView, validate_serializer

from announcement.models import Announcement
from announcement.serializers import AnnouncementSerializer, CreateAnnouncementSerializer, EditAnnouncementSerializer


class AnnouncementAdminAPI(APIView):
    @validate_serializer(CreateAnnouncementSerializer)
    @super_admin_required
    def post(self, request):
        """
        发布通知信息，增加
        :param request: 请求
        :return: 返回序列化数据
        """
        data = request.data
        announcement = Announcement.objects.create(title=data["title"],
                                                   content=data["content"],
                                                   created_by=request.user,
                                                   visible=data["visible"],
                                                   )
        return self.success(AnnouncementSerializer(announcement).data)

    @super_admin_required
    def delete(self, request):
        # 根据请求传入的id，将通知删除掉，删除数据
        if request.GET.get("id"):
            Announcement.objects.filter(id=request.GET["id"]).delete()
        return self.success()

    @super_admin_required
    def get(self, request):
        """
        获取announcement list 或者 get one announcement，获取数据
        :param request: 请求
        :return: 序列化数据
        """
        announcement_id = request.GET.get("id")
        if announcement_id:
            try:
                announcement = Announcement.objects.get(id=announcement_id)
                return self.success(AnnouncementSerializer(announcement).data)
            except Announcement.DoesNotExist:
                return self.error("Announcement does not exist")
        # 根据创建的时间将通知查询出来，使用条件查询，将可见的通知分页显示
        announcement = Announcement.objects.all().order_by("-create_time")
        if request.GET.get("visible") == "true":
            announcement = announcement.filter(visible=True)
        return self.success(self.paginate_data(request, announcement, AnnouncementSerializer))

    @validate_serializer(EditAnnouncementSerializer)
    @super_admin_required
    def put(self, request):
        """
        编辑通知，修改数据
        :param request:
        :return:
        """
        data = request.data
        try:
            announcement = Announcement.objects.get(id=data.pop("id"))
        except Announcement.DoesNotExist:
            return self.error("Announcement does not exist")

        for k, v in data.items():
            setattr(announcement, k, v)
        announcement.save()

        return self.success(AnnouncementSerializer(announcement).data)
