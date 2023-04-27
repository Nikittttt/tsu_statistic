# Боль. На докере убунты BASH_VERSION не установлен как env, из-за этого greenplum_path.sh отказывается работать
# Можно было бы настроить вручную, но имхо это костыль и не факт что только это пришлось бы настраивать
# вполне возможно есть такая же проблема, которую потом было бы сложно выявить
# p.s. Я не забыл удалить этот файл, просто оставил его для истории
FROM ubuntu:18.04

RUN apt update
RUN apt install software-properties-common -y
RUN add-apt-repository ppa:greenplum/db -y

RUN apt update
ARG GP_V=6.23.4
ARG GP_V_APT=$GP_V-1
RUN apt install greenplum-db-6=$GP_V_APT -y

WORKDIR /home/gpadmin
#RUN ["chmod", "777", "/opt/greenplum-db-$GP_V/greenplum_path.sh"]
ENV GPHOME /opt/greenplum-db-$GP_V
RUN /bin/bash -c "source /opt/greenplum-db-$GP_V/greenplum_path.sh"

ADD $GPHOME/docs/cli_help/gpconfigs/gpinitsystem_singlenode .

ENV MACHINE_LIST_FILE=./hostlist_singlenode
RUN "declare -a DATA_DIRECTORY=(/home/gpadmin/primary /home/gpadmin/primary)"
ENV MASTER_HOSTNAME=ubuntu
ENV MASTER_DIRECTORY=/home/gpadmin/master

RUN "gpssh-exkeys -h localhost"
#RUN "gpinitsystem -c gpinitsystem_singlenode"