#!/usr/bin/env python
# -*-encoding:UTF-8-*-

import os
from celery import shared_task


@shared_task
def delete_files(*args):
    # 删除文件
    for item in args:
        try:
            os.remove(item)
        except Exception:
            pass
