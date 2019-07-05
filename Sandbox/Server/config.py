import os
import pwd

import grp

#常量参数配置

#评判机基础工作空间
JUDGER_WORKSPACE_BASE = "/judger/run"

# 日志基础路径
LOG_BASE = "/log"

# 编译器日志路径
COMPILER_LOG_PATH = os.path.join(LOG_BASE, "compile.log")

#评判机运行日志路径
JUDGER_RUN_LOG_PATH = os.path.join(LOG_BASE, "judger.log")

#服务器日志路径
SERVER_LOG_PATH = os.path.join(LOG_BASE, "judge_server.log")

#根据用户名设置运行用户和组ID
RUN_USER_UID = pwd.getpwnam("code").pw_uid
RUN_GROUP_GID = grp.getgrnam("code").gr_gid

#根据用户名设置编译器的用户和组ID
COMPILER_USER_UID = pwd.getpwnam("compiler").pw_uid
COMPILER_GROUP_GID = grp.getgrnam("compiler").gr_gid

#根据用户名设置特殊用户ID
SPJ_USER_UID = pwd.getpwnam("spj").pw_uid
SPJ_GROUP_GID = grp.getgrnam("spj").gr_gid

#注意：这几个路径是我在写entrypoint.sh的时候已经创建好的了，除了TEST_CASE_DIR文件路径。
#测试用例路径
TEST_CASE_DIR = "/test_case"
#特殊评判源码路径
SPJ_SRC_DIR = "/judger/spj"
#特殊评判执行文件路径
SPJ_EXE_DIR = "/judger/spj"
