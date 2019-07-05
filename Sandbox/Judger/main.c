#include "argtable3.h"  //引入参数表头文件
#include "runner.h"  //包含runner.h 然后使用struct config和struct result指针调用run方法

#define INT_PLACE_HOLDER "<n>"
#define STR_PLACE_HOLDER "<str>"

struct arg_lit *verb, *help, *version;
struct arg_int *max_cpu_time, *max_real_time, *max_memory, *max_stack, *memory_limit_check_only,
        *max_process_number, *max_output_size, *uid, *gid;
struct arg_str *exe_path, *input_path, *output_path, *error_path, *args, *env, *log_path, *seccomp_rule_name;
struct arg_end *end;

int main(int argc, char *argv[]) {
    //设置显示OJ的cli程序的参数表构建
    void *arg_table[] = {
            help = arg_litn(NULL, "help", 0, 1, "Display This Help And Exit"),
            version = arg_litn(NULL, "version", 0, 1, "Display Version Info And Exit"),
            max_cpu_time = arg_intn(NULL, "max_cpu_time", INT_PLACE_HOLDER, 0, 1, "Max CPU Time (ms)"),
            max_real_time = arg_intn(NULL, "max_real_time", INT_PLACE_HOLDER, 0, 1, "Max Real Time (ms)"),
            max_memory = arg_intn(NULL, "max_memory", INT_PLACE_HOLDER, 0, 1, "Max Memory (byte)"),
            memory_limit_check_only = arg_intn(NULL, "memory_limit_check_only", INT_PLACE_HOLDER, 0, 1, "only check memory usage, do not setrlimit (default False)"),
            max_stack = arg_intn(NULL, "max_stack", INT_PLACE_HOLDER, 0, 1, "Max Stack (byte, default 16M)"),
            max_process_number = arg_intn(NULL, "max_process_number", INT_PLACE_HOLDER, 0, 1, "Max Process Number"),
            max_output_size = arg_intn(NULL, "max_output_size", INT_PLACE_HOLDER, 0, 1, "Max Output Size (byte)"),

            exe_path = arg_str1(NULL, "exe_path", STR_PLACE_HOLDER, "Exe Path"),
            input_path = arg_strn(NULL, "input_path", STR_PLACE_HOLDER, 0, 1, "Input Path"),
            output_path = arg_strn(NULL, "output_path", STR_PLACE_HOLDER, 0, 1, "Output Path"),
            error_path = arg_strn(NULL, "error_path", STR_PLACE_HOLDER, 0, 1, "Error Path"),

            args = arg_strn(NULL, "args", STR_PLACE_HOLDER, 0, 255, "Arg"),
            env = arg_strn(NULL, "env", STR_PLACE_HOLDER, 0, 255, "Env"),

            log_path = arg_strn(NULL, "log_path", STR_PLACE_HOLDER, 0, 1, "Log Path"),
            seccomp_rule_name = arg_strn(NULL, "seccomp_rule_name", STR_PLACE_HOLDER, 0, 1, "Seccomp Rule Name"),

            uid = arg_intn(NULL, "uid", INT_PLACE_HOLDER, 0, 1, "UID (default 65534)"),
            gid = arg_intn(NULL, "gid", INT_PLACE_HOLDER, 0, 1, "GID (default 65534)"),

            end = arg_end(10),
    };

    //初始化退出代码为0，第一次出现
    int exitcode = 0;
    //初始化name数组字符串
    char name[] = "libjudger.so";
    //cli程序的一部分，解析命令行
    int nerrors = arg_parse(argc, argv, arg_table);

    //输出cli程序的语法帮助信息，count给出数组中保存的值的数目，help出现了，
    //count就大于0，就输出提示语法信息和选项词汇表，下面的类似。
    if (help->count > 0) {
        printf("Usage: %s", name);
        arg_print_syntax(stdout, arg_table, "\n\n");
        arg_print_glossary(stdout, arg_table, "  %-25s %s\n");
        goto exit;
    }

    if (version->count > 0) {
        printf("Version: %d.%d.%d\n", (VERSION >> 16) & 0xff, (VERSION >> 8) & 0xff, VERSION & 0xff);
        goto exit;
    }

    if (nerrors > 0) {
        arg_print_errors(stdout, end, name);
        printf("Try '%s --help' for more information.\n", name);
        //都出错是就改变exitcode，代码值出现第二次。
        exitcode = 1;
        goto exit;
    }

    //这是OJ正式开始部分
    //ival成员变量指向一个整数数组，该数组保存从命令行中提取的值 
    //例如调用Judger时传入的max_cpu_time的值就会自动保存到ival
    //参数表中已经构造了max_cpu_time出现一次或不出现，出现就初始化赋值为*max_cpu_time->ival
    //，不出现就初始化为UNLIMITED=-1，下面的类似。
    struct config _config;
    //初始换7个判题结果为0
    struct result _result = {0, 0, 0, 0, 0, 0, 0};

    if (max_cpu_time->count > 0) {
        _config.max_cpu_time = *max_cpu_time->ival;
    } else {
        _config.max_cpu_time = UNLIMITED;
    }

    if (max_real_time->count > 0) {
        _config.max_real_time = *max_real_time->ival;
    } else {
        _config.max_real_time = UNLIMITED;
    }

    if (max_memory->count > 0) {
        _config.max_memory = (long) *max_memory->ival;
    } else {
        _config.max_memory = UNLIMITED;
    }
    
    //如果这个值为0，将会只检查内存使用量，因为setrlimit（maxrss）将导致一些崩溃的问题
    if (memory_limit_check_only->count > 0) {
        _config.memory_limit_check_only = *memory_limit_check_only->ival == 0 ? 0 : 1;
    } else {
        _config.memory_limit_check_only = 0;
    }

    //如果栈的使用大小传入有值，就赋值给传入的值，否则指定其大小为：_config.max_stack = 16 * 1024 * 1024
    if (max_stack->count > 0) {
        _config.max_stack = (long) *max_stack->ival;
    } else {
        _config.max_stack = 16 * 1024 * 1024;
    }

    //允许为调用进程的实际用户ID创建的最大进程数，-1为不设限制
    if (max_process_number->count > 0) {
        _config.max_process_number = *max_process_number->ival;
    } else {
        _config.max_process_number = UNLIMITED;
    }

    //允许进程输出到标准输出，标准错误和文件的最大数据量，-1为不设限制
    if (max_output_size->count > 0) {
        _config.max_output_size = (long) *max_output_size->ival;
    } else {
        _config.max_output_size = UNLIMITED;
    }

    //设置执行文件存放的路径
    _config.exe_path = (char *)*exe_path->sval;

    //输入文件路径设置
    if (input_path->count > 0) {
        _config.input_path = (char *)input_path->sval[0];
    } else {
        _config.input_path = "/dev/stdin";
    }

    //输出文件路径设置
    if (output_path->count > 0) {
        _config.output_path = (char *)output_path->sval[0];
    } else {
        _config.output_path = "/dev/stdout";
    }

    //出错文件路径设置
    if (error_path->count > 0) {
        _config.error_path = (char *)error_path->sval[0];
    } else {
        _config.error_path = "/dev/stderr";
    }

    //args和sval都是一个字符串数组，初始化args[0]为执行文件的路径
    //因为命令行里面的格式是：./执行文件 参数1 参数2 
    //(字符串数组以NULL结尾)：设置运行此进程的参数
    _config.args[0] = _config.exe_path;
    int i = 1;
    if (args->count > 0) {
        for (; i < args->count + 1; i++) {
            _config.args[i] = (char *)args->sval[i - 1];
        }
    }
    //各个参数设置完之后以NULL结尾
    _config.args[i] = NULL;

    //同样的，环境路径也是一样，只不过没有执行文件它是这样的：环境1 环境2 
    //最后也是要设置为NULL
    i = 0;
    if (env->count > 0) {
        for (; i < env->count; i++) {
            _config.env[i] = (char *)env->sval[i];
        }
    }
    _config.env[i] = NULL;

    //设置评判机的日志存放路径，否则放在当前目录下面
    if (log_path->count > 0) {
        _config.log_path = (char *)log_path->sval[0];
    } else {
        _config.log_path = "judger.log";
    }

    //(字符串或者NULL)：设置用于限制进程系统调用的seccomp规则，名称用于调用相应的函数。
    if (seccomp_rule_name->count > 0) {
        _config.seccomp_rule_name = (char *)seccomp_rule_name->sval[0];
    } else {
        _config.seccomp_rule_name = NULL;
    }

    //设置运行此进程的用户,否则设置成为不信任的uid=65534
    if (uid->count > 0) {
        _config.uid = (uid_t)*(uid->ival);
    }
    else {
        _config.uid = 65534;
    }
    
    //此进程归属的用户组，否则设置成为不信任的gid=65534
    if(gid->count > 0) {
        _config.gid = (gid_t)*(gid->ival);
    }
    else {
        _config.gid = 65534;
    }

    //设置完成之后开始调用runner.c 中的run(...)函数开始判题。
    run(&_config, &_result);

    //判题成功返回，输出系统资源的使用情况。
    printf("{\n"
           "    \"cpu_time\": %d,\n"
           "    \"real_time\": %d,\n"
           "    \"memory\": %ld,\n"
           "    \"signal\": %d,\n"
           "    \"exit_code\": %d,\n"
           "    \"error\": %d,\n"
           "    \"result\": %d\n"
           "}",
           _result.cpu_time,
           _result.real_time,
           _result.memory,
           _result.signal,
           _result.exit_code,
           _result.error,
           _result.result);

    //解除分配arg_table[]中的每个非空条目
    exit:
    arg_freetable(arg_table, sizeof(arg_table) / sizeof(arg_table[0]));
    //返回exitcode，第三次出现
    return exitcode;
}
