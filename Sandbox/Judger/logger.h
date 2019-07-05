#ifndef JUDGER_LOGGER_H
#define JUDGER_LOGGER_H

#define LOG_LEVEL_FATAL 0       //致命0
#define LOG_LEVEL_WARNING 1     //警告1
#define LOG_LEVEL_INFO 2        //正常信息2
#define LOG_LEVEL_DEBUG 3       //调试3


FILE *log_open(const char *);   //打开日志

void log_close(FILE *);         //关闭日志

//写入日志
void log_write(int level, const char *source_filename, const int line_number, const FILE *log_fp, const char *, ...);

//使用宏定义函数向日志写入信息，x...表示log_fp之后的参数可以是零个或者多个，##x连接。
#ifdef JUDGER_DEBUG
#define LOG_DEBUG(log_fp, x...)   log_write(LOG_LEVEL_DEBUG, __FILE__, __LINE__, log_fp, ##x)
#else
#define LOG_DEBUG(log_fp, x...)
#endif

#define LOG_INFO(log_fp, x...)  log_write(LOG_LEVEL_INFO, __FILE__, __LINE__, log_fp, ##x)
#define LOG_WARNING(log_fp, x...) log_write(LOG_LEVEL_WARNING, __FILE__, __LINE__, log_fp, ##x)
#define LOG_FATAL(log_fp, x...)   log_write(LOG_LEVEL_FATAL, __FILE__, __LINE__, log_fp, ##x)

#endif //JUDGER_LOGGER_H
