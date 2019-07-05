from django.test import TestCase
import copy
import hashlib
import os
import shutil
from datetime import timedelta
from zipfile import ZipFile

from django.conf import settings

from myutils.api.tests import APITestCase

from .models import ProblemTag
from .models import Problem, ProblemRuleType
from contest.models import Contest
# 导入默认的比赛数据
from contest.tests import DEFAULT_CONTEST_DATA

from .views.viadmin import TestCaseAPI
from .utils import parse_problem_template

# 首先设置默认的测试数据，默认spj为false，spj_compile_ok为True，contest_id默认为空
DEFAULT_PROBLEM_DATA = {"_id": "A-110", "title": "test", "description": "<p>test</p>", "input_description": "test",
                        "output_description": "test", "time_limit": 1000, "memory_limit": 256, "difficulty": "Low",
                        "visible": True, "tags": ["test"], "languages": ["C", "C++", "Java", "Python2"], "template": {},
                        "samples": [{"input": "test", "output": "test"}], "spj": False, "spj_language": "C",
                        "spj_code": "", "spj_compile_ok": True, "test_case_id": "499b26290cc7994e0b497212e842ea85",
                        "test_case_score": [{"output_name": "1.out", "input_name": "1.in", "output_size": 0,
                                             "stripped_output_md5": "d41d8cd98f00b204e9800998ecf8427e",
                                             "input_size": 0, "score": 0}],
                        "rule_type": "ACM", "hint": "<p>test</p>", "source": "test"}


class ProblemCreateTestBase(APITestCase):
    # 题目创建测试基础，本类作为父类被继承调用
    @staticmethod
    def add_problem(problem_data, created_by):
        # 添加题目：题目数据和创建者
        # 首先是从传入的数据里面获取数据，然后配置题目信息
        data = copy.deepcopy(problem_data)
        # 首先判断是否需要进行特殊评判
        if data["spj"]:
            if not data["spj_language"] or not data["spj_code"]:
                raise ValueError("Invalid spj")
            # apj的version的数值是由apj_language和spj_code 组成的键值对形式，经过utf-8编码之后，
            # 再次经过摘要算法生成摘要字符串，apj就是这样保持其唯一的版本
            data["apj_version"] = hashlib.md5(
                (data["spj_language"] + ":" + data["spj_code"]).encode("utf-8")).hexdigest()
        else:
            # 否则就设置特殊评判的语言和代码为None
            data["spj_language"] = None
            data["spj_code"] = None
        # 如果评判类型为OI,初始化总分
        if data["rule_type"] == ProblemRuleType.OI:
            total_score = 0
            for item in data["test_case_score"]:
                if item["score"] <= 0:
                    raise ValueError("invalid score")
                else:
                    total_score += item["score"]
            data["total_score"] = total_score
        # 设置题目的创建这created_by ,这个字段是由用户传进来的
        data["created_by"] = created_by
        # 设置问题的标签：将data里面的tags全部pop出来,因为标签是一个表单独
        # 存放的，所以这里不会和Problems同时创建到Problems表
        tags = data.pop("tags")

        # 因为一道题目可以选择有不同的语言可以进行AC，所以将语言真一项转化成一个列表
        data["languages"] = list(data["languages"])

        # 根据更新配置的数据创建问题
        problem = Problem.objects.create(**data)

        # 创建题目之后单独处理标签，标签表其实就是一个id对应一种标签，一个字段非常简单
        for item in tags:
            try:
                # 根据标签名查找标签，如果没有这个标签就将这个标签添加到数据库里面去
                tag = ProblemTag.objects.get(name=item)
            except ProblemTag.DoesNotExist:
                tag = ProblemTag.objects.create(name=item)

            # 最后循环将标签添加到问题的标签列表中
            problem.tags.add(tag)
        return problem


class ProblemTagListAPITest(APITestCase):
    def test_get_tag_list(self):
        # 测试获取题目标签的列表
        ProblemTag.objects.create(name="name1")
        ProblemTag.objects.create(name="name2")
        resp = self.client.get(self.reverse("problem_tag_list_api"))
        self.assertSuccess(resp)


class TestCaseUploadAPITest(APITestCase):
    def setUp(self):
        self.api = TestCaseAPI()
        self.url = self.reverse("test_case_api")
        self.create_super_admin()

    def test_filter_file_name(self):
        # filter_name_list在TestCaseAPI继承的TestCaseZipProcesser中
        # 过滤文件名称：首先要先以1出现并且要同时有.in和.out出现才能通过
        # 没有使用self.url请求，直接使用继承调用方法
        self.assertEqual(self.api.filter_name_list(["1.in", "1.out", "2.in", ".DS_Store"], spj=False), ["1.in", "1.out"])
        # 因为没有1.in和1.out，所以返回为空
        self.assertEqual(self.api.filter_name_list(["2.in", "2.out"], spj=False), [])

        # 需要进行特殊评判，只选取x.in文件，但是也需要进行排序
        self.assertEqual(self.api.filter_name_list(["1.in", "1.out", "2.in"], spj=True), ["1.in", "2.in"])
        self.assertEqual(self.api.filter_name_list(["2.in", "3.in"], spj=True),[])

    def make_test_case_zip(self):
        # 创建测试案例的zip包
        # 创建基础目录
        base_dir = os.path.join("/tmp", "test_case")
        shutil.rmtree(base_dir, ignore_errors=True)
        os.mkdir(base_dir)  # /tmp/test_case
        # 提供文件列表
        file_names = ["1.in", "1.out", "2.in", ".DS_Store"]
        for item in file_names:    # /tmp/test_case/1.in(1.out, 2.in, .DS_Store)
            with open(os.path.join(base_dir, item), "w", encoding="utf-8") as f:
                f.write(item + "\n" + item + "\r\n" + "end")            # 写入的内容就是：每个文件中存放两行本文件名：1.in \n 1.in \r\n
        # 设置压缩文件路径，写完之后就压缩
        zip_file = os.path.join(base_dir, "test_case.zip")
        # 使用ZipFile压缩文件，压缩完成之后，这个压缩文件里面含有文件["1.in", "1.out", "2.in", ".DS_Store"]
        # 再次在每个文件中写入文件的路径，并返回zip_file
        with ZipFile(os.path.join(base_dir, "test_case.zip"), "w") as f:
            for item in file_names:
                f.write(os.path.join(base_dir, item), item)         # /tmp/test_case/1.in(1.out, 2.in, .DS_Store)
        return zip_file                         # 返回/tmp/test_case/test_case.zip

    def test_upload_spj_test_case_zip(self):
        # 测试上传特殊评判样例压缩文件
        # 创建压缩文件并打开，写二进制方式
        with open(self.make_test_case_zip(), "rb") as f:
            # 请求数据有特殊评判和压缩文件f
            resp = self.client.post(self.url, data={"spj": "true", "file": f}, format="multipart")
            self.assertSuccess(resp)
            data = resp.data["data"]
            self.assertEqual(data["spj"], True)
            # 测试用例存放到的目录
            test_case_dir = os.path.join(settings.TEST_CASE_DIR, data["id"])
            self.assertTrue(os.path.exists(test_case_dir))
            for item in data["info"]:
                name = item["input_name"]
                with open(os.path.join(test_case_dir, name), "r", encoding="utf-8") as f:
                    # 最后读到的数据就是例如：1.in \n 1.in\n
                    self.assertEqual(f.read(), name + "\n" + name + "\n" + "end")

    def test_upload_test_case_zip(self):
        # 直接在Pycharm测试会出现权限不足的情况
        with open(self.make_test_case_zip(), "rb") as f:
            resp = self.client.post(self.url,data={"spj": "false", "file": f}, format="multipart")
            self.assertSuccess(resp)
            data = resp.data["data"]
            self.assertEqual(data["apj"], False)
            test_case_dir = os.path.join(settings.TEST_CASE_DIR, data["id"])
            self.assertTrue(os.path.exists(test_case_dir))
            for item in data["info"]:
                name = item["input_name"]
                with open(os.path.join(test_case_dir, name), "r", encoding="utf-8") as f:
                    self.assertEqual(f.read(), name + "\n" + name + "\n" + "end")


class ProblemAdminAPITest(APITestCase):
    # 管理员管理题目
    def setUp(self):
        self.url = self.reverse("problem_admin_api")
        self.create_super_admin()
        self.data = copy.deepcopy(DEFAULT_PROBLEM_DATA)

    def test_create_problem(self):
        # 创建题目
        resp = self.client.post(self.url, data=self.data)
        self.assertSuccess(resp)
        # 返回resp供下面的方法调用
        return resp

    def test_duplicate_display_id(self):
        # 对个问题检测，基于上面已经创建的题目
        self.test_create_problem()
        resp = self.client.post(self.url,data=self.data)
        self.assertFailed(resp, "Display ID already exists")

    def test_spj(self):
        # 测试特殊评判
        data = copy.deepcopy(self.data)
        data["spj"] = True

        # 默认是不提供spj_code的，分别进行不提供spj_code和提供spj_code进行测试，common_checks的测试
        resp = self.client.post(self.url, data)
        self.assertFailed(resp, "Invalid spj")

        data["spj_code"] = "test"
        resp = self.client.post(self.url, data=data)
        self.assertSuccess(resp)

    def test_get_problem(self):
        # 获取题目
        self.test_create_problem()
        resp = self.client.get(self.url)
        self.assertSuccess(resp)

    def test_get_one_problem(self):
        # 获取一个问题，先创建一个题目，接着查询出来
        problem_id = self.test_create_problem().data["data"]["id"]
        resp = self.client.get(self.url + "?id=" + str(problem_id))
        self.assertSuccess(resp)

    def test_edit_problem(self):
        # 编辑问题，使用put，先是没有指定problem_id的，该id由数据库自动生成
        problem_id = self.test_create_problem().data["data"]["id"]
        data = copy.deepcopy(self.data)
        # 创建题目之后要将该id传入才能找到该题目，然后才能修改
        data["id"] = problem_id
        resp = self.client.put(self.url, data=data)
        self.assertSuccess(resp)


class ProblemAPITest(ProblemCreateTestBase):
    # 普通用户题目接口测试
    def setUp(self):
        # 创建超级用户是为了创建题目，然后单独创建一个普通用户作为测试
        self.url = self.reverse("problem_api")
        admin = self.create_admin(login=False)
        self.problem = self.add_problem(DEFAULT_PROBLEM_DATA, admin)
        self.create_user("test", "test123")

    # 普通用户的权限就仅限于查看题目列表，每次查10条和查看单个题目信息
    def test_get_problem_list(self):
        resp = self.client.get(f"{self.url}?limit=10")
        self.assertSuccess(resp)

    def test_get_one_problem(self):
        # 查找单挑数据
        resp = self.client.get(self.url + "?problem_id=" + self.problem._id)
        self.assertSuccess(resp)


class ContestProblemAdminTest(APITestCase):
    def setUp(self):
        # 创建超级用户和添加比赛
        self.url = self.reverse("contest_problem_admin_api")
        self.create_admin()
        self.contest = self.client.post(self.reverse("contest_admin_api"), data=DEFAULT_CONTEST_DATA).data["data"]

    def test_create_contest_problem(self):
        # 创建比赛题目
        data = copy.deepcopy(DEFAULT_PROBLEM_DATA)
        # 添加contest_id
        data["contest_id"] = self.contest["id"]
        resp = self.client.post(self.url, data=data)
        self.assertSuccess(resp)
        return resp.data["data"]

    def test_get_contest_problem(self):
        # 获取比赛题目
        self.test_create_contest_problem()
        contest_id = self.contest["id"]
        resp = self.client.get(self.url + "?contest_id=" + str(contest_id))
        self.assertSuccess(resp)
        # 返回分页中的查询到的数据集合的长度
        self.assertEqual(len(resp.data["data"]["results"]), 1)

    def test_get_one_contest_problem(self):
        # 其实这里及传入问题的 id又传入比赛的id，因为要查找的是问题本身，虽然问题包含在题目里面，但是只需要返回问题即可
        contest_problem = self.test_create_contest_problem()
        contest_id = self.contest["id"]
        problem_id = contest_problem["id"]
        # 注意这里传入两个参数的写法URL之后接着？，参数之间使用&分割
        resp = self.client.get(f"{self.url}?contest_id={contest_id}&id={problem_id}")
        self.assertSuccess(resp)


# ===================================================检查检查！！！！！==============================
# ==========诡秘的传值，传入contest_id时候竟然不接收，但是事实上是不用接受的，因为在get方法里面直接找到contest了=========
class ContestProblemTest(ProblemCreateTestBase):
    # 普通用户的比赛题目测试，这个测试有点诡秘，再看看
    def setUp(self):
        admin = self.create_admin()
        url = self.reverse("contest_admin_api")     # 这个命名空间是比赛contest的APP的命名空间，引入为了创建一个比赛
        contest_data = copy.deepcopy(DEFAULT_CONTEST_DATA)
        contest_data["password"] = ""
        contest_data["start_time"] = contest_data["start_time"] + timedelta(hours=1)
        self.contest = self.client.post(url, data=contest_data).data["data"]
        # 往数据库中添加题目
        self.problem = self.add_problem(DEFAULT_PROBLEM_DATA, admin)
        self.problem.contest_id = self.contest["id"]
        self.problem.save()
        self.url = self.reverse("contest_problem_api")      # 问题命名空间

    def test_admin_get_contest_problem_list(self):
        # 管理员获取比赛的题目列表
        contest_id = self.contest["id"]
        print(self.url )
        resp = self.client.get(self.url + "?contest_id=" + str(contest_id))
        self.assertSuccess(resp)
        self.assertEqual(len(resp.data["data"]), 1)

    def test_admin_get_one_contest_problem(self):
        # 获取一个比赛题目
        contest_id = self.contest["id"]
        problem_id = self.problem._id
        resp = self.client.get("{}?contest_id={}&problem_id={}".format(self.url, contest_id, problem_id))
        self.assertSuccess(resp)

    def test_regular_user_get_not_started_contest_problem(self):
        # 常规用户获取还没开始的比赛问题
        self.create_user("test", "test123")
        resp = self.client.get(self.url + "?contest_id=" + str(self.contest["id"]))
        self.assertDictEqual(resp.data, {"error": "error", "data": "Contest has not started yet."})

    def test_reguar_user_get_started_contest_problem(self):
        # 常规用户获取已经开始的比赛问题
        self.create_user("test", "test123")
        contest = Contest.objects.first()
        contest.start_time = contest.start_time - timedelta(hours=1)
        contest.save()
        resp = self.client.get(self.url + "?contest_id=" + str(self.contest["id"]))
        self.assertSuccess(resp)


class AddProblemFromPublicProblemAPITest(ProblemCreateTestBase):
    # 添加
    def setUp(self):
        # 创建超级用户
        admin = self.create_admin()
        url = self.reverse("contest_admin_api")
        contest_data = copy.deepcopy(DEFAULT_CONTEST_DATA)
        contest_data["password"] = ""
        contest_data["start_time"] = contest_data["start_time"] + timedelta(hours=1)
        # 创建比赛
        self.contest = self.client.post(url, data=contest_data).data["data"]
        self.problem = self.add_problem(DEFAULT_PROBLEM_DATA, admin)
        self.url = self.reverse("add_contest_problem_from_public_api")
        self.data = {
            "display_id": "1000",
            "contest_id": self.contest["id"],
            "problem_id": self.problem.id
        }

    def test_add_contest_problem(self):
        # 添加竞赛题目
        resp = self.client.post(self.url, data=self.data)
        self.assertSuccess(resp)
        self.assertTrue(Problem.objects.all().exists())
        self.assertTrue(Problem.objects.filter(contest_id=self.contest["id"]).exists())


# ==================================测试未通过=====================
class ParseProblemTemplateTest(APITestCase):
    def test_parse(self):
        # 模板
        template_str = """
    //PREPEND BEGIN
    aaa
    //PREPEND END

    //TEMPLATE BEGIN
    bbb
    //TEMPLATE END

    //APPEND BEGIN
    ccc
    //APPEND END
    """
        # 调用问题模板解析来测试
        ret = parse_problem_template(template_str)
        self.assertEqual(ret["prepend"], "aaa\n")
        self.assertEqual(ret["template"], "bbb\n")
        self.assertEqual(ret["append"], "ccc\n")

    def test_parse1(self):
        template_str = """
    //PREPEND BEGIN
    aaa
    //PREPEND END

    //APPEND BEGIN
    ccc
    //APPEND END
    //APPEND BEGIN
    ddd
    //APPEND END
    """

        ret = parse_problem_template(template_str)
        self.assertEqual(ret["prepend"], "aaa\n")
        self.assertEqual(ret["template"], "")
        self.assertEqual(ret["append"], "ccc\n")






















