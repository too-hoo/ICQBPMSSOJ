#define _GNU_SOURCE
#define _POSIX_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <sched.h>
#include <signal.h>
#include <pthread.h>
#include <wait.h>
#include <errno.h>
#include <unistd.h>    //fork()函数头文件

#include <sys/time.h>
#include <sys/resource.h>
#include <sys/types.h>  // 中文名称为基本系统数据类型，此头文件还包含适当时应使用的多个基本派生类型，如下面用到的uid_t,和pid_t等

#include "runner.h"
#include "killer.h"
#include "child.h"
#include "logger.h"

/**
  初始化评判结果:
  评判结果代码和评判结果错误均设成SUCCESS等等
*/
void init_result(struct result *_result) {
    _result->result = _result->error = SUCCESS;
    _result->cpu_time = _result->real_time = _result->signal = _result->exit_code = 0;
    _result->memory = 0;
}


void run(struct config *_config, struct result *_result) {
    // init log fp  初始化日志存放路径
    FILE *log_fp = log_open(_config->log_path);

    // init result 初始化评判结果
    init_result(_result);

    // check whether current user is root  检查当前的用户是否为root
    //如果不是就退出程序设置ROOT_REQUIRED=-5
    uid_t uid = getuid();
    if (uid != 0) {
        ERROR_EXIT(ROOT_REQUIRED); 
    }

    // check args 检查参数，如果有任意一个不满足都会退出，并设置INVALID_CONFIG=-1
    if ((_config->max_cpu_time < 1 && _config->max_cpu_time != UNLIMITED) ||
        (_config->max_real_time < 1 && _config->max_real_time != UNLIMITED) ||
        (_config->max_stack < 1) ||
        (_config->max_memory < 1 && _config->max_memory != UNLIMITED) ||
        (_config->max_process_number < 1 && _config->max_process_number != UNLIMITED) ||
        (_config->max_output_size < 1 && _config->max_output_size != UNLIMITED)) {
        ERROR_EXIT(INVALID_CONFIG);
    }

    // record current time  记录当前时间
    struct timeval start, end;
    gettimeofday(&start, NULL);

    pid_t child_pid = fork();  //已将包含头文件unistd.h,fork()子进程。

    //当 pid < 0 时显示 clone 失败 
    if (child_pid < 0) {   
        ERROR_EXIT(FORK_FAILED);
    }
    else if (child_pid == 0) {      //开启子进程
        child_process(log_fp, _config);
    }
    else if (child_pid > 0){
        // create new thread to monitor process running time
        // 产生新的线程来监控进程的运行时间
        pthread_t tid = 0;
        //最大时间有限制就进去
        if (_config->max_real_time != UNLIMITED) {
            struct timeout_killer_args killer_args;

            killer_args.timeout = _config->max_real_time;
            killer_args.pid = child_pid;
            //使用pthread_create()函数进行操作
            if (pthread_create(&tid, NULL, timeout_killer, (void *) (&killer_args)) != 0) {
                kill_pid(child_pid);
                ERROR_EXIT(PTHREAD_FAILED);
            }
        }

        int status;
        struct rusage resource_usage;

        // 等待孩子进程终止
        // 成功时，返回进程状态改变的孩子进程的ID
        // 失败时，返回-1
        if (wait4(child_pid, &status, WSTOPPED, &resource_usage) == -1) {
            kill_pid(child_pid);
            ERROR_EXIT(WAIT_FAILED);
        }
        // 获得结束时间
        gettimeofday(&end, NULL);
        _result->real_time = (int) (end.tv_sec * 1000 + end.tv_usec / 1000 - start.tv_sec * 1000 - start.tv_usec / 1000);

        // 进程退出之后，还需要去取消监控子进程的 killer thread。
        if (_config->max_real_time != UNLIMITED) {
            if (pthread_cancel(tid) != 0) {
                // todo logging
            };
        }

        if (WIFSIGNALED(status) != 0) {
            _result->signal = WTERMSIG(status);
        }

        if(_result->signal == SIGUSR1) {
            _result->result = SYSTEM_ERROR;
        }
        else {
            _result->exit_code = WEXITSTATUS(status);
            _result->cpu_time = (int) (resource_usage.ru_utime.tv_sec * 1000 +
                                       resource_usage.ru_utime.tv_usec / 1000);
            _result->memory = resource_usage.ru_maxrss * 1024;

            if (_result->exit_code != 0) {
                _result->result = RUNTIME_ERROR;
            }

            if (_result->signal == SIGSEGV) {
                if (_config->max_memory != UNLIMITED && _result->memory > _config->max_memory) {
                    _result->result = MEMORY_LIMIT_EXCEEDED;
                }
                else {
                    _result->result = RUNTIME_ERROR;
                }
            }
            else {
                if (_result->signal != 0) {
                    _result->result = RUNTIME_ERROR;
                }
                if (_config->max_memory != UNLIMITED && _result->memory > _config->max_memory) {
                    _result->result = MEMORY_LIMIT_EXCEEDED;
                }
                if (_config->max_real_time != UNLIMITED && _result->real_time > _config->max_real_time) {
                    _result->result = REAL_TIME_LIMIT_EXCEEDED;
                }
                if (_config->max_cpu_time != UNLIMITED && _result->cpu_time > _config->max_cpu_time) {
                    _result->result = CPU_TIME_LIMIT_EXCEEDED;
                }
            }
        }

        log_close(log_fp);
    }
}
