#!/usr/bin/env python
# -*-encoding:UTF-8-*-

from __future__ import absolute_import, unicode_literals
from celery import shared_task


from account.models import User
from submission.models import Submission
from judge.dispatcher import JudgeDispatcher


# celery 发现任务之后会执行
@shared_task
def judge_task(submissiom_id, problem_id):
    uid = Submission.objects.get(id=submissiom_id).user_id
    if User.objects.get(id=uid).is_disabled:
        return
    # 在判定用户有效之后，JudgeDispatcher会将问题提交的ID和问题ID提交给评判机
    JudgeDispatcher(submissiom_id, problem_id).judge()
