#ifndef JUDGER_RUNNER_H
#define JUDGER_RUNNER_H

#include <sys/types.h>  // 中文名称为基本系统数据类型，此头文件还包含适当时应使用的多个基本派生类型
#include <stdio.h>

// (ver >> 16) & 0xff, (ver >> 8) & 0xff, ver & 0xff  -> real version
#define VERSION 0x020101

#define UNLIMITED -1  // 没有限制为-1

//完善日志记录机制 格式：Error: "#error_code  '#' 只用在宏里面相当于'+'
#define LOG_ERROR(error_code) LOG_FATAL(log_fp, "Error: "#error_code);

//宏定义多行代码函数
#define ERROR_EXIT(error_code)\
    {\
        LOG_ERROR(error_code);  \
        _result->error = error_code; \
        log_close(log_fp);  \
        return; \
    }

#define ARGS_MAX_NUMBER 256   //参数个数最大值
#define ENV_MAX_NUMBER 256    //环境个数最大值

//错误代码
enum {
    SUCCESS = 0,                //成功通过
    INVALID_CONFIG = -1,        //无效配置码    
    FORK_FAILED = -2,           //复刻失败
    PTHREAD_FAILED = -3,        //-开线程失败
    WAIT_FAILED = -4,           //等待失败
    ROOT_REQUIRED = -5,         //需要root权限
    LOAD_SECCOMP_FAILED = -6,   //加载安全计算模式失败
    SETRLIMIT_FAILED = -7,      //设置资源限制失败
    DUP2_FAILED = -8,           //复制文件描述符失败
    SETUID_FAILED = -9,         //设置用户ID失败
    EXECVE_FAILED = -10,        //执行execve系统调用失败
    SPJ_ERROR = -11             //特殊评判失败 评判机模块不会返回这个值，它用来进行对答案检查
};


struct config {
    int max_cpu_time;              //允许进程消耗的最大CPU时间，-1为不设限制,单位（ms）
    int max_real_time;              //允许进程消耗的最大真实时间，-1为不设限制，单位（ms）
    long max_memory;                //允许进程消耗的最大虚拟内存，-1为不设限制，单位（byte）
    long max_stack;                 //允许进程消耗的最大栈内存，-1为不设限制，单位（byte）
    int max_process_number;         //允许为调用进程的实际用户ID创建的最大进程数，-1为不设限制
    long max_output_size;           //允许进程输出到标准输出，标准错误和文件的最大数据量，-1为不设限制
    int memory_limit_check_only;    //如果这个值为0，将会只检查内存使用量，因为setrlimit（maxrss）将导致一些崩溃的问题
    char *exe_path;                 //被运行文件存放路径
    char *input_path;               //将这个文件的内容重定向输入到进程的标准输入
    char *output_path;              //将进程的标准输出重定向输入到这个文件里面
    char *error_path;               //将进程的标准错误重定向输入到这个文件里面
    char *args[ARGS_MAX_NUMBER];    //(字符串数组以NULL结尾)：运行此进程的参数
    char *env[ENV_MAX_NUMBER];      //(字符串数组以NULL结尾)：此进程可以得到的环境变量
    char *log_path;                 //评判机的日志存放路径
    char *seccomp_rule_name;        //(字符串或者NULL)：用于限制进程系统调用的seccomp规则，名称用于调用相应的函数。
    uid_t uid;                      //运行此进程的用户
    gid_t gid;                      //此进程归属的用户组
};

//评判结果
enum {
    WRONG_ANSWER = -1,              //judger 模块将不会返回这个值，它用来作为答案的判断  例如：答案逻辑错误等
    CPU_TIME_LIMIT_EXCEEDED = 1,    //CPU时间时间限制超时，例如 时空效率低下的情况：死循环或者代码复杂度高
    REAL_TIME_LIMIT_EXCEEDED = 2,   //真实时间限制超时，包含等待时间和运行判题时间
    MEMORY_LIMIT_EXCEEDED = 3,      //内存限制溢出 例如使用malloc（）分配空间时，用完不free（）。
    RUNTIME_ERROR = 4,              //运行时错误 例如：1.数组开得太小了，2.发生除零错误，3.大数组定义在函数内，导致程序栈区耗尽，4.指针用错了，导致访问到不改访问到的区域，5.程序抛出未接收的异常
    SYSTEM_ERROR = 5                //系统出现错误
};


struct result {
    int cpu_time;       //进程已经使用的CPU时间
    int real_time;      //进程实际运行时间
    long memory;        //进程使用的最大内存量
    int signal;         //信号代码
    int exit_code;      //进程退出代码
    int error;          //参数args验证错误或者评判机内部错误，细节见本文件的错误代码
    int result;         //评判结果，细节见本文件的评判结果
};


void run(struct config *, struct result *);
#endif //JUDGER_RUNNER_H
