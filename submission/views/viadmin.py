#!/usr/bin/env python
# -*-encoding:UTF-8-*-

from account.decorators import super_admin_required
from judge.tasks import judge_task
# from judge.dispatcher import JudgeDispatcher
from myutils.api import APIView
from ..models import Submission


class SubmissionRejudgeAPI(APIView):
    # 管理员， 提交信息重新评判的接口
    @super_admin_required
    def get(self, request):
        id = request.GET.get("id")
        # 获取重新评测的提交信息ID
        if not id:
            return self.error("Parameter error, id is required")
        try:
            submission = Submission.objects.select_related("problem").get(id=id, contest_id__isnull=True)
        except Submission.DoesNotExist:
            return self.error("Submission does not exists")
        submission.statistic_info = {}
        submission.save()

        judge_task.delay(submission.id, submission.problem.id)
        return self.success()
