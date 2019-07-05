# 服务器异常类处理
class JudgeServerException(Exception):
    def __init__(self, message):
        super().__init__()
        self.message = message

#编译异常处理类
class CompileError(JudgeServerException):
    pass

#特殊评判编译异常处理类
class SPJCompileError(JudgeServerException):
    pass

# 令牌验证失败处理类
class TokenVerificationFailed(JudgeServerException):
    pass

#客户端错误处理类
class JudgeClientError(JudgeServerException):
    pass

#服务异常处理类
class JudgeServiceError(JudgeServerException):
    pass
