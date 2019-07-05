import json
import os
import shutil
import uuid

#基于一个小型的flask的应用
#首先导入flask类。这个类的实例将会是我们的 WSGI 应用程序。和一些其他的模块
from flask import Flask, request, Response

from compiler import Compiler
from config import JUDGER_WORKSPACE_BASE, SPJ_SRC_DIR, SPJ_EXE_DIR, COMPILER_USER_UID, SPJ_USER_UID, RUN_USER_UID, RUN_GROUP_GID
from exception import TokenVerificationFailed, CompileError, SPJCompileError, JudgeClientError
from judge_client import JudgeClient
from utils import server_info, logger, token


#创建app应用实例,__name__是python预定义变量，被设置为使用本模块.'__main__'会找到这里。
app = Flask(__name__)

#当系统获取的Judger_debug字符串为1时候，调试模式才是True，否则为False
DEBUG = os.environ.get("judger_debug") == "1"
app.debug = DEBUG


#初始化提交环境，
class InitSubmissionEnv(object):
    
    #以下的三个函数（__init__， __enter__，__exit__）是with...as的执行机制
    # 在下面的with...as函数中被调用，
    #根据提交的ID初始化工作空间路径
    def __init__(self, judger_workspace, submission_id):
        self.path = os.path.join(judger_workspace, submission_id)

    #紧接着执行with的入口第一个函数，创建对应的文件夹，更改目录所有者和权限，此函数被调用之后先
    # 返回下面with...as主函数继续执行
    def __enter__(self):
        try:
            #创建，更改用户和组ID，赋予所有者所有权限，组用户和其他用户执行权限
            os.mkdir(self.path)
            os.chown(self.path, COMPILER_USER_UID, RUN_GROUP_GID)
            os.chmod(self.path, 0o711)
        except Exception as e:
            logger.exception(e)
            raise JudgeClientError("failed to create runtime dir")
        return self.path
    
    #with...as的最后操作退出，非调试模式下并删除工作空间路径文件夹
    def __exit__(self, exc_type, exc_val, exc_tb):
        if not DEBUG:
            try:
                shutil.rmtree(self.path)
            except Exception as e:
                logger.exception(e)
                raise JudgeClientError("failed to clean runtime dir")

#根据请求：/ping,/judge,/compile_spj三个不同的映射来进行选择
class JudgeServer:
    #如果是用户请求ping一下，就返回系统的信息
    @classmethod
    def ping(cls):
        data = server_info()
        data["action"] = "pong"
        return data


    # 后台传入：评判语言，源码，max_cpu_time, max_memory和测试用例ID等参数
    # 注意区别普通评判源代码src和特殊评判源代码
    # 传入的language_config,spj_version,spj_config,spj_compile_config等参数的格式都是json格式的
    @classmethod
    def judge(cls, language_config, src, max_cpu_time, max_memory, test_case_id,
              spj_version=None, spj_config=None, spj_compile_config=None, spj_src=None, output=False):
        # 初始化
        # 根据语言配置，获得language_config里面的compile下的编译参数配置：编译源文件名称，执行文件名称，最大CPU使用时间，评判实际用时，最大内存，编译命令
        compile_config = language_config.get("compile")
        # 根据语言配置，获得language_config里面的run下的运行参数配置：执行文件的路径，安全运行模式名称，运行环境
        run_config = language_config["run"]
        # 使用python内置模块uuid在此生成对应的提交ID
        submission_id = uuid.uuid4().hex

        # 如果特殊评判版本和评判配置不为空,就要进行特殊评判，否则才执行下面的操作
        if spj_version and spj_config:
            # 拼接设置特殊评判执行文件的路径
            spj_exe_path = os.path.join(SPJ_EXE_DIR, spj_config["exe_name"].format(spj_version=spj_version))
            # 如果特殊评判之前没有被编译成功，找不到可执行文件，日志抛出警告，然后先编译
            if not os.path.isfile(spj_exe_path):
                logger.warning("%s does not exists, spj src will be recompiled")
                #类本身调用编译方法进行编译
                cls.compile_spj(spj_version=spj_version, src=spj_src,
                                spj_compile_config=spj_compile_config)
        
        #特殊评判编译成功，或者不用执行特殊评判之后，执行正常的普通代码评判
        #要注意with...as的运行机制的好处，和执行过程
        # 返回上面调用机制，先将工作空间拼接好，然后赋值给submission_dir(提交文件目录)
        #初始化提交源码文件的环境:submission_dir=/judger/run/submission_id/
        with InitSubmissionEnv(JUDGER_WORKSPACE_BASE, submission_id=str(submission_id)) as submission_dir:
            #如果编译配置非空，说明需要编译源码，否则说明源码已经被编译好了，设置运行源码
            if compile_config:
                #每种语言的submission_dir都是不同放入，c,c++为main.c等
                src_path = os.path.join(submission_dir, compile_config["src_name"])

                # 将普通评判代码写入到文件，并更改文件的归属用户ID和组ID
                with open(src_path, "w", encoding="utf-8") as f:
                    f.write(src)
                os.chown(src_path, COMPILER_USER_UID, 0)
                os.chmod(src_path, 0o400)

                # 编译用户提交的源代码并返回可执行文件路径
                exe_path = Compiler().compile(compile_config=compile_config,
                                              src_path=src_path,
                                              output_dir=submission_dir)
                try:
                    #编译后Java的可执行文件是SOME_PATH/Main，但是真实的文件是SOME_PATH/Main.class
                    #可以先忽略这个
                    os.chown(exe_path, RUN_USER_UID, 0)
                    os.chmod(exe_path, 0o500)
                except Exception:
                    pass
            else:
                #注意：这里的exe_path不是上面编译器返回的执行文件路径，而是运行配置里面新拼接的执行文件路径，这个可能容易弄混
                #拼接设置运行（非编译）可执行文件的路径，打开并向里面写入源码
                exe_path = os.path.join(submission_dir, run_config["exe_name"])
                with open(exe_path, "w", encoding="utf-8") as f:
                    f.write(src)

            #运行用户提交的代码,run是一个json类型的数据
            judge_client = JudgeClient(run_config=language_config["run"],
                                        #无论用户传过来的文件是源文件、特殊评判文件还是可执行文件，如果是源文件和特殊评判文件，那我们
                                        # 就帮他编译一下，反正到这里，都是可以执行的文件就行了。
                                       exe_path=exe_path,
                                       max_cpu_time=max_cpu_time,
                                       max_memory=max_memory,
                                       test_case_id=str(test_case_id),
                                       submission_dir=submission_dir,
                                       spj_version=spj_version,
                                       spj_config=spj_config,
                                       output=output)
            run_result = judge_client.run()

            return run_result

    # 编译特殊评判源文件，需要传入三个参数，此时传入的是特殊评判的源代码
    # 完成后返回字符串“success”
    @classmethod
    def compile_spj(cls, spj_version, src, spj_compile_config):
        # format格式化特殊评判版本，也即是源文件和可执行文件的名字，目标位置在language
        spj_compile_config["src_name"] = spj_compile_config["src_name"].format(spj_version=spj_version)
        spj_compile_config["exe_name"] = spj_compile_config["exe_name"].format(spj_version=spj_version)
        #拼接设置特殊评判的源文件路径，这里是compile，非run
        spj_src_path = os.path.join(SPJ_SRC_DIR, spj_compile_config["src_name"])

        #如果特殊评判源代码不存在，然后将源代码写入到文件里面
        #这个设置的是特殊评判的源代码的路径的：spj_src_path
        if not os.path.exists(spj_src_path):
            with open(spj_src_path, "w", encoding="utf-8") as f:
                f.write(src)
            # 写入之后更改源代码的所有者，使用root才可以，0表示更改的用户组
            os.chown(spj_src_path, COMPILER_USER_UID, 0)
            #更改文件的权限，）0o400表示拥有者具有读写权限
            os.chmod(spj_src_path, 0o400)

        try:
            #编译传入的特殊评判源文件，并输出编译好的可执行文件到SPJ_EXE_DIR，以供运行使用
            exe_path = Compiler().compile(compile_config=spj_compile_config,
                                          src_path=spj_src_path,
                                          output_dir=SPJ_EXE_DIR)
            #更改执行文件的用户ID和组ID，所有者对文件的权限为0o500:拥有者具有读写和执行的权利
            os.chown(exe_path, SPJ_USER_UID, 0)
            os.chmod(exe_path, 0o500)
        # 出错的话就将普通的编译错误转换成特殊评判编译错误
        except CompileError as e:
            raise SPJCompileError(e.message)
        return "success"

#建立路由，通过路由可以执行其覆盖的方法，可以多个路由指向同一个方法。
#使用 route() 装饰器告诉 Flask 什么样的URL 能触发我们的函数
#这个函数的名字也在生成 URL 时被特定的函数采用，返回我们想要显示在用户浏览器中的信息。
#请求使用POST方法
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=["POST"])
def server(path):
    #设置多个可能的路由请求
    if path in ("judge", "ping", "compile_spj"):
        _token = request.headers.get("X-Judge-Server-Token")
        try:
            #如果令牌出错就抛出异常，否者执行try，获取数据
            if _token != token:
                raise TokenVerificationFailed("invalid token")
            try:
                data = request.json
            except Exception:
                data = {}
            #**将data的json格式数据转换成a=b的形式
            ret = {"err": None, "data": getattr(JudgeServer, path)(**data)}
        except (CompileError, TokenVerificationFailed, SPJCompileError, JudgeClientError) as e:
            logger.exception(e)
            ret = {"err": e.__class__.__name__, "data": e.message}
        except Exception as e:
            logger.exception(e)
            ret = {"err": "JudgeClientError", "data": e.__class__.__name__ + " :" + str(e)}
    else:
        ret = {"err": "InvalidRequest", "data": "404"}

    #通过json的dumps的模块可以把特定的对象序列化处理为字符串
    return Response(json.dumps(ret), mimetype='application/json')


#调试模式非空，设置python日志的信息为调试开启
if DEBUG:
    logger.info("DEBUG=ON")

# 用 run() 函数来让应用运行在本地服务器上。 其中 if __name__ == '__main__': 确保服务器只会在该脚本被 Python 
# 解释器直接执行的时候才会运行，而不是作为模块导入的时候。
# gunicorn -w 4 -b 0.0.0.0:8080 server:app
if __name__ == "__main__":
    #根据系统获取的Judger_debug信息来确定是否启用了调试支持，服务器会在代码修改后自动重新载入。
    app.run(debug=DEBUG)
