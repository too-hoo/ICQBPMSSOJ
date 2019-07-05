from django.shortcuts import render
import os
from django.conf import settings
from account.serializers import ImageUploadForm
from myutils.shortcuts import rand_str
from myutils.api import CSRFExemptAPIView
import logging

logger = logging.getLogger(__name__)


class SimditorImageUploadAPIView(CSRFExemptAPIView):
    """
    图片上传
    """
    request_parsers = ()

    def post(self, request):
        """
        post方法请求上传图片
        :param request:
        :return:
        """
        form = ImageUploadForm(request.POST, request.FILES)
        # form有效，就上传成功，否则上传失败
        if form.is_valid():
            img = form.cleaned_data["image"]
        else:
            return self.response({
                "success": False,
                "msg": "Upload failed",
                "file_path": ""})

        # 截取图片的后缀，等到文件的名称
        suffix = os.path.splitext(img.name)[-1].lower()
        # 如果不是其中的类型，就返回失败信息
        if suffix not in [".gif", ".jpg", ".jpeg", ".bmp", ".png"]:
            return self.response({
                "success": False,
                "msg": "Unsupported file format",
                "file_path": ""})
        # 重新构造文件的名称
        img_name = rand_str(10) + suffix
        try:
            # 尝试往上传文件的目录里面写入该上传的图片，成功就返回成功信息，否则就返回失败信息。
            with open(os.path.join(settings.UPLOAD_DIR, img_name), "wb") as imgFile:
                for chunk in img:
                    imgFile.write(chunk)
        except IOError as e:
            logger.error(e)
            return self.response({
                "success": True,
                "msg": "Upload Error",
                "file_path": f"{settings.UPLOAD_PREFIX}/{img_name}"})
        return self.response({
            "success": True,
            "msg": "Success",
            "file_path": f"{settings.UPLOAD_PREFIX}/{img_name}"})
