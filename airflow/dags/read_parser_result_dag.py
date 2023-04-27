from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.contrib.sensors.python_sensor import PythonSensor
from airflow.utils.log.logging_mixin import LoggingMixin
from datetime import datetime


def delivery_report(errmsg, msg):
    """
    Reports the Failure or Success of a message delivery.
    Args:
        errmsg  (KafkaError): The Error that occurred while message producing.
        msg    (Actual message): The message that was produced.
    Note:
        In the delivery report callback the Message.key() and Message.value()
        will be the binary format as encoded by any configured Serializers and
        not the same object that was passed to produce().
        If you wish to pass the original object(s) for key and value to delivery
        report callback we recommend a bound callback or lambda where you pass
        the objects along.
    """
    if errmsg is not None:
        print("Delivery failed for Message: {} : {}".format(msg.key(), errmsg))
        return
    print('Message: {} successfully produced to Topic: {} Partition: [{}] at offset {}'.format(
        msg.key(), msg.topic(), msg.partition(), msg.offset()))


def _wait_for_json(**kwargs):
    from pathlib import Path

    ti = kwargs['ti']
    path_ = Path("./result")
    data_files = path_.glob("*.json")
    files = [str(i) for i in data_files]
    LoggingMixin().log.info(f'Find files {files}')
    ti.xcom_push(key='files', value=files)
    return bool(files)


def extract_data(**kwargs):
    import json

    ti = kwargs['ti']
    list_files = ti.xcom_pull(key='files', task_ids=['_wait_for_json'])[0]
    data = []
    for file in list_files:
        with open(file) as f:
            reader = json.loads(f.read())
            data.append(reader)
    print(data)
    print(list_files)
    if list_files:
        ti.xcom_push(key='files', value=list_files)
        ti.xcom_push(key='data', value=data)
    else:
        raise Warning('No files to process')


def transform_data(**kwargs):
    ti = kwargs['ti']
    data_taken = ti.xcom_pull(key='data', task_ids=['extract_data'])[0]
    final_data = []
    for file_data_taken in data_taken:
        for data in file_data_taken:
            dict_to_add = {}
            for group in data["groups"]:
                for score_ind in range(len(group["name"])):
                    dict_to_add["semester"] = data["semester"]
                    dict_to_add["course_name"] = data["course_name"]
                    dict_to_add["group_name"] = group["name"].strip()
                    dict_to_add["score"] = group["score"]
                    dict_to_add["final_score"] = group["final"]
            final_data.append(dict_to_add)

    LoggingMixin().log.info(f'Find data {final_data}')
    ti.xcom_push(key='data', value=final_data)


def load_data(**kwargs):
    from json import dumps
    from uuid import uuid4
    from confluent_kafka import Producer

    kafka_topic_name = 'tsuscore'
    conf = {
        'bootstrap.servers': 'kafka:29092'
    }
    producer = Producer(conf)

    ti = kwargs['ti']
    data_taken = ti.xcom_pull(key='data', task_ids=['transform_data'])[0]
    for data in data_taken:
        producer.produce(topic=kafka_topic_name, key=str(uuid4()), value=str(data).encode(), on_delivery=delivery_report)
        LoggingMixin().log.info(f'produce to kafka {data}')
    producer.flush()


def del_json_files(**kwargs):
    import os

    ti = kwargs['ti']
    for file in ti.xcom_pull(key='files', task_ids=['extract_data'])[0]:
        os.remove(file)


# Following are defaults which can be overridden later on
args = {
    'owner': 'nikita',
    'start_date': datetime(2022, 1, 1),
    'provide_context': True
}


with DAG('etl_data', description='extract transform load data parsed from tsu', schedule_interval='*/1 * * * *',
         catchup=False, default_args=args) as dag:  # 0 * * * *   */1 * * * *

    sensor_data = PythonSensor(
        task_id="_wait_for_json",
        python_callable=_wait_for_json,
        poke_interval=30,
        timeout=1 * 60,
        mode='reschedule'
    )
    extract = PythonOperator(
        task_id='extract_data',
        python_callable=extract_data)
    transform = PythonOperator(
        task_id='transform_data',
        python_callable=transform_data)
    load = PythonOperator(
        task_id='load_data',
        python_callable=load_data)
    del_json = PythonOperator(
        task_id='del_json_files',
        python_callable=del_json_files)

    sensor_data >> extract
    extract >> transform
    transform >> load
    load >> del_json