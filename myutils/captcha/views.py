#!/usr/bin/env python
# -*-encoding:UTF-8-*-

from . import Captcha
from ..api import APIView
from ..shortcuts import img2base64


class CaptchaAPIView(APIView):
    """
    画出图形验证码的视图类
    """
    def get(self, request):
        return self.success(img2base64(Captcha(request).get()))
