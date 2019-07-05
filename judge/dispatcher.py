#!/usr/bin/env python
# -*-encoding:UTF-8-*-
# 判题服务核心类文件：调度者dispatcher

import hashlib   # 摘要算法
import json
import logging
from urllib.parse import urljoin

import requests
from django.db import transaction
from django.db.models import F  # 条件查询

from account.models import User
from conf.models import JudgeServer
from contest.models import ContestRuleType, ACMContestRank, OIContestRank, ContestStatus
from options.options import SysOptions
from problem.models import Problem, ProblemRuleType

from problem.utils import parse_problem_template   #noqa

from submission.models import JudgeStatus, Submission
from myutils.cache import cache
from myutils.constants import CacheKey

logger = logging.getLogger(__name__)


# 继续处理在队列中的任务
def process_pending_task():
    # 如果llen："Return the length of the list ``name``"返回的waiting_queue名字长度不空，
    # 队列中还有任务，导入评判任务judge_task，加载在队列里面等待的任务到异步队列
    if cache.llen(CacheKey.waiting_queue):
        # 防止循环引入
        from judge.tasks import judge_task
        data = json.loads(cache.rpop(CacheKey.waiting_queue).decode("utf-8"))
        judge_task.delay(**data)


class DispatcherBase(object):
    def __init__(self):
        # judge_server_token默认就是judge_server_token
        self.token = hashlib.sha256(SysOptions.judge_server_token.encode("utf-8")).hexdigest()

    def _request(self, url, data=None):
        kwargs = {"headers": {"X-Judge-Server-Token": self.token}}
        if data:
            # 设置键值对关键参数kwargs为传入的数据
            kwargs["json"] = data
        try:
            # 在这里通过post的方法请求后端的评测机---------------->>>>>>>>>>>>>>>>>这里是判题入口
            return requests.post(url, **kwargs).json()
        except Exception as e:
            logger.exception(e)

    @staticmethod
    def choose_judge_server():
        # 选择测评服务器
        with transaction.atomic():
            # 按照任务数字排列，将能够判题的Server查出来
            servers = JudgeServer.objects.select_for_update().filter(is_disabled=False).order_by("task_number")
            # 选出servers中server状态为normal的评测机组成新的servers
            servers = [s for s in servers if s.status == "normal"]
            for server in servers:
                # 根据原来server的任务数设置新的任务数
                if server.task_number <= server.cpu_core * 2:
                    server.task_number = F("task_number") + 1
                    server.save()
                    return server

    @staticmethod
    def release_judge_server(judge_server_id):
        # 释放判题测评机
        with transaction.atomic():
            # 使用原子操作, 同时因为use和release中间间隔了判题过程,需要重新查询一下
            server = JudgeServer.objects.get(id=judge_server_id)
            # 释放server就将任务数减去1，以便其他的任务被安排上
            server.task_number = F("task_number") - 1
            server.save()


class SPJCompiler(DispatcherBase):
    # 特殊评判编译类
    def __init__(self, spj_code, spj_version, spj_language):
        # 初始化特殊评判编译配置spj_compile_config
        super().__init__()
        # 根据输入的config，获得里面的config["name"]，从而获得spj_language
        spj_compile_config = list(filter(lambda config: spj_language == config["name"], SysOptions.spj_languages))[0]["spj"][
            "compile"]
        self.data = {
            "src": spj_code,
            "spj_version": spj_version,
            "spj_compile_config": spj_compile_config
        }

    def compile_spj(self):
        # 编译特殊评判
        server = self.choose_judge_server()
        # 如果当前没有可用的Server，返回错误
        if not server:
            return "No available judge_server"
        # 拼接server的url和compile_spj的路径当做请求路径---->发送请求判题
        result = self._request(urljoin(server.service_url, "compile_spj"), data=self.data)
        # 结果返回之后释放server，出现错误err就返回对应的data
        self.release_judge_server(server.id)
        if result["err"]:
            return result["data"]


class JudgeDispatcher(DispatcherBase):
    # 评测调度者类
    def __init__(self, submission_id, problem_id):
        # 初始化sumission、比赛contest_id、last_result
        super().__init__()
        self.submission = Submission.objects.get(id=submission_id)
        self.contest_id = self.submission.contest_id
        # 如果self.submissiom.info(从评测机返回的信息) 不空，那最近一次（上一次）的结果（last_result）也就是self.submission.result，否则是None
        # self.submission.result默认数据是JudgeStatus.PENDING，那么self.last_result在有数据返回的情况下值也是JudgeStatus.PENDING
        self.last_result = self.submission.result if self.submission.info else None

        # 设置比赛id和题目id
        # 比赛id非空就要设置题目id和题目归属的比赛id，就是外键关系，否则说明题目并不依附于比赛，肯能就是用户从问题列表中找一道题目来尝试ac
        if self.contest_id:
            self.problem = Problem.objects.select_related("contest").get(id=problem_id, contest_id=self.contest_id)
            self.contest = self.problem.contest
        else:
            self.problem = Problem.objects.get(id=problem_id)

    def _compute_statistic_info(self, resp_data):
        # 根据评判结果返回的数据计算统计信息：内存使用、时间使用、OI分数
        # 用时和内存占用保存为多个测试点中最长的那个
        self.submission.statistic_info["time_cost"] = max([x["cpu_time"] for x in resp_data])
        self.submission.statistic_info["memory_cost"] = max([x["memory"] for x in resp_data])

        # sum up the score in OI mode
        if self.problem.rule_type == ProblemRuleType.OI:
            score = 0
            try:
                for i in range(len(resp_data)):
                    # 题目处于AC状态才计分否则总分为0
                    if resp_data[i]["result"] == JudgeStatus.ACCEPTED:
                        # 从第i个问题对应的测试用例得到的分数赋值给resp_data[i]["score"]开始，循环将所有的分数相加
                        resp_data[i]["score"] = self.problem.test_case_score[i]["score"]
                        score += resp_data[i]["score"]
                    else:
                        resp_data[i]["score"] = 0
            except IndexError:
                # 只用一种情况就是索引出错，导致计分出错
                logger.error(f"Index Error raised when summing up the score in problem {self.problem.id}")
                self.submission.statistic_info["score"] = 0
                return
            # 计分正常，得出统计分数
            self.submission.statistic_info["score"] = score

    def judge(self):
        # 先选择评测机
        server = self.choose_judge_server()
        if not server:
            # 没有Server说明现在被用完，需要等一下
            data = {"submission_id": self.submission.id, "problem_id": self.problem.id}
            # 缓存存放等待任务，返回
            cache.lpush(CacheKey.waiting_queue, json.dumps(data))
            return

        # 提交代码所选择的语言
        language = self.submission.language
        # 提交信息配置sub_config和特殊评判信息配置spj_config
        # 过滤各项名字为系统的选项语言，并保存在语言language，形成一个列表，取到第一项（下标为0）
        sub_config = list(filter(lambda item: language == item["name"], SysOptions.languages))[0]
        spj_config = {}

        # 需要进行特殊评判：配置评判语言
        if self.problem.spj_code:
            for lang in SysOptions.spj_languages:
                if lang["name"] == self.problem.spj_language:
                    spj_config = lang["spj"]
                    break

        # 如果提交的语言包含在问题的模板里面，解析模板，重新拼接成新的代码，否则就直接选取配置代码
        if language in self.problem.template:
            template = parse_problem_template(self.problem.template[language])
            code = f"{template['prepend']}\n{self.submission.code}\n{template['append']}"
        else:
            code = self.submission.code

        # 提交数据信息
        data = {
            "language_config": sub_config["config"],
            "src": code,
            "max_cpu_time": self.problem.time_limit,
            "max_memory": 1024 * 1024 * self.problem.memory_limit,
            "test_case_id": self.problem.test_case_id,
            "output": False,
            "spj_version": self.problem.spj_version,
            "spj_config": spj_config.get("config"),
            "spj_compile_config": spj_config.get("compile"),
            "spj_src": self.problem.spj_code
        }

        # 将对应ID的提交信息更新到提交信息数据表，状态由waiting_queue--->JUDGING
        Submission.objects.filter(id=self.submission.id).update(result=JudgeStatus.JUDGING)

        # 评判请求发起------->>>>请求后台评判机
        resp = self._request(urljoin(server.service_url, "/judge"), data=data)

        # 根据返回的评测结果信息设置提交信息表字段并保存到数据库表
        if resp["err"]:
            self.submission.result = JudgeStatus.COMPILE_ERROR
            self.submission.statistic_info["err_info"] = resp["data"]
            self.submission.statistic_info["score"] = 0
        else:
            # 成功后，将返回的数据按照test_case顺序排序
            resp["data"].sort(key=lambda x: int(x["test_case"]))
            # 更具响应信息设置提交信息，统计返回的信息
            self.submission.info = resp
            self._compute_statistic_info(resp["data"])
            # 过滤resp["data"]中未通过的测试案例到list，并赋值给error_test_case
            error_test_case = list(filter(lambda case: case["result"] != 0, resp["data"]))
            # ACM模式下,多个测试点全部正确则AC，否则取第一个错误的测试点的状态
            # OI模式下, 若多个测试点全部正确则AC， 若全部错误则取第一个错误测试点状态，否则为部分正确
            if not error_test_case:
                self.submission.result = JudgeStatus.ACCEPTED
            elif self.problem.rule_type == ProblemRuleType.ACM or len(error_test_case) == len(resp["data"]):
                self.submission.result = error_test_case[0]["result"]
            else:
                self.submission.result = JudgeStatus.PARTIALLY_ACCEPTED
        # 保存提交信息，并释放Server
        self.submission.save()
        self.release_judge_server(server.id)

        if self.contest_id:
            # 如果当前不是正在进行比赛 或者 当前的提交信息对应的用户是比赛的创建者（当前用户是管理员），
            # 日志中记录管理员是在进行调试：显示contest_id和submission.id
            if self.contest.status != ContestStatus.CONTEST_UNDERWAY or \
                    User.objects.get(id=self.submission.user_id).is_contest_admin(self.contest):
                logger.info(
                    "Contest debug mode, id: " + str(self.contest_id) + ", submission id: " + self.submission.id)
                return
            # 否则说明是普通用户在进行比赛，更新比赛问题状态和排名
            self.update_contest_problem_status()
            self.update_contest_rank()
        else:
            # 最近的判题（上一次返回的判题）结果不空，就是说评测机Judge Server有信息返回，说明你上一次提交了一次（AC/not AC）,这次再提交（往往是没AC时候）
            # 否则就刷新问题状态（例如有一道题被ac，则此题的被ac率应该更新）
            if self.last_result:
                self.update_problem_status_rejudge()
            else:
                self.update_problem_status()

        # 至此判题结束，尝试处理任务队列中剩余的任务
        process_pending_task()

    def update_problem_status_rejudge(self):
        # 更新数据：当一次提交不通过，又一次提交时候，走这个函数
        # 此方法更新的是用户配置表的数据
        result = str(self.submission.result)
        problem_id = str(self.problem.id)
        with transaction.atomic():
            # update problem status
            problem = Problem.objects.select_for_update().get(contest_id=self.contest_id, id=self.problem.id)
            # 上一次评测结果不是AC，而这次AC，那么AC数就加1
            if self.last_result != JudgeStatus.ACCEPTED and self.submission.result == JudgeStatus.ACCEPTED:
                problem.accepted_number += 1
            # 更新题目的AC数目和统计信息（字典类型：统计题目的ac，wa等），注意get方法的使用
            problem_info = problem.statistic_info
            # 统计信息字典中排队数减1，last_result默认是pending
            problem_info[self.last_result] = problem_info.get(self.last_result, 1) - 1
            # 统计信息字典中的结果字段下PENDING(=6) + 1 --> JUDGING(=7)
            problem_info[result] = problem_info.get(result, 0) + 1
            problem.save(update_fields=["accepted_number", "statistic_info"])

            # 更新用户的配置信息，例如题目的ac数目
            profile = User.objects.select_for_update().get(id=self.submission.user_id).userprofile
            if problem.rule_type == ProblemRuleType.ACM:
                # 获取已经AC的问题的字典数据，里面的题目都已经AC
                acm_problems_status = profile.acm_problems_status.get("problems", {})
                # 如果用户本身对此题目ac不通过(默认是这样)，那么对此题目的ac状态赋值为这次自身提交信息的结果
                if acm_problems_status[problem_id]["status"] != JudgeStatus.ACCEPTED:
                    acm_problems_status[problem_id]["status"] = self.submission.result
                    # 进一步判断，如果这次对这道题目提交的结果ac了，ac数目加1
                    if self.submission.result == JudgeStatus.ACCEPTED:
                        profile.accepted_number += 1
                # 如果本身已经AC通过，赋值回自身，不做更改（不能这次没通过就抹掉前面的AC状态），同时更新用户配置数据
                profile.acm_problems_status["problems"] = acm_problems_status
                profile.save(update_fields=["accepted_number", "acm_problems_status"])

            else:
                # 获取用户配置信息中OI通过的状态信息
                oi_problems_status = profile.oi_problems_status.get("problems", {})
                # 取到本次做OI题目的总分score
                score = self.submission.statistic_info["score"]
                # 如果上一次OI题目不AC
                if oi_problems_status[problem_id]["status"] != JudgeStatus.ACCEPTED:
                    # 注意：计算总分时候，应该先减掉上一次该题所得的分数，然后再加上本次所得的分数，这样就不会出现冲突混乱，不然你要怎样计分
                    profile.add_score(this_time_score=score,
                                      last_time_score=oi_problems_status[problem_id]["score"])
                    # 将此问题的分数更新为本次所得的分数，同时更新次题目的状态为本次OI状态，如果上次得分多，本次得分少，那就分数少了，就是这个规则
                    oi_problems_status[problem_id]["score"] = score
                    oi_problems_status[problem_id]["status"] = self.submission.result
                    # 上次没AC，今次AC，那就AC+1，vice versa
                    if self.submission.result == JudgeStatus.ACCEPTED:
                        profile.accepted_number += 1
                # 如果本身已经AC通过，赋值回自身，不做更改（不能这次没通过就抹掉前面的AC状态），同时更新用户配置数据
                profile.oi_problems_status["problems"] = oi_problems_status
                profile.save(update_fields=["accepted_number", "oi_problems_status"])

    def update_problem_status(self):
        # 更新问题状态，
        result = str(self.submission.result)
        problem_id = str(self.problem.id)
        with transaction.atomic():
            # 更新问题状态：题目提交数、ac数、统计信息的AC数，跟新数据库
            problem = Problem.objects.select_for_update().get(contest_id=self.contest_id, id=self.problem.id)
            problem.submission_number += 1
            if self.submission.result == JudgeStatus.ACCEPTED:
                problem.accepted_number += 1
            problem_info = problem.statistic_info
            # 统计信息字典中的结果字段下PENDING(=6) + 1 --> JUDGING(=7)
            problem_info[result] = problem_info.get(result, 0) + 1
            problem.save(update_fields=["accepted_number", "submission_number", "statistic_info"])

            # 更新用户配置
            user = User.objects.select_for_update().get(id=self.submission.user_id)
            user_profile = user.userprofile
            # 提交数+1
            user_profile.submission_number += 1
            if problem.rule_type == ProblemRuleType.ACM:
                # 查找出之前用户对该题的AC状态
                acm_problems_status = user_profile.acm_problems_status.get("problems", {})
                # 显示的problems_id不在字典类型acm_problems_status，这种情况是用户首次提交该题的信息，非rejudge，后者有专门的方法处理或者走下面的elif
                if problem_id not in acm_problems_status:
                    # 新构建acm_problems_status类型，并保存
                    acm_problems_status[problem_id] = {"status": self.submission.result, "_id": self.problem._id}
                    # 本次通过，AC+1
                    if self.submission.result == JudgeStatus.ACCEPTED:
                        user_profile.accepted_number += 1
                # 之前的状态为not AC
                elif acm_problems_status[problem_id]["status"] != JudgeStatus.ACCEPTED:
                    # 更新本次的提交状态
                    acm_problems_status[problem_id]["status"] = self.submission.result
                    # 如果AC就+1
                    if self.submission.result == JudgeStatus.ACCEPTED:
                        user_profile.accepted_number += 1
                # 状态不存在而又没AC，赋值会给自身，不做更改， 更新数据库
                user_profile.acm_problems_status["problems"] = acm_problems_status
                user_profile.save(update_fields=["submission_number", "accepted_number", "acm_problems_status"])

            else:
                # 取到之前的OI状态和本次OI的得分
                oi_problems_status = user_profile.oi_problems_status.get("problems", {})
                score = self.submission.statistic_info["score"]
                if problem_id not in oi_problems_status:
                    # 之前没做过这道题，首次提交，分数就是本次所得的分数
                    user_profile.add_score(score)
                    # 新构建oi_problems_status，将该题目的状态信息以字典类型存放
                    oi_problems_status[problem_id] = {"status": self.submission.result,
                                                      "_id": self.problem._id,
                                                      "score": score}
                    # 如果AC，AC+1
                    if self.submission.result == JudgeStatus.ACCEPTED:
                        user_profile.accepted_number += 1
                elif oi_problems_status[problem_id]["status"] != JudgeStatus.ACCEPTED:
                    # 注意：计算总分时候，应该先减掉上一次该题所得的分数，然后再加上本次所得的分数
                    user_profile.add_score(this_time_score=score,
                                           last_time_score=oi_problems_status[problem_id]["score"])
                    # 配置该题目的分数和答题状态，并保存
                    oi_problems_status[problem_id]["score"] = score
                    oi_problems_status[problem_id]["status"] = self.submission.result
                    if self.submission.result == JudgeStatus.ACCEPTED:
                        user_profile.accepted_number += 1
                user_profile.oi_problems_status["problems"] = oi_problems_status
                user_profile.save(update_fields=["submission_number", "accepted_number", "oi_problems_status"])

    def update_contest_problem_status(self):
        # 更新比赛题目答题状态
        with transaction.atomic():
            # 获取参赛用户、配置、提交的问题
            user = User.objects.select_for_update().get(id=self.submission.user_id)
            user_profile = user.userprofile
            problem_id = str(self.problem.id)
            if self.contest.rule_type == ContestRuleType.ACM:
                # 获取上一次用户对该题的AC状态，才做都是在字典里面进行
                contest_problems_status = user_profile.acm_problems_status.get("contest_problems", {})
                if problem_id not in contest_problems_status:
                    # 初次答题构建新的status
                    contest_problems_status[problem_id] = {"status": self.submission.result, "_id": self.problem._id}
                elif contest_problems_status[problem_id]["status"] != JudgeStatus.ACCEPTED:
                    # not AC，直接赋值新状态
                    contest_problems_status[problem_id]["status"] = self.submission.result
                else:
                    # 如果已AC， 直接跳过 不计入任何计数器
                    return
                user_profile.acm_problems_status["contest_problems"] = contest_problems_status
                user_profile.save(update_fields=["acm_problems_status"])

            elif self.contest.rule_type == ContestRuleType.OI:
                # 获取上一次的题目答题状态和当前分数
                contest_problems_status = user_profile.oi_problems_status.get("contest_problems", {})
                score = self.submission.statistic_info["score"]
                if problem_id not in contest_problems_status:
                    # 初次答题构建新的status
                    contest_problems_status[problem_id] = {"status": self.submission.result,
                                                           "_id": self.problem._id,
                                                           "score": score}
                else:
                    # 否则就是已经对该题提交过答案，跟新信息
                    contest_problems_status[problem_id]["score"] = score
                    contest_problems_status[problem_id]["status"] = self.submission.result
                user_profile.oi_problems_status["contest_problems"] = contest_problems_status
                user_profile.save(update_fields=["oi_problems_status"])

            # 如果不是以ACM或者OI参加的比赛，用户仅仅是想AC这道题，根据contest_id和problem.id查找出该比赛题目
            problem = Problem.objects.select_for_update().get(contest_id=self.contest_id, id=self.problem.id)
            result = str(self.submission.result)
            problem_info = problem.statistic_info
            # 统计信息中的PENDING(=6)+1 -->JUDGING
            problem_info[result] = problem_info.get(result, 0) + 1
            # 提交数目+1
            problem.submission_number += 1
            if self.submission.result == JudgeStatus.ACCEPTED:
                problem.accepted_number += 1
            problem.save(update_fields=["submission_number", "accepted_number", "statistic_info"])

    def update_contest_rank(self):
        # 如果比赛是OI或者比赛实时排名为true，先删除缓存的数据，重新按照指定的比赛规则进行排序
        if self.contest.rule_type == ContestRuleType.OI or self.contest.real_time_rank:
            cache.delete(f"{CacheKey.contest_rank_cache}:{self.contest.id}")
        with transaction.atomic():
            if self.contest.rule_type == ContestRuleType.ACM:
                acm_rank, _ = ACMContestRank.objects.select_for_update(). \
                    get_or_create(user_id=self.submission.user_id, contest=self.contest)
                # 传入查找到的acm_rank，里面有accepted_number、total_time、submission_info
                self._update_acm_contest_rank(acm_rank)
            else:
                oi_rank, _ = OIContestRank.objects.select_for_update(). \
                    get_or_create(user_id=self.submission.user_id, contest=self.contest)
                # 传入查找到的oi_rank，里面有total_score、submission_info
                self._update_oi_contest_rank(oi_rank)

    def _update_acm_contest_rank(self, rank):
        # 获取本题的ID
        info = rank.submission_info.get(str(self.submission.problem_id))
        # 因前面更改过，这里需要重新获取
        problem = Problem.objects.get(contest_id=self.contest_id, id=self.problem.id)

        # 首先此题提交过，Info非空，即非第一次提交
        if info:
            # 如果本题没被AC，返回.否则继续
            if info["is_ac"]:
                return

            # rank的提交数+1
            rank.submission_number += 1
            if self.submission.result == JudgeStatus.ACCEPTED:
                # 本题被AC，配置ac题目为true，获取时间并根据规则(罚时20min)计算排名总用时
                rank.accepted_number += 1
                info["is_ac"] = True
                info["ac_time"] = (self.submission.create_time - self.contest.start_time).total_seconds()
                rank.total_time += info["ac_time"] + info["error_number"] * 20 * 60

                # 首次被AC
                if problem.accepted_number == 1:
                    info["is_first_ac"] = True
            # 不是编译错误，就是答案错误，提交错误数+1
            elif self.submission.result != JudgeStatus.COMPILE_ERROR:
                info["error_number"] += 1

        # 第一次提交，一般从这里开始
        else:
            rank.submission_number += 1
            # 初始Info信息
            info = {"is_ac": False, "ac_time": 0, "error_number": 0, "is_first_ac": False}
            if self.submission.result == JudgeStatus.ACCEPTED:
                rank.accepted_number += 1
                info["is_ac"] = True
                info["ac_time"] = (self.submission.create_time - self.contest.start_time).total_seconds()
                # 首次计时不加罚时
                rank.total_time += info["ac_time"]

                if problem.accepted_number == 1:
                    info["is_first_ac"] = True

            # 否则非编译错误就是答案错误
            elif self.submission.result != JudgeStatus.COMPILE_ERROR:
                info["error_number"] = 1
        # 更新并保存对应比赛的题目的提交信息
        rank.submission_info[str(self.submission.problem_id)] = info
        rank.save()

    def _update_oi_contest_rank(self, rank):
        # 获取题目ID，当前统计信息里面的分数，上一次该题的得分
        problem_id = str(self.submission.problem_id)
        current_score = self.submission.statistic_info["score"]
        last_score = rank.submission_info.get(problem_id)
        # 非第一次做题
        if last_score:
            rank.total_score = rank.total_score - last_score + current_score
        # 首次做该题
        else:
            rank.total_score = rank.total_score + current_score
        # 更新并保存对应比赛的题目的提交信息
        rank.submission_info[problem_id] = current_score
        rank.save()

