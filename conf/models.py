from django.db import models

from django.utils import timezone
# Create your models here.


class JudgeServer(models.Model):
    # 评判服务器返回的字段属性对应的数据库表
    hostname = models.TextField()
    ip = models.TextField(null=True)
    judger_version = models.TextField()
    cpu_core = models.IntegerField()
    memory_usage = models.FloatField()
    cpu_usage = models.FloatField()
    last_heartbeat = models.DateTimeField()
    create_time = models.DateTimeField(auto_now_add=True)
    task_number = models.IntegerField(default=0)
    service_url = models.TextField(null=True)
    is_disabled = models.BooleanField(default=False)

    @property
    def status(self):
        # 可以看做是Server的属性用于返回
        # 这里增加一秒延时，提高对网络环境的适应性,之前设置last_heartbeat的时间为5秒响应一次
        if (timezone.now() - self.last_heartbeat).total_seconds() > 6:
            return "abnormal"
        return "normal"

    class Meta:
        db_table = "judge_server"
