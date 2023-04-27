FROM python:3.10

ADD requirements.txt /tmp/requirements.txt

RUN pip install --upgrade -r /tmp/requirements.txt

#RUN createdb -h ${GREENPLUM_HOST} -U ${GREENPLUM_USER} ${POSTGRES_DB}
add . .

#RUN python /tmp/Consumer.py