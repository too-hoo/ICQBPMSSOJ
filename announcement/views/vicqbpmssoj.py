#!/usr/bin/env python
# -*-encoding:UTF-8-*-

from myutils.api import APIView
from announcement.models import Announcement
from announcement.serializers import AnnouncementSerializer


class AnnouncementAPI(APIView):
    """
    对于普通的用户来说，只能查看能够被看得见的信息
    """
    def get(self, request):
        announcements = Announcement.objects.filter(visible=True)
        return self.success(self.paginate_data(request, announcements, AnnouncementSerializer))
