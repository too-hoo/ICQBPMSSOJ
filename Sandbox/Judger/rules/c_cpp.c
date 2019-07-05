#include <stdio.h>
#include <seccomp.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

#include "../runner.h"

//系统调用白名单
int c_cpp_seccomp_rules(struct config *_config) {
    int syscalls_whitelist[] = {SCMP_SYS(read), SCMP_SYS(fstat),
                                SCMP_SYS(mmap), SCMP_SYS(mprotect),
                                SCMP_SYS(munmap), SCMP_SYS(uname),
                                SCMP_SYS(arch_prctl), SCMP_SYS(brk),
                                SCMP_SYS(access), SCMP_SYS(exit_group),
                                SCMP_SYS(close), SCMP_SYS(readlink),
                                SCMP_SYS(sysinfo), SCMP_SYS(write),
                                SCMP_SYS(writev), SCMP_SYS(lseek)};

    int syscalls_whitelist_length = sizeof(syscalls_whitelist) / sizeof(int);
    scmp_filter_ctx ctx = NULL;

    // 开始加载seccomp规则
    ctx = seccomp_init(SCMP_ACT_KILL);
    // ctx == NULL 时就返回LOAD_SECCOMP_FAILED
    if (!ctx) {
        return LOAD_SECCOMP_FAILED;
    }

    //循环加载白名单的系统调用，SCMP_ACT_ALLOW允许的系统调用，如果失败返回值非0，返回LOAD_SECCOMP_FAILED
    for (int i = 0; i < syscalls_whitelist_length; i++) {
        if (seccomp_rule_add(ctx, SCMP_ACT_ALLOW, syscalls_whitelist[i], 0) != 0) {
            return LOAD_SECCOMP_FAILED;
        }
    }

    // 为execve添加额外的1个规则，使用SCMP_A0指定文件的路径，必须匹配才行，否则不能执行
    if (seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(execve), 1, SCMP_A0(SCMP_CMP_EQ, (scmp_datum_t)(_config->exe_path))) != 0) {
        return LOAD_SECCOMP_FAILED;
    }
    //我们不期望这些程序可以写任何文件。这种想法的直觉是限制 write 的第一个参数 fd 不能大于 stderr，
    //但是实际是可绕过沙箱的，那就是 mmap。页面最下面的例子修改下然后 strace 运行就会发现只需要
    //open 然后 mmap 也可以写文件的。正确的方法是限制 open，不能带写权限.
    //Open要求：The argument flags must include one of the following access modes: O_RDONLY(只读), O_WRONLY(只写), or O_RDWR(读写)
    //所以这里就需要之前的掩码后比较了，其实掩码操作就是使用掩码和原数据进行与操作，
    // SCMP_CMP(1, SCMP_CMP_MASKED_EQ, O_WRONLY | O_RDWR, 0) 就是说这两位上都是0才可以通过
    // do not allow "w" and "rw"
    if (seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(open), 1, SCMP_CMP(1, SCMP_CMP_MASKED_EQ, O_WRONLY | O_RDWR, 0)) != 0) {
        return LOAD_SECCOMP_FAILED;
    }
    //调用open或openat函数可以打开或创建一个文件,所以openat也要限制
    if (seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(openat), 1, SCMP_CMP(2, SCMP_CMP_MASKED_EQ, O_WRONLY | O_RDWR, 0)) != 0) {
        return LOAD_SECCOMP_FAILED;
    }

    //加载到内核生效
    if (seccomp_load(ctx) != 0) {
        return LOAD_SECCOMP_FAILED;
    }
    //最后释放ctx上下文过滤器
    seccomp_release(ctx);
    return 0;
}