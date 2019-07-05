#define _DEFAULT_SOURCE
#define _POSIX_SOURCE
#define _GNU_SOURCE
#include <stdio.h>
#include <stdarg.h>
#include <signal.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <grp.h>
#include <dlfcn.h>
#include <errno.h>
#include <sched.h>
#include <sys/resource.h>      //包含rlimit结构体等头文件
#include <sys/types.h>
#include <sys/time.h>
#include <sys/mount.h>

#include "runner.h"
#include "child.h"
#include "logger.h"
#include "rules/seccomp_rules.h"

#include "killer.h"


//关闭文件
void close_file(FILE *fp) {
    if (fp != NULL) {
        fclose(fp);
    }
}

//经过fork(),并开启孩子进程
//设置最大的进程堆栈RLIMIT_STACK，以字节为单位，失败时退出
void child_process(FILE *log_fp, struct config *_config) {
    FILE *input_file = NULL, *output_file = NULL, *error_file = NULL;

    if (_config->max_stack != UNLIMITED) {
        struct rlimit max_stack;
        max_stack.rlim_cur = max_stack.rlim_max = (rlim_t) (_config->max_stack);
        if (setrlimit(RLIMIT_STACK, &max_stack) != 0) {
            CHILD_ERROR_EXIT(SETRLIMIT_FAILED);
        }
    }

    //设置内存限制：RLIMIT_AS //进程的最大虚内存空间，字节为单位。
    //如果memory_limit_check_only这个值为0，将会只检查内存使用量，因为setrlimit（maxrss）将导致一些崩溃的问题
    if (_config->memory_limit_check_only == 0) {
        if (_config->max_memory != UNLIMITED) {
            struct rlimit max_memory;
            max_memory.rlim_cur = max_memory.rlim_max = (rlim_t) (_config->max_memory) * 2;
            if (setrlimit(RLIMIT_AS, &max_memory) != 0) {
                CHILD_ERROR_EXIT(SETRLIMIT_FAILED);
            }
        }
    }

    //设置进程消耗的最大CPU时间（秒）
    if (_config->max_cpu_time != UNLIMITED) {
        struct rlimit max_cpu_time;
        max_cpu_time.rlim_cur = max_cpu_time.rlim_max = (rlim_t) ((_config->max_cpu_time + 1000) / 1000);
        if (setrlimit(RLIMIT_CPU, &max_cpu_time) != 0) {
            CHILD_ERROR_EXIT(SETRLIMIT_FAILED);
        }
    }

    //设置为调用进程的实际用户ID创建的最大进程数
    if (_config->max_process_number != UNLIMITED) {
        struct rlimit max_process_number;
        max_process_number.rlim_cur = max_process_number.rlim_max = (rlim_t) _config->max_process_number;
        if (setrlimit(RLIMIT_NPROC, &max_process_number) != 0) {
            CHILD_ERROR_EXIT(SETRLIMIT_FAILED);
        }
    }

    //设置进程输出到标准输出，标准错误和文件的最大数据量
    if (_config->max_output_size != UNLIMITED) {
        struct rlimit max_output_size;
        max_output_size.rlim_cur = max_output_size.rlim_max = (rlim_t ) _config->max_output_size;
        if (setrlimit(RLIMIT_FSIZE, &max_output_size) != 0) {
            CHILD_ERROR_EXIT(SETRLIMIT_FAILED);
        }
    }
    
    //将这个文件的内容重定向输入到进程的标准输入
    if (_config->input_path != NULL) {
        input_file = fopen(_config->input_path, "r");
        if (input_file == NULL) {
            CHILD_ERROR_EXIT(DUP2_FAILED);
        }
        // 重定向文件File -> stdin
        // 成功时，这些系统调用返回新的描述符
        //出错时，返回-1，并正确设置errno
        if (dup2(fileno(input_file), fileno(stdin)) == -1) {
            // todo log
            CHILD_ERROR_EXIT(DUP2_FAILED);
        }
    }

    //将进程的标准输出重定向输入到这个文件里面
    if (_config->output_path != NULL) {
        output_file = fopen(_config->output_path, "w");
        if (output_file == NULL) {
            CHILD_ERROR_EXIT(DUP2_FAILED);
        }
        // 重定向标准输出流stdout -> file
        if (dup2(fileno(output_file), fileno(stdout)) == -1) {
            CHILD_ERROR_EXIT(DUP2_FAILED);
        }
    }

    if (_config->error_path != NULL) {
        // 如果输出信息文件和错误信息文件有相同的路径，使用同一个文件指针
        if (_config->output_path != NULL && strcmp(_config->output_path, _config->error_path) == 0) {
            error_file = output_file;
        }
        else {
            error_file = fopen(_config->error_path, "w");
            if (error_file == NULL) {
                // todo log
                CHILD_ERROR_EXIT(DUP2_FAILED);
            }
        }
        //  重定向标准错误流stderr -> file
        if (dup2(fileno(error_file), fileno(stderr)) == -1) {
            // todo log
            CHILD_ERROR_EXIT(DUP2_FAILED);
        }
    }

    // 设置此进程归属的用户组
    gid_t group_list[] = {_config->gid};
    if (_config->gid != -1 && (setgid(_config->gid) == -1 || setgroups(sizeof(group_list) / sizeof(gid_t), group_list) == -1)) {
        CHILD_ERROR_EXIT(SETUID_FAILED);
    }

    //设置运行进程的用户
    if (_config->uid != -1 && setuid(_config->uid) == -1) {
        CHILD_ERROR_EXIT(SETUID_FAILED);
    }

    // 加载安全计算模式seccomp规则
    if (_config->seccomp_rule_name != NULL) {
        if (strcmp("c_cpp", _config->seccomp_rule_name) == 0) {
            if (c_cpp_seccomp_rules(_config) != SUCCESS) {
                CHILD_ERROR_EXIT(LOAD_SECCOMP_FAILED);
            }
        }
        else if (strcmp("general", _config->seccomp_rule_name) == 0) {
            if (general_seccomp_rules(_config) != SUCCESS ) {
                CHILD_ERROR_EXIT(LOAD_SECCOMP_FAILED);
            }
        }
        // 其他规则
        else {
            // 规则不存在
            CHILD_ERROR_EXIT(LOAD_SECCOMP_FAILED);
        }
    }

    execve(_config->exe_path, _config->args, _config->env);
    CHILD_ERROR_EXIT(EXECVE_FAILED);
}
