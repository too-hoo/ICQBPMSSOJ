import _judger
import hashlib
import logging
import os
import socket

import psutil

from config import SERVER_LOG_PATH
from exception import JudgeClientError

# 服务器工具类
# 日志工具类：配置logging基本的设置
# 获得日志对象
logger = logging.getLogger(__name__)
#设置服务器的日志路径，用于将日志写到文件中
handler = logging.FileHandler(SERVER_LOG_PATH)
#时间+日志级别+日志信息
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
#设置文件输出的格式
handler.setFormatter(formatter)
#日志按照设置的格式写到日志文件中
logger.addHandler(handler)
#设置日志的信息等级
logger.setLevel(logging.WARNING)

#服务器信息工具，使用psutil更加方便的获取到系统的信息
def server_info():
    ver = _judger.VERSION
    return {"hostname": socket.gethostname(),
            "cpu": psutil.cpu_percent(),
            "cpu_core": psutil.cpu_count(),
            "memory": psutil.virtual_memory().percent,
            "judger_version": ".".join([str((ver >> 16) & 0xff), str((ver >> 8) & 0xff), str(ver & 0xff)])}


#获取系统的token，这个token在使用docker—compose部署的时候已经制定：no_body_know,在这里进行加密，
# 加密过后的token有server.py进行调用
def get_token():
    token = os.environ.get("TOKEN")
    if token:
        return token
    else:
        raise JudgeClientError("env 'TOKEN' not found")

#使用摘要算法sha256生成令牌
token = hashlib.sha256(get_token().encode("utf-8")).hexdigest()
