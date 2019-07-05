#!/bin/sh

APP=/home/toohoo/PycharmProjects/ICQBPMSSOJ
DATA=/data

# 首先创建主要的数据目录/data,然后在该目录下面创建多个数据存储和日志目录
#mkdir -p $DATA/log $DATA/config $DATA/ssl $DATA/test_case $DATA/public/upload $DATA/public/avatar $DATA/public/website

# -f 判断文件是否存在
# 如果在该目录下面没有密钥，就创建一个
if [ ! -f "$DATA/config/secret.key" ]; then
    echo $(cat /dev/urandom | head -1 | md5sum | head -c 32) > "$DATA/config/secret.key"
fi

# 如果没有对应的头像，就将一个准备好的头像复制道对应的目录里面去
if [ ! -f "$DATA/public/avatar/default.png" ]; then
   cp $APP/data/public/avatar/default.png $DATA/public/avatar
fi

# 如果没有对应的logo，就将对应的logo复制到指定的目录里面去
if [ ! -f "$DATA/public/website/favicon.ico" ]; then
   cp $APP/data/public/website/favicon.ico $DATA/public/website
fi

# 创建公钥和私钥
SSL="$DATA/ssl"
if [ ! -f "$SSL/server.key" ]; then
    openssl req -x509 -newkey rsa:2048 -keyout "$SSL/server.key" -out "$SSL/server.crt" -days 1000 \
        -subj "/C=CN/ST=Zhanjiang/L=Zhanjiang/O=Zhanjiang ICQBPMSSOJ Technology Co., Ltd./OU=Service Infrastructure Department/CN=`hostname`" -nodes
fi

# 服务器Nginx的设置：
# 创建软连接，设置跳转等等，设置软连接之后，别人想应用就很方便
cd $APP/deploy/nginx
ln -sf locations.conf https_locations.conf
# 判断字符串$FORCE_HTTPS是否为空（后指向前），然后决定跳转的软连接
if [ -z "$FORCE_HTTPS" ]; then
    ln -sf locations.conf http_locations.conf
else
    ln -sf https_redirect.conf http_locations.conf
fi

# 判断字符串$LOWER_IP_HEADER是否为空，替换
if [ ! -z "$LOWER_IP_HEADER" ]; then
    sed -i "s/__IP_HEADER__/\$http_$LOWER_IP_HEADER/g" api_proxy.conf;
else
    sed -i "s/__IP_HEADER__/\$remote_addr/g" api_proxy.conf;
fi

# 判断字符串$MAX_WORKER_NUM是否为空，首先应该是空的，然后根据CPU的信息：CPU的核数目，设置Worker的数目，保存到系统里面
if [ -z "$MAX_WORKER_NUM" ]; then
    export CPU_CORE_NUM=$(grep -c ^processor /proc/cpuinfo)
    # 如果CPU的核数目小于2，最大的worker设置为2，否则设置为CPU的核数
    if [ $CPU_CORE_NUM -lt 2 ]; then
        export MAX_WORKER_NUM=2
    else
        export MAX_WORKER_NUM=$(($CPU_CORE_NUM))
    fi
fi

#设置前端显示
#判断字符串$STATIC_CDN_HOST是否为空，过滤信息
#cd $APP/dist
#if [ ! -z "$STATIC_CDN_HOST" ]; then
#    find . -name "*.*" -type f -exec sed -i "s/__STATIC_CDN_HOST__/\/$STATIC_CDN_HOST/g" {} \;
#else
#    find . -name "*.*" -type f -exec sed -i "s/__STATIC_CDN_HOST__\///g" {} \;
#fi

cd $APP

#进行数据库的设置：
n=0
while [ $n -lt 5 ]
do
    #创建表格
    python3 manage.py migrate --no-input &&
    #创建超级用户
    python3 manage.py inituser --username=root --password=root123 --action=create_super_admin &&

    #如果创建成功，显示出评判机的口令，使用python manage.py shell 启动解释器之前，它告诉Django使用哪个设置文件
    # 先执行python manage.py shell打开shell，再在shell上面执行 echo "..." 更新口令和任务数目
    echo "from options.options import SysOptions; SysOptions.judge_server_token='$JUDGE_SERVER_TOKEN'" | python3 manage.py shell &&
    echo "from conf.models import JudgeServer; JudgeServer.objects.update(task_number=0)" | python3 manage.py shell &&
    break
    #总共尝试5次
    n=$(($n+1))
    echo "Failed to migrate, going to retry..."
    sleep 8
done

#设置用户组和用户
# 增加用户组spj， gid=12003
# 增加用户server，uid=12000 指定用户登录之后使用的shell和归属的用户组spj
# 注意在Ubuntu和alpine的设置用户和组的命令是不同的
# 由于已经设置好了，下面将其注释

groupadd -g 12003 spj
useradd server -g spj -u 12000 -s /bin/bash

#更改目录的拥有者：
# chown -R 用户名:组名
# -R处理指定目录以及其子目录下的所有文件，将$DATA $APP/dist的使用权归为server，以及所属组spj
# 将目录$DATA/test_case下的-type一般目录-d和文件-f列出，目录更改权限710，文件更改权限640
# a=User、b=Group、c=Other,r=4，w=2，x=1
chown -R server:spj $DATA $APP/dist
find $DATA/test_case -type d -exec chmod 710 {} \;
find $DATA/test_case -type f -exec chmod 640 {} \;

#启动supervisor
exec supervisord -c /home/toohoo/PycharmProjects/ICQBPMSSOJ/deploy/supervisord.conf
