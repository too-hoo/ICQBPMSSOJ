#! /bin/bash
# 开发环境的数据库初始化
set -x

if [[ ! -f manage.py ]]; then
     echo "No manage.py, wrong location!"
     exit 1
fi

sleep 2
docker rm -f icqbpmssoj-postgres-dev icqbpmssoj-redis-dev
docker run -it -d -e POSTGRES_DB=icqbpmssoj -e POSTGRES_USER=icqbpmssoj -e POSTGRES_PASSWORD=icqbpmssoj -p 127.0.0.1:5435:5432 --name icqbpmssoj-postgres-dev postgres:10-alpine
docker run -it -d -p 127.0.0.1:6380:6379 --name icqbpmssoj-redis-dev redis:4.0-alpine

# 如果传入的第一个参数是migrate就创建数据库，否则就只是构建数据库镜像
# 注意：管道的执行顺序是从右边往左边执行的：head -c 32++ md5sum++ head -1++ cat /dev/urandom

if [ "$1" = "--migrate" ]; then
    sleep 3
    echo `cat /dev/urandom | head -1 | md5sum | head -c 32` > data/config/secret.key
    python manage.py migrate
    python manage.py inituser --username root --password root123 --action create_super_admin
fi