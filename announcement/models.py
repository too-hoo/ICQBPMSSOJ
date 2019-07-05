from django.db import models

from account.models import User
from myutils.models import RichTextField

# Create your models here.


class Announcement(models.Model):
    title = models.TextField()
    # HTML
    content = RichTextField()
    create_time = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User)
    # 最新更新的时间自然是现在的时间
    last_update_time = models.DateTimeField(auto_now = True)
    visible = models.BooleanField(default=True)

    class Meta:
        db_table = "announcement"
        # 按照创建时间先后排序
        ordering = ("-create_time",)
