#ifndef JUDGER_KILLER_H
#define JUDGER_KILLER_H

//超时killer参数结构
struct timeout_killer_args {
    int pid;
    int timeout;
};

//杀死指定pid进程
int kill_pid(pid_t pid);

//超时killer
void *timeout_killer(void *timeout_killer_args);

#endif //JUDGER_KILLER_H
