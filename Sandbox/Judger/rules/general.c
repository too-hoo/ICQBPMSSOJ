#include <stdio.h>
#include <seccomp.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>

#include "../runner.h"

//系统调用黑名单
int general_seccomp_rules(struct config *_config) {
    int syscalls_blacklist[] = {SCMP_SYS(clone),
                                SCMP_SYS(fork), SCMP_SYS(vfork),
                                SCMP_SYS(kill), 
#ifdef __NR_execveat      //NR 开头就是系统调用
                                SCMP_SYS(execveat)
#endif
                               };
    int syscalls_blacklist_length = sizeof(syscalls_blacklist) / sizeof(int);
    // 初始化过滤器ctx
    scmp_filter_ctx ctx = NULL;
    // 加载安全计算模式规则
    ctx = seccomp_init(SCMP_ACT_ALLOW);
    if (!ctx) {
        return LOAD_SECCOMP_FAILED;
    }
    //循环加载白名单的系统调用，SCMP_ACT_ALLOW允许的系统调用，如果成功返回0，失败返回值非0，
    // 返回LOAD_SECCOMP_FAILED
    for (int i = 0; i < syscalls_blacklist_length; i++) {
        if (seccomp_rule_add(ctx, SCMP_ACT_KILL, syscalls_blacklist[i], 0) != 0) {
            return LOAD_SECCOMP_FAILED;
        }
    }

    // use SCMP_ACT_KILL for socket, python will be killed immediately
    //为socket使用 SCMP_ACT_KILL，python 将会被立即杀死
    //SCMP_ACT_ERRNO(EACCES):当线程调用与筛选规则匹配的系统调用时，它将收到errno的一个返回值
    if (seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EACCES), SCMP_SYS(socket), 0) != 0) {
        return LOAD_SECCOMP_FAILED;
    }
    // 为execve添加额外的限制规则，在我的规则之下才可以执行
    // SCMP_ACT_KILL：不能执行，要被杀死，下面一样
    // 为了避免用户调用系统的路径干坏事，第一个参数必须为用户的编译好的文件路径才行，使用SCMP_A0()函数限制路径，否则将execve杀掉
    if (seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(execve), 1, SCMP_A0(SCMP_CMP_NE, (scmp_datum_t)(_config->exe_path))) != 0) {
        return LOAD_SECCOMP_FAILED;
    }
    // do not allow "w" and "rw" using open
    if (seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(open), 1, SCMP_CMP(1, SCMP_CMP_MASKED_EQ, O_WRONLY, O_WRONLY)) != 0) {
        return LOAD_SECCOMP_FAILED;
    }
    if (seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(open), 1, SCMP_CMP(1, SCMP_CMP_MASKED_EQ, O_RDWR, O_RDWR)) != 0) {
        return LOAD_SECCOMP_FAILED;
    }
    // do not allow "w" and "rw" using openat
    if (seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(openat), 1, SCMP_CMP(2, SCMP_CMP_MASKED_EQ, O_WRONLY, O_WRONLY)) != 0) {
        return LOAD_SECCOMP_FAILED;
    }
    if (seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(openat), 1, SCMP_CMP(2, SCMP_CMP_MASKED_EQ, O_RDWR, O_RDWR)) != 0) {
        return LOAD_SECCOMP_FAILED;
    }

    //加载到内核生效
    if (seccomp_load(ctx) != 0) {
        return LOAD_SECCOMP_FAILED;
    }
    seccomp_release(ctx);
    return 0;
}
