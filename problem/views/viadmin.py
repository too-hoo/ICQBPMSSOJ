#!/usr/bin/env python
# -*-encoding:UTF-8-*-
import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from wsgiref.util import FileWrapper

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.http import StreamingHttpResponse, FileResponse

from account.decorators import problem_permission_required, ensure_created_by
from contest.models import Contest, ContestStatus
from fps.parser import FPSHelper, FPSParser
from judge.dispatcher import SPJCompiler
from options.options import SysOptions
from submission.models import Submission, JudgeStatus
from myutils.api import APIView, CSRFExemptAPIView, validate_serializer, APIError
from myutils.constants import Difficulty
from myutils.shortcuts import rand_str, natural_sort_key
from myutils.tasks import delete_files
from ..models import Problem, ProblemRuleType, ProblemTag
from ..serializers import (CreateContestProblemSerializer, CompileSPJSerializer,
                           CreateProblemSerializer, EditProblemSerializer, EditContestProblemSerializer,
                           ProblemAdminSerializer, TestCaseUploadForm, ContestProblemMakePublicSerializer,
                           AddContestProblemSerializer, ExportProblemSerializer,
                           ExportProblemRequestSerialzier, UploadProblemForm, ImportProblemSerializer,
                           FPSProblemSerializer)
from ..utils import TEMPLATE_BASE, build_problem_template


class TestCaseZipProcessor(object):
    # 测试案例压缩解析，
    def process_zip(self, uploaded_zip_file, spj, dir=""):
        """
        这个方法被TestCaseAPI的post调用，用户解析用户上传传过来的zip文件
        :param uploaded_zip_file: 用户上传的zip文件
        :param spj: 特殊评判
        :param dir: 默认为空
        :return:
        """
        try:
            # 以读的方式打开压缩文件，不能打开就报错
            zip_file = zipfile.ZipFile(uploaded_zip_file, "r")
        except zipfile.BadZipFile:
            raise APIError("Bad zip file")
        # 获得压缩文件的名字列表，["1.in", "1.out", "2.in", ".DS_Store"]
        name_list = zip_file.namelist()
        # 调用filter_name_list函数过滤测试用例，过滤之后为的test_case_list为["1.in", "2.in"]->这里以特殊评判为例,如果为空就报错
        # 如果是非特殊评判的就是：过滤之后为的test_case_list为["1.in", "2.out"]
        test_case_list = self.filter_name_list(name_list, spj=spj, dir=dir)
        if not test_case_list:
            raise APIError("Empty file")

        # 创建测试用例文件夹同时更改文件夹权限
        test_case_id = rand_str()
        test_case_dir = os.path.join(settings.TEST_CASE_DIR, test_case_id)    # /data/test_case/test_case_id
        os.mkdir(test_case_dir)
        os.chmod(test_case_dir, 0o710)

        # 设置缓存
        size_cache = {}     # 如果是spj，作为input_size
        md5_cache = {}

        for item in test_case_list:
            with open(os.path.join(test_case_dir, item), "wb") as f:
                # 拼接路径,例如：/data/test_case/test_case_id/1.in
                content = zip_file.read(f"{dir}{item}").replace(b"\r\n", b"\n")
                # 设置内容的大小
                size_cache[item] = len(content)     # 最终如果是spj, 用于内容的输入大小说明
                if item.endswith(".out"):
                    # 这个是对于普通评判来说，因为特殊评判没有.out文件，同时要生成摘要保存在字典先
                    md5_cache[item] = hashlib.md5(content.rstrip()).hexdigest()
                f.write(content)            # 1.in \n 1.in\n

        # 设置测试用例备用
        test_case_info = {"spj": spj, "test_cases": {}}
        # info列表备用
        info = []

        if spj:
            for index, item in enumerate(test_case_list):
                data = {"input_name": item, "input_size": size_cache[item]}
                # info文件拼接数据
                info.append(data)
                # index是从0开始的，所以需要+1
                test_case_info["test_cases"][str(index + 1)] = data
        else:
            # 输入输出情况
            # ["1.in", "1.out", "2.in", "2.out"] => [("1.in", "1.out"), ("2.in", "2.out")]
            test_case_list = zip(*[test_case_list[i::2] for i in range(2)])
            for index, item in enumerate(test_case_list):
                data = {"stripped_output_md5": md5_cache[item[1]],
                        "input_size": size_cache[item[0]],
                        "output_size": size_cache[item[1]],
                        "input_name": item[0],
                        "output_name": item[1]}
                info.append(data)
                test_case_info["test_cases"][str(index + 1)] = data

        # 真正打开Info文件的时候，将test_case_info写入到info文件里面去
        with open(os.path.join(test_case_dir, "info"), "w", encoding="utf-8") as f:
            f.write(json.dumps(test_case_info, indent=4))

        # 对于每个文件# /data/test_case/test_case_id都更改权限
        #               -1.in
        #               -1.out
        #               -info
        for item in os.listdir(test_case_dir):
            os.chmod(os.path.join(test_case_dir, item), 0o640)

        #返回信息文件和测试用例ID
        return info, test_case_id

    def filter_name_list(self, name_list, spj, dir=""):
        # 过滤测试用例，传入一个名字列表，spj布尔变量，dir默认为空，当传入的dir不空时候，会覆盖掉空的dir
        # 定义返回列表，默认为空
        ret = []
        # 默认设置输入输出的文件的前缀为“1”
        prefix = 1

        # 如果spj为true，不要求一个1.in 对等一个 1.out， 直接进行1.in的选取，最后返回排好序的结果
        if spj:
            while True:
                in_name = f"{prefix}.in"
                if f"{dir}{in_name}" in name_list:
                    ret.append(in_name)
                    prefix += 1
                    continue
                else:
                    return sorted(ret, key=natural_sort_key)
        else:
            # 如果spj=False的话，首先假定in_name = 1.in, out_name = 1.out
            while True:
                in_name = f"{prefix}.in"
                out_name = f"{prefix}.out"
                # 首先必须是1.in，1.out, 然后才到2.in,2.out, 成对出现之后添加到列表里面，之后前缀加1，
                # 循环继续，否则一旦不满足就将返回文件排序，并返回
                if f"{dir}{in_name}" in name_list and f"{dir}{out_name}" in name_list:
                    ret.append(in_name)
                    ret.append(out_name)
                    prefix += 1
                    continue
                else:
                    return sorted(ret, key=natural_sort_key)


class TestCaseAPI(CSRFExemptAPIView, TestCaseZipProcessor):
    request_parsers = ()

    def get(self, request):                               # =================没测试
        # 还没测试
        problem_id = request.GET.get("problem_id")
        if not problem_id:
            return self.error("Parameter error, problem_id is required")
        try:
            problem = Problem.objects.get(id=problem_id)
        except Problem.DoesNotExist:
            return self.error("Problem does not exists")

        if problem.contest:
            ensure_created_by(problem.contest, request.user)
        else:
            ensure_created_by(problem, request.user)

        test_case_dir = os.path.join(settings.TEST_CASE_DIR, problem.test_case_id)
        if not os.path.isdir(test_case_dir):
            return self.error("Test case does not exists")
        name_list = self.filter_name_list(os.listdir(test_case_dir), problem.spj)
        name_list.append("info")
        file_name = os.path.join(test_case_dir, problem.test_case_id + ".zip")
        with zipfile.ZipFile(file_name, "w") as file:
            for test_case in name_list:
                file.write(f"{test_case_dir}/{test_case}", test_case)
        response = StreamingHttpResponse(FileWrapper(open(file_name, "rb")),
                                         content_type="application/octet-stream")

        response["Content-Disposition"] = f"attachment; filename=problem_{problem.id}_test_cases.zip"
        response["Content-Length"] = os.path.getsize(file_name)
        return response

    def post(self, request):
        # 使用post方法上传测试用例压缩文件
        # 使用form接受传过来的文件
        form = TestCaseUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # 表格有效，设置特殊评判为真，以及接受文件，否则抛出错误
            spj = form.cleaned_data["spj"] == "true"
            file = form.cleaned_data["file"]
        else:
            return self.error("Upload failed")
        # 设置zip_file文件，因为这里是上传特殊评判测试用例，使用随机字符串作为文件名，
        # 暂存在/tmp,等完成构建测试用力，会删除此文件
        zip_file = f"/tmp/{rand_str()}.zip"
        # 打开文件向里面写入数据chunk
        with open(zip_file, "wb") as f:
            for chunk in file:
                f.write(chunk)
        # 调用上面的process_zip方法解析，并构建测试用例
        info, test_case_id = self.process_zip(zip_file, spj=spj)
        os.remove(zip_file)
        return self.success({"id": test_case_id, "info": info, "spj": spj})


class CompileSPJAPI(APIView):
    # 此方法还没测试，到评判哪里测试
    @validate_serializer(CompileSPJSerializer)
    def post(self, request):
        data = request.data
        spj_version = rand_str(8)
        error = SPJCompiler(data["spj_code"], spj_version, data["spj_language"]).compile_spj()
        if error:
            return self.error(error)
        else:
            return self.success()


class ProblemBase(APIView):
    # 此类为题目基础类
    def common_checks(self, request):
        # 基础性逻辑问题检测，返回的情况有：Invalid spj、SPJ code must be compiled successfully、Invalid score
        data = request.data
        if data["spj"]:
            if not data["spj_language"] or not data["spj_code"]:
                return "Invalid spj"
            if not data["spj_compile_ok"]:
                return "SPJ code must be compiled successfully"
            data["spj_version"] = hashlib.md5(
                (data["spj_language"] + ":" + data["spj_code"]).encode("utf-8")).hexdigest()
        else:
            data["spj_language"] = None
            data["spj_code"] = None
        if data["rule_type"] == ProblemRuleType.OI:
            total_score = 0
            for item in data["test_case_score"]:
                if item["score"] <= 0:
                    return "Invalid score"
                else:
                    total_score += item["score"]
            data["total_score"] = total_score
        # 将题目支持的语言转化成列表
        data["languages"] = list(data["languages"])


class ProblemAPI(ProblemBase):
    # 管理员管理题目类
    @problem_permission_required
    @validate_serializer(CreateProblemSerializer)
    def post(self, request):
        # post请求创建题目
        data = request.data
        _id = data["_id"]
        if not _id:
            return self.error("Display ID is required")
        # 如果显示的_id 存在，比赛id为null
        if Problem.objects.filter(_id=_id, contest_id__isnull=True).exists():
            return self.error("Display ID already exists")

        error_info = self.common_checks(request)
        if error_info:
            return self.error(error_info)

        # todo check filename and score info
        # 先保存问题的标签备用
        tags = data.pop("tags")
        # 最后还要将创建问题的用户设置成为请求的用户
        data["created_by"] = request.user
        problem = Problem.objects.create(**data)

        # 最后将标签保存到数据库
        for item in tags:
            try:
                tag = ProblemTag.objects.get(name=item)
            except ProblemTag.DoesNotExist:
                tag = ProblemTag.objects.create(name=item)
            problem.tags.add(tag)
        return self.success(ProblemAdminSerializer(problem).data)

    @problem_permission_required
    def get(self, request):
        # 使用get方法获取题目，
        problem_id = request.GET.get("id")
        rule_type = request.GET.get("rule_type")
        user = request.user
        if problem_id:
            try:
                # 获取题目要保证是该管理员创建的题目才可以，返回序列化的题目信息
                problem = Problem.objects.get(id=problem_id)
                ensure_created_by(problem, request.user)
                return self.success(ProblemAdminSerializer(problem).data)
            except Problem.DoesNotExist:
                return self.error("Problem does not exist")
        # 如果不提供问题的ID，同时比赛的ID也是空，就按照创建的事件先后来获取
        problems = Problem.objects.filter(contest_id__isnull=True).order_by("-create_time")
        if rule_type:
            if rule_type not in ProblemRuleType.choices():
                return self.error("Invalid rule_type")
            else:
                problems = problems.filter(rule_type=rule_type)

        # 安关键字查找
        keyword = request.GET.get("keyword", "").strip()
        if keyword:
            problems = problems.filter(Q(title__icontains=keyword) | Q(_id__icontains=keyword))
        # 如果该用户不能管理所有的问题，就查找返回该用户自己创建的题目
        if not user.can_mgmt_all_problem():
            problems = problems.filter(created_by=user)
        # 经过分层的查找之后，返回分页数据（Problems-> problems）
        return self.success(self.paginate_data(request, problems, ProblemAdminSerializer))

    @problem_permission_required
    @validate_serializer(EditProblemSerializer)
    def put(self, request):
        # 修改题目
        # 接收数据同时获取该题目的ID
        data = request.data
        problem_id = data.pop("id")

        # 根据id查找题目，没有找到就返回不存在错误信息
        try:
            problem = Problem.objects.get(id=problem_id)
            ensure_created_by(problem, request.user)
        except Problem.DoesNotExist:
            return self.error("Problem does not exist")

        _id = data["_id"]
        if not _id:
            return self.error("Display ID is required")
        # 刚刚创建一个problem，有一个显示_id, 使用exclude，先排除一下这个问题，
        # 从而判定数据库里面是否存在这个显示_id，有就返回报错信息
        if Problem.objects.exclude(id=problem_id).filter(_id=_id, contest_id__isnull=True).exists():
            return self.error("Display ID already exists")

        # 一般新错误检测，有就返回错误信息
        error_info = self.common_checks(request)
        if error_info:
            return self.error(error_info)
        # todo check filename and score info
        tags = data.pop("tags")
        data["languages"] = list(data["languages"])

        # 键值使用for更新并保存到数据库
        for k, v in data.items():
            setattr(problem, k, v)
        problem.save()

        # 先将该问题的标签清空，更新数据库同时在将标签附加到问题
        problem.tags.remove(*problem.tags.all())
        for tag in tags:
            try:
                tag = ProblemTag.objects.get(name=tag)
            except ProblemTag.DoesNotExist:
                tag = ProblemTag.objects.create(name=tag)
            problem.tags.add(tag)

        return self.success()

    @problem_permission_required
    def delete(self, request):                                      # ==========没测试
        # 题目删除还没测试
        id = request.GET.get("id")
        if not id:
            return self.error("Invalid parameter, id is required")
        try:
            problem = Problem.objects.get(id=id, contest_id__isnull=True)
        except Problem.DoesNotExist:
            return self.error("Problem does not exists")
        ensure_created_by(problem, request.user)
        if Submission.objects.filter(problem=problem).exists():
            return self.error("Can't delete the problem as it has submissions")
        d = os.path.join(settings.TEST_CASE_DIR, problem.test_case_id)
        if os.path.isdir(d):
            shutil.rmtree(d, ignore_errors=True)
        problem.delete()
        return self.success()


class ContestProblemAPI(ProblemBase):
    @validate_serializer(CreateContestProblemSerializer)
    def post(self, request):
        # 创建比赛题目：一样的套路
        data = request.data
        try:
            contest = Contest.objects.get(id=data.pop("contest_id"))
            ensure_created_by(contest, request.user)
        except Contest.DoesNotExist:
            return self.error("Contest does not exist")

        if data["rule_type"] != contest.rule_type:
            return self.error("Invalid rule type")

        _id = data["_id"]
        if not _id:
            return self.error("Display ID is required")

        if Problem.objects.filter(_id=_id, contest=contest).exists():
            return self.error("Duplicate Display id")

        error_info = self.common_checks(request)
        if error_info:
            return self.error(error_info)

        # todo check filename and score info
        data["contest"] = contest
        tags = data.pop("tags")
        data["created_by"] = request.user
        problem = Problem.objects.create(**data)

        for item in tags:
            try:
                tag = ProblemTag.objects.get(name=item)
            except ProblemTag.DoesNotExist:
                tag = ProblemTag.objects.create(name=item)
            problem.tags.add(tag)
        return self.success(ProblemAdminSerializer(problem).data)

    def get(self, request):
        # 获得比赛题目
        problem_id = request.GET.get("id")
        contest_id = request.GET.get("contest_id")
        user = request.user
        # 题目ID非空就返回题目信息，但是如果之传入contest_id则不会经过这个判断，会现在执行
        if problem_id:
            # 查找竞赛问题时候，其实这里及传入问题的 id又传入比赛的id，因为要查找的是问题本身，
            # 虽然问题包含在题目里面，但是只需要返回问题即可，程序在这个判断完成之后返回
            try:
                problem = Problem.objects.get(id=problem_id)
                ensure_created_by(problem.contest, user)
            except Problem.DoesNotExist:
                return self.error("Problem does not exist")
            return self.success(ProblemAdminSerializer(problem).data)

        if not contest_id:
            return self.error("Contest id is required")
        try:
            contest = Contest.objects.get(id=contest_id)
            ensure_created_by(contest, user)
        except Contest.DoesNotExist:
            return self.error("Contest does not exist")
        problems = Problem.objects.filter(contest=contest).order_by("-create_time")
        if user.is_admin():
            problems = problems.filter(contest__created_by=user)
        keyword = request.GET.get("keyword")
        if keyword:
            problems = problems.filter(title__contains=keyword)
        return self.success(self.paginate_data(request, problems, ProblemAdminSerializer))

    @validate_serializer(EditContestProblemSerializer)
    def put(self, request):
        data = request.data
        user = request.user

        try:
            contest = Contest.objects.get(id=data.pop("contest_id"))
            ensure_created_by(contest, user)
        except Contest.DoesNotExist:
            return self.error("Contest does not exist")

        if data["rule_type"] != contest.rule_type:
            return self.error("Invalid rule type")

        problem_id = data.pop("id")

        try:
            problem = Problem.objects.get(id=problem_id, contest=contest)
        except Problem.DoesNotExist:
            return self.error("Problem does not exist")

        _id = data["_id"]
        if not _id:
            return self.error("Display ID is required")
        if Problem.objects.exclude(id=problem_id).filter(_id=_id, contest=contest).exists():
            return self.error("Display ID already exists")

        error_info = self.common_checks(request)
        if error_info:
            return self.error(error_info)
        # todo check filename and score info
        tags = data.pop("tags")
        data["languages"] = list(data["languages"])

        for k, v in data.items():
            setattr(problem, k, v)
        problem.save()

        problem.tags.remove(*problem.tags.all())
        for tag in tags:
            try:
                tag = ProblemTag.objects.get(name=tag)
            except ProblemTag.DoesNotExist:
                tag = ProblemTag.objects.create(name=tag)
            problem.tags.add(tag)
        return self.success()

    def delete(self, request):                                          # =======没测试
        id = request.GET.get("id")
        if not id:
            return self.error("Invalid parameter, id is required")
        try:
            problem = Problem.objects.get(id=id, contest_id__isnull=False)
        except Problem.DoesNotExist:
            return self.error("Problem does not exists")
        ensure_created_by(problem.contest, request.user)
        if Submission.objects.filter(problem=problem).exists():
            return self.error("Can't delete the problem as it has submissions")
        d = os.path.join(settings.TEST_CASE_DIR, problem.test_case_id)
        if os.path.isdir(d):
            shutil.rmtree(d, ignore_errors=True)
        problem.delete()
        return self.success()


class MakeContestProblemPublicAPIView(APIView):                                # =======没测试
    @validate_serializer(ContestProblemMakePublicSerializer)
    @problem_permission_required
    def post(self, request):
        data = request.data
        display_id = data.get("display_id")
        if Problem.objects.filter(_id=display_id, contest_id__isnull=True).exists():
            return self.error("Duplicate display ID")

        try:
            problem = Problem.objects.get(id=data["id"])
        except Problem.DoesNotExist:
            return self.error("Problem does not exist")

        if not problem.contest or problem.is_public:
            return self.error("Already be a public problem")
        problem.is_public = True
        problem.save()
        # https://docs.djangoproject.com/en/1.11/topics/db/queries/#copying-model-instances
        tags = problem.tags.all()
        problem.pk = None
        problem.contest = None
        problem._id = display_id
        problem.visible = False
        problem.submission_number = problem.accepted_number = 0
        problem.statistic_info = {}
        problem.save()
        problem.tags.set(tags)
        return self.success()


class AddContestProblemAPI(APIView):
    # 将公开的题目添加到比赛题目接口
    @validate_serializer(AddContestProblemSerializer)
    def post(self, request):
        data = request.data
        try:
            contest = Contest.objects.get(id=data["contest_id"])
            problem = Problem.objects.get(id=data["problem_id"])
        except (Contest.DoesNotExist, Problem.DoesNotExist):
            return self.error("Contest or Problem does not exist")

        # 添加比赛题目需在比赛还没有结束的时候
        if contest.status == ContestStatus.CONTEST_ENDED:
            return self.error("Contest has ended")
        if Problem.objects.filter(contest=contest, _id=data["display_id"]).exists():
            return self.error("Duplicate display id in this contest")

        tags = problem.tags.all()
        problem.pk = None
        # 题目对应的比赛，公开、可见
        problem.contest = contest
        problem.is_public = True
        problem.visible = True
        problem._id = request.data["display_id"]
        # 初始数据提交数量和通过数量为0
        problem.submission_number = problem.accepted_number = 0
        problem.statistic_info = {}
        problem.save()
        problem.tags.set(tags)
        return self.success()


class ExportProblemAPI(APIView):
    # 导出题目
    def choose_answers(self, user, problem):
        ret = []
        for item in problem.languages:
            submission = Submission.objects.filter(problem=problem,
                                                   user_id=user.id,
                                                   language=item,
                                                   result=JudgeStatus.ACCEPTED).order_by("-create_time").first()
            if submission:
                ret.append({"language": submission.language, "code": submission.code})
        return ret

    def process_one_problem(self, zip_file, user, problem, index):
        info = ExportProblemSerializer(problem).data
        info["answers"] = self.choose_answers(user, problem=problem)
        compression = zipfile.ZIP_DEFLATED
        zip_file.writestr(zinfo_or_arcname=f"{index}/problem.json",
                          data=json.dumps(info, indent=4),
                          compress_type=compression)
        problem_test_case_dir = os.path.join(settings.TEST_CASE_DIR, problem.test_case_id)
        with open(os.path.join(problem_test_case_dir, "info")) as f:
            info = json.load(f)
        for k, v in info["test_cases"].items():
            zip_file.write(filename=os.path.join(problem_test_case_dir, v["input_name"]),
                           arcname=f"{index}/testcase/{v['input_name']}",
                           compress_type=compression)
            if not info["spj"]:
                zip_file.write(filename=os.path.join(problem_test_case_dir, v["output_name"]),
                               arcname=f"{index}/testcase/{v['output_name']}",
                               compress_type=compression)

    @validate_serializer(ExportProblemRequestSerialzier)
    def get(self, request):
        problems = Problem.objects.filter(id__in=request.data["problem_id"])
        for problem in problems:
            if problem.contest:
                ensure_created_by(problem.contest, request.user)
            else:
                ensure_created_by(problem, request.user)
        path = f"/tmp/{rand_str()}.zip"
        with zipfile.ZipFile(path, "w") as zip_file:
            for index, problem in enumerate(problems):
                self.process_one_problem(zip_file=zip_file, user=request.user, problem=problem, index=index + 1)
        delete_files.apply_async((path,), countdown=300)
        resp = FileResponse(open(path, "rb"))
        resp["Content-Type"] = "application/zip"
        resp["Content-Disposition"] = f"attachment;filename=problem-export.zip"
        return resp


class ImportProblemAPI(CSRFExemptAPIView, TestCaseZipProcessor):            # =====还没测试
    # 导入题目
    request_parsers = ()

    def post(self, request):
        form = UploadProblemForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data["file"]
            tmp_file = f"/tmp/{rand_str()}.zip"
            with open(tmp_file, "wb") as f:
                for chunk in file:
                    f.write(chunk)
        else:
            return self.error("Upload failed")

        count = 0
        with zipfile.ZipFile(tmp_file, "r") as zip_file:
            name_list = zip_file.namelist()
            for item in name_list:
                if "/problem.json" in item:
                    count += 1
            with transaction.atomic():
                for i in range(1, count + 1):
                    with zip_file.open(f"{i}/problem.json") as f:
                        problem_info = json.load(f)
                        serializer = ImportProblemSerializer(data=problem_info)
                        if not serializer.is_valid():
                            return self.error(f"Invalid problem format, error is {serializer.errors}")
                        else:
                            problem_info = serializer.data
                            for item in problem_info["template"].keys():
                                if item not in SysOptions.language_names:
                                    return self.error(f"Unsupported language {item}")

                        problem_info["display_id"] = problem_info["display_id"][:24]
                        for k, v in problem_info["template"].items():
                            problem_info["template"][k] = build_problem_template(v["prepend"], v["template"],
                                                                                 v["append"])

                        spj = problem_info["spj"] is not None
                        rule_type = problem_info["rule_type"]
                        test_case_score = problem_info["test_case_score"]

                        # process test case
                        _, test_case_id = self.process_zip(tmp_file, spj=spj, dir=f"{i}/testcase/")

                        problem_obj = Problem.objects.create(_id=problem_info["display_id"],
                                                             title=problem_info["title"],
                                                             description=problem_info["description"]["value"],
                                                             input_description=problem_info["input_description"][
                                                                 "value"],
                                                             output_description=problem_info["output_description"][
                                                                 "value"],
                                                             hint=problem_info["hint"]["value"],
                                                             test_case_score=test_case_score if test_case_score else [],
                                                             time_limit=problem_info["time_limit"],
                                                             memory_limit=problem_info["memory_limit"],
                                                             samples=problem_info["samples"],
                                                             template=problem_info["template"],
                                                             rule_type=problem_info["rule_type"],
                                                             source=problem_info["source"],
                                                             spj=spj,
                                                             spj_code=problem_info["spj"]["code"] if spj else None,
                                                             spj_language=problem_info["spj"][
                                                                 "language"] if spj else None,
                                                             spj_version=rand_str(8) if spj else "",
                                                             languages=SysOptions.language_names,
                                                             created_by=request.user,
                                                             visible=False,
                                                             difficulty=Difficulty.MID,
                                                             total_score=sum(item["score"] for item in test_case_score)
                                                             if rule_type == ProblemRuleType.OI else 0,
                                                             test_case_id=test_case_id
                                                             )
                        for tag_name in problem_info["tags"]:
                            tag_obj, _ = ProblemTag.objects.get_or_create(name=tag_name)
                            problem_obj.tags.add(tag_obj)
        return self.success({"import_count": count})


class FPSProblemImport(CSRFExemptAPIView):                              # ==========还没测试
    # 使用FPS导入
    request_parsers = ()

    def _create_problem(self, problem_data, creator):
        if problem_data["time_limit"]["unit"] == "ms":
            time_limit = problem_data["time_limit"]["value"]
        else:
            time_limit = problem_data["time_limit"]["value"] * 1000
        template = {}
        prepend = {}
        append = {}
        for t in problem_data["prepend"]:
            prepend[t["language"]] = t["code"]
        for t in problem_data["append"]:
            append[t["language"]] = t["code"]
        for t in problem_data["template"]:
            our_lang = lang = t["language"]
            if lang == "Python":
                our_lang = "Python3"
            template[our_lang] = TEMPLATE_BASE.format(prepend.get(lang, ""), t["code"], append.get(lang, ""))
        spj = problem_data["spj"] is not None
        Problem.objects.create(_id=f"fps-{rand_str(4)}",
                               title=problem_data["title"],
                               description=problem_data["description"],
                               input_description=problem_data["input"],
                               output_description=problem_data["output"],
                               hint=problem_data["hint"],
                               test_case_score=[],
                               time_limit=time_limit,
                               memory_limit=problem_data["memory_limit"]["value"],
                               samples=problem_data["samples"],
                               template=template,
                               rule_type=ProblemRuleType.ACM,
                               source=problem_data.get("source", ""),
                               spj=spj,
                               spj_code=problem_data["spj"]["code"] if spj else None,
                               spj_language=problem_data["spj"]["language"] if spj else None,
                               spj_version=rand_str(8) if spj else "",
                               visible=False,
                               languages=SysOptions.language_names,
                               created_by=creator,
                               difficulty=Difficulty.MID,
                               test_case_id=problem_data["test_case_id"])

    def post(self, request):
        form = UploadProblemForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data["file"]
            with tempfile.NamedTemporaryFile("wb") as tf:
                for chunk in file.chunks(4096):
                    tf.file.write(chunk)
                problems = FPSParser(tf.name).parse()
        else:
            return self.error("Parse upload file error")

        helper = FPSHelper()
        with transaction.atomic():
            for _problem in problems:
                test_case_id = rand_str()
                test_case_dir = os.path.join(settings.TEST_CASE_DIR, test_case_id)
                os.mkdir(test_case_dir)
                helper.save_test_case(_problem, test_case_dir)
                problem_data = helper.save_image(_problem, settings.UPLOAD_DIR, settings.UPLOAD_PREFIX)
                s = FPSProblemSerializer(data=problem_data)
                if not s.is_valid():
                    return self.error(f"Parse FPS file error: {s.errors}")
                problem_data = s.data
                problem_data["test_case_id"] = test_case_id
                self._create_problem(problem_data, request.user)
        return self.success({"import_count": len(problems)})
