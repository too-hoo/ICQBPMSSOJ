#!/usr/bin/env python
# -*-encoding:UTF-8-*-
from django.conf.urls import url
from ..views.vicqbpmssoj import AnnouncementAPI

urlpatterns = [
    url(r"^announcement/?$", AnnouncementAPI.as_view(), name="announcement_api"),
]