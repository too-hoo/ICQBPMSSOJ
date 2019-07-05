from django.db import models
from myutils.models import JSONField

# Create your models here.


class SysOptions(models.Model):
    # 系统选项对应的类
    # 系统的选项就是一些键值对：一个键对应一个值
    key = models.TextField(unique=True, db_index=True)
    value = JSONField()
