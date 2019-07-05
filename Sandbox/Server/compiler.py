import _judger
import json
import os

from config import COMPILER_LOG_PATH, COMPILER_USER_UID, COMPILER_GROUP_GID
from exception import CompileError

#编译器类
class Compiler(object):
    def compile(self, compile_config, src_path, output_dir):
        #通过编译配置获取编译命令
        command = compile_config["compile_command"]
        #拼接配置执行文件路径，output_dir就是submission_dir
        exe_path = os.path.join(output_dir, compile_config["exe_name"])
        #编译命令格式化，格式化路径在配置文件里面
        command = command.format(src_path=src_path, exe_dir=output_dir, exe_path=exe_path)
        #编译完成文件输出路径
        compiler_out = os.path.join(output_dir, "compiler.out")
        #按照空格将编译命令分割成块
        _command = command.split(" ")

        #转到编译输出文件路径
        os.chdir(output_dir)
        #调用评判机Judger模块进行编译，也就是说编译也是要经过评判机的，因为编译本身就是一个执行文件的过程，
        #用户的可执行代码在另外一个文件judge-client中处理。
        result = _judger.run(max_cpu_time=compile_config["max_cpu_time"],
                             max_real_time=compile_config["max_real_time"],
                             max_memory=compile_config["max_memory"],
                             max_stack=128 * 1024 * 1024,
                             max_output_size=1024 * 1024,
                             max_process_number=_judger.UNLIMITED, #-1
                             #编译命令空格分割的第一个文件,这里的exe_path已经更改成编译器的路径，不是上面的exe_path了
                             exe_path=_command[0],
                             # 使用为文件/dev/null是最好的，但在某些系统中，这将调用ioctl system call
                             input_path=src_path,
                             output_path=compiler_out,
                             error_path=compiler_out,
                             #从第一个开始读取参数
                             args=_command[1::], 
                             #设置运行环境
                             env=["PATH=" + os.getenv("PATH")],
                             log_path=COMPILER_LOG_PATH,
                             #这里不设置安全计算规则是因为编译的执行文件第一个都是系统的编译器，本身运行就对系统无害
                             #唯一出现的可能就是编译错误
                             seccomp_rule_name=None,
                             uid=COMPILER_USER_UID,
                             gid=COMPILER_GROUP_GID)
        
        # 如果编译异常，结果不相等，并且编译输出文件存在，那么打开文件并设置编译错误信息，最后删除此文件
        # 只会出现编译错误，不可能出现其他错误。
        if result["result"] != _judger.RESULT_SUCCESS:
            if os.path.exists(compiler_out):
                with open(compiler_out, encoding="utf-8") as f:
                    error = f.read().strip()
                    os.remove(compiler_out)
                    # 错误不空，抛出错误
                    if error:
                        raise CompileError(error)
            #抛出编译错误信息
            raise CompileError("Compiler runtime error, info: %s" % json.dumps(result))
        else:
            #编译通过，删除编译输出文件，返回编译用户的代码后执行文件路径
            os.remove(compiler_out)
            return exe_path
