#define _POSIX_SOURCE
#include <pthread.h>
#include <unistd.h>
#include <signal.h>     //sleep(),fork()等函数头文件

#include "killer.h"

//发送SIGKILL信号给pid
int kill_pid(pid_t pid) {
    return kill(pid, SIGKILL);
}

//超时killer
void *timeout_killer(void *timeout_killer_args) {
    // 这是一个新的线程，如果时间超时就杀死进程
    pid_t pid = ((struct timeout_killer_args *)timeout_killer_args)->pid;
    int timeout = ((struct timeout_killer_args *)timeout_killer_args)->timeout;
    
    // 成功时，pthread_detach()就返回0；出错时，它就返回一个错误码。
    if (pthread_detach(pthread_self()) != 0) {
        kill_pid(pid);
        return NULL;
    }
    // usleep can't be used, for time args must < 1000ms
    // usleep 不能使用，因为time的参数必须小于1000ms，这样就可能比我们希望的sleep时间要长，但是
    // 我们最后会再来一个检查
    // this may sleep longer that expected, but we will have a check at the end
    if (sleep((unsigned int)((timeout + 1000) / 1000)) != 0) {
        kill_pid(pid);
        return NULL;
    }
    if (kill_pid(pid) != 0) {
        return NULL;
    }
    return NULL;
}