import _judger
import hashlib
import json
import os

#本例使用python中的多进程线程池模块，例如里面包含的方法：apply_async(_run, (self, test_case_file_id))
from multiprocessing import Pool

import psutil

#可执行文件的运行和评判结果的对比在这里进行
# 导入常量配置信息
from config import TEST_CASE_DIR, JUDGER_RUN_LOG_PATH, RUN_GROUP_GID, RUN_USER_UID, SPJ_EXE_DIR, SPJ_USER_UID, SPJ_GROUP_GID, RUN_GROUP_GID
from exception import JudgeClientError

# 设置特殊评判常量
SPJ_WA = 1
SPJ_AC = 0
SPJ_ERROR = -1

# 评判一个测试用例，其中instance（实例）就是值类JudgeClient的一个实例
def _run(instance, test_case_file_id):
    return instance._judge_one(test_case_file_id)


class JudgeClient(object):
    #构造函数初始化运行参数，这些参数都是前台传过来的
    def __init__(self, run_config, exe_path, max_cpu_time, max_memory, test_case_id,
                 submission_dir, spj_version, spj_config, output=False):
        #_run_config是一个json的数据
        self._run_config = run_config
        self._exe_path = exe_path
        self._max_cpu_time = max_cpu_time
        self._max_memory = max_memory
        #最大真实时间限定为最大CPU时间的3倍
        self._max_real_time = self._max_cpu_time * 3
        self._test_case_id = test_case_id
        #因为每个测试用例不同的，这个test_case_id也应该有用户传进，然后拼接在一起形成一个新的文件路径
        self._test_case_dir = os.path.join(TEST_CASE_DIR, test_case_id)
        #_submission_dir=submission_dir=/judger/run/submission_id/
        self._submission_dir = submission_dir
        #实例化一个多进程池，里面的进程数根据系统CPU逻辑个数开启
        self._pool = Pool(processes=psutil.cpu_count())
        #加载测试用例信息
        self._test_case_info = self._load_test_case_info()

        self._spj_version = spj_version
        self._spj_config = spj_config
        self._output = output

        #如果特殊评判版本和配置不为空，则执行特殊评判
        #拼接配置特殊评判的执行文件的路径，注意这里是config的，非compile
        if self._spj_version and self._spj_config:
            self._spj_exe = os.path.join(SPJ_EXE_DIR,
                                         self._spj_config["exe_name"].format(spj_version=self._spj_version))
            #到SPJ_EXE_DIR去找，如果特殊评判执行文件不存在，则抛出异常
            if not os.path.exists(self._spj_exe):
                raise JudgeClientError("spj exe not found")

    # 注意，单杠'_'开头的不是表示私有的，双杠开头的才是表示私有的。
    # 加载测试用例信息，使用json加载，被构造函数_test_case_info调用
    def _load_test_case_info(self):
        try:
            with open(os.path.join(self._test_case_dir, "info")) as f:
                return json.load(f)
        except IOError:
            raise JudgeClientError("Test case not found")
        except ValueError:
            raise JudgeClientError("Bad test case config")

    # 获取测试用例文件信息，被比较输出函数_compare_output调用
    def _get_test_case_file_info(self, test_case_file_id):
        return self._test_case_info["test_cases"][test_case_file_id]

    # 比较运行结果与标准的结果是否一致，被运行单个测试评判函数_judge_one中调用
    def _compare_output(self, test_case_file_id):
        user_output_file = os.path.join(self._submission_dir, str(test_case_file_id) + ".out")
        with open(user_output_file, "rb") as f:
            content = f.read()
        #文件内容去掉尾随空格之后提取摘要信息
        output_md5 = hashlib.md5(content.rstrip()).hexdigest()
        #将输出在.out文件中的信息使用摘要算法加密的结果与info文件中的已删除尾随空字符的输出文件的md5进行比较
        result = output_md5 == self._get_test_case_file_info(test_case_file_id)["stripped_output_md5"]
        # 返回的一个是字符串和一个布尔值
        return output_md5, result

    # 特殊评判运行特殊测试用例
    def _spj(self, in_file_path, user_out_file_path):
        # 更改文件_submission_dir的所有者，设置所有者的ID为SPJ_USER_UID，用户组为0
        os.chown(self._submission_dir, SPJ_USER_UID, 0)
        os.chown(user_out_file_path, SPJ_USER_UID, 0)
        #更改文件或目录的权限，）o740表示：拥有者有全部权限(权限掩码)和组用户有读权限。
        os.chmod(user_out_file_path, 0o740)
        #规格化执行命令，这里也是config的，不是compile，format对应三个参数
        command = self._spj_config["command"].format(exe_path=self._spj_exe,
                                                     in_file_path=in_file_path,
                                                     user_out_file_path=user_out_file_path).split(" ")
        
        #设置评测规则,默认是c_cpp，这里更改成seccomp_rule,因为默认是先被系统编译器调用，
        # 而系统编译器不会干坏事，使用c_cpp白名单即可，因为是特殊评判，所以这里的系统资源相对开的大一点
        seccomp_rule_name = self._spj_config["seccomp_rule"]
        result = _judger.run(max_cpu_time=self._max_cpu_time * 3,
                             max_real_time=self._max_cpu_time * 9,
                             max_memory=self._max_memory * 3,
                             max_stack=128 * 1024 * 1024,
                             max_output_size=1024 * 1024 * 1024,
                             #默认开启的进程数是不限制的
                             max_process_number=_judger.UNLIMITED,
                             exe_path=command[0],
                             input_path=in_file_path,
                             output_path="/tmp/spj.out",
                             error_path="/tmp/spj.out",
                             args=command[1::],
                             env=["PATH=" + os.environ.get("PATH", "")],
                             log_path=JUDGER_RUN_LOG_PATH,
                             seccomp_rule_name=seccomp_rule_name,
                             uid=SPJ_USER_UID,
                             gid=SPJ_GROUP_GID)

        #两种情况：1、通过判题机，返回成功(RESULT_SUCCESS=0)
        #         2、运行时出错exit_code=4，且退出码在（特殊评判答案错误1(系统对应的是RESULT_CPU_TIME_LIMIT_EXCEEDED)，
        #         特殊评判错误RESULT_WRONG_ANSWER=-1）中，且正常退出0
        if result["result"] == _judger.RESULT_SUCCESS or \
                (result["result"] == _judger.RESULT_RUNTIME_ERROR and
                 result["exit_code"] in [SPJ_WA, SPJ_ERROR] and result["signal"] == 0):
            #返回结果：-1，0，1，4
            return result["exit_code"]
        else:
            #RESULT_CPU_TIME_LIMIT_EXCEEDED=-1
            return SPJ_ERROR

    # 测试单个用例
    def _judge_one(self, test_case_file_id):
        # 找到测试用例信息
        test_case_info = self._get_test_case_file_info(test_case_file_id)
        # 输入文件路径，input_name:1.in，那么路径就是/test_case/1.in
        in_file = os.path.join(self._test_case_dir, test_case_info["input_name"])
        # 输出文件路径:user_output_file=_submission_dir+test_case_file_id.out=/judger/run/submission_id/test_case_file_id.out
        user_output_file = os.path.join(self._submission_dir, test_case_file_id + ".out")

        #先格式化执行文件命令并按照空格分割成块，exe_path对应c和c++，exe_dir和max_memory对应java
        command = self._run_config["command"].format(exe_path=self._exe_path, exe_dir=os.path.dirname(self._exe_path),
                                                     max_memory=int(self._max_memory / 1024)).split(" ")
        
        #设置运行环境：系统的路径拼接上运行配置的路径
        env = ["PATH=" + os.environ.get("PATH", "")] + self._run_config.get("env", [])

        run_result = _judger.run(max_cpu_time=self._max_cpu_time,
                                 max_real_time=self._max_real_time,
                                 max_memory=self._max_memory,
                                 max_stack=128 * 1024 * 1024,
                                 # 根据配置文件要求，比较选取最大的那个
                                 max_output_size=max(test_case_info.get("output_size", 0) * 2, 1024 * 1024 * 16),
                                 max_process_number=_judger.UNLIMITED,
                                 #这里执行的是用户的编译好的代码
                                 exe_path=command[0],
                                 input_path=in_file,
                                 output_path=user_output_file,
                                 error_path=user_output_file,
                                 #从第1个参数开始，直至最后
                                 args=command[1::],
                                 env=env,
                                 log_path=JUDGER_RUN_LOG_PATH,
                                 #这里需要设置黑名单安全计算规则
                                 seccomp_rule_name=self._run_config["seccomp_rule"],
                                 uid=RUN_USER_UID,
                                 gid=RUN_GROUP_GID,
                                 #由于java比较特殊，所以只设置其运行内存为检查，查出了就报错
                                 memory_limit_check_only=self._run_config.get("memory_limit_check_only", 0))
        
        #这个是judge.run():返回的数据：例如{'cpu_time': 0, 'signal': 0, 'memory': 4554752, 'exit_code': 0, 'result': 0, 'error': 0, 'real_time': 2}
        #因为run_result里面的json数据是没有对应的test_cast这么一条数据的，但是可以添加进去，那么运行的结果就有对应的数据了
        #因为是for循环进行的调用的，所以可以每次评判完成时候添加这几个数据，例如下面的outp_md5和output因为还没有生成，需要
        #进行测试结果比较会后才会返回，所以这里就先将它们赋值为None，等返回对应的之后再进行相应的覆盖即可。
        #run_result是一个json的数据，里面的参数就是运行的结果
        run_result["test_case"] = test_case_file_id

        # if progress exited normally, then we should check output result
        # 如果进程正常退出，那么然后我们就应该检查输出结果
        run_result["output_md5"] = None
        run_result["output"] = None
        
        # 如果评测结果通过，仅仅运行没有错误，还要将结果进行比较
        if run_result["result"] == _judger.RESULT_SUCCESS:
            #调用_load_test_case_info加载测试用例信息，当spj为真，就进行spj评判，否者比较结果
            if self._test_case_info.get("spj"):
                #如果特殊测试配值为0或者版本号没设置，抛出相应的异常
                if not self._spj_config or not self._spj_version:
                    raise JudgeClientError("spj_config or spj_version not set")

                #意思就是通过正常的测试之后，如果需要进行特殊评判的话，就进入特殊评判，所以输入文
                # 件路径还是从本目录传进去，等到调用_spj()函数之后，在做相应的用户和用户组和权限的更改。
                spj_result = self._spj(in_file_path=in_file, user_out_file_path=user_output_file)

                #特殊评判答案错误-1
                if spj_result == SPJ_WA:
                    run_result["result"] = _judger.RESULT_WRONG_ANSWER
                #返回1(这里不设RESULT_CPU_TIME_LIMIT_EXCEEDED)，因为不用，只是然后用户知道是系统错误就行
                elif spj_result == SPJ_ERROR:
                    run_result["result"] = _judger.RESULT_SYSTEM_ERROR
                    run_result["error"] = _judger.ERROR_SPJ_ERROR
            else:
                #否则就不用进行特殊测试，直接比较结果的md5值，判断评测结果，返回之后覆盖None
                run_result["output_md5"], is_ac = self._compare_output(test_case_file_id)
                # -1 为错误答案
                # is_ac为假，WA并不便是运算不通过，是得出的结果和测试数据的不同
                if not is_ac:
                    run_result["result"] = _judger.RESULT_WRONG_ANSWER
        
        #输出文件不为空，就设置运行的结果为文件的内容
        if self._output:
            try:
                with open(user_output_file, "r", encoding="utf-8") as f:
                    #覆盖之前的None
                    run_result["output"] = f.read()
            except Exception:
                pass

        return run_result

    def run(self):
        tmp_result = []
        result = []
        #去调用_load_test_case_info()加载info文件的信息，就知道有多少个测试用例，例如本例中只有一个test_case，
        # '_'表示即使没有1，2，3这样的编号，也照样进行遍历
        for test_case_file_id, _ in self._test_case_info["test_cases"].items():
            #循环添加到临时的结果列表中，调用进程池实例的apply_async函数，按照测试用例文件ID运行
            #apply_async用于传递不定参数，是非阻塞且支持结果返回进行回调，返回一个列表
            #函数原型：apply_async(func[, args=()[, kwds={}[, callback=None]]])
            tmp_result.append(self._pool.apply_async(_run, (self, test_case_file_id)))
        # 关闭进程池，表示不能在往进程池中添加进程
        self._pool.close()
        # 等待进程池中的所有进程执行完毕以后再继续往下运行，通常用于进程间的同步，join方法必须在close或terminate之后使用
        self._pool.join()
        for item in tmp_result:
            # 结果就是返回pool中所有进程的值的对象（注意是对象，不是值本身）。
            # 当调用get()函数的时候，会抛出异常，因为无论是对或是错，我都要返回的数据，最后由json解析
            # # http://stackoverflow.com/questions/22094852/how-to-catch-exceptions-in-workers-in-multiprocessing
            result.append(item.get())
        #最后返回结果到服务器，就是返回每个测试的结果堆在一起的一个列表
        return result

    def __getstate__(self):
        # http://stackoverflow.com/questions/25382455/python-notimplementederror-pool-objects-cannot-be-passed-between-processes
        # 在使用pickle进行数据持久化的时候（要返回评判的结果：一个结果列表，而结果又在类里面，要打破类的封装就要使用pickle），_pool本身也是
        # 一个实例化变量，_pool对象不能被pickle，所以就要实现__getstate__()方法，先删除_poor实例变量，再进行pickle。
        self_dict = self.__dict__.copy()
        del self_dict["_pool"]
        return self_dict
