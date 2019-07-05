from django.contrib.postgres.fields import JSONField  #NOQA
from django.db import models

# Create your models here.
from myutils.xss_filter import XSSHtml


class RichTextField(models.TextField):
    # 富文本编辑器字段实体类
    def get_prep_value(self, value):
        with XSSHtml() as parser:
            return parser.clean(value or "")
