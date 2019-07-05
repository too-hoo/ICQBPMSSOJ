#ifndef JUDGER_CHILD_H
#define JUDGER_CHILD_H

#include <string.h>
#include "runner.h"

//宏定义函数，调用日志文件中的函数，将Judger的信息输出到log_fp中格式为：
// Error: System errno: %s; Internal errno: "#error_code, strerror(errno));
//SIGUSR1 用户自定义信号 进程自身终止 raise(SIGUSR1) 等价于 kill(getpid(), SIGUSR1)。
#define CHILD_ERROR_EXIT(error_code)\
    {\
        LOG_FATAL(log_fp, "Error: System errno: %s; Internal errno: "#error_code, strerror(errno)); \
        close_file(input_file); \
        if (output_file == error_file) { \
            close_file(output_file); \
        } else { \
            close_file(output_file); \
            close_file(error_file);  \
        } \
        raise(SIGUSR1);  \
        exit(EXIT_FAILURE); \
    }

//经过fork(),并开启子进程
void child_process(FILE *log_fp, struct config *_config);

#endif //JUDGER_CHILD_H
