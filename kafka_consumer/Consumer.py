from confluent_kafka import Consumer
import psycopg2
from datetime import datetime

from json import loads
import os

conf = {'bootstrap.servers': "kafka:29092",
        'group.id': "tsuscore",
        'auto.offset.reset': 'smallest'}

consumer = Consumer(conf)

greenplum = psycopg2.connect(
    host=os.getenv('GREENPLUM_HOST'),
    database=os.getenv('GREENPLUM_DB'),
    user=os.getenv('GREENPLUM_USER'),
    password=os.getenv('PGPASSWORD'))
cursor = greenplum.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS "
               "score_table("
               "created_at TIMESTAMP DEFAULT now(),"
               "semester text NOT NULL,"
               "course_name text NOT NULL,"
               "group_name text NOT NULL,"
               "final_score int NOT NULL,"
               "score int[]) ;")


# Subscribe to topic
topic = "tsuscore"
consumer.subscribe([topic])

# Poll for new messages from Kafka and print them.
try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            # Initial message consumption may take up to
            # `session.timeout.ms` for the consumer group to
            # rebalance and start consuming
            print("Waiting...")
        elif msg.error():
            print("ERROR: %s".format(msg.error()))
        else:
            print("Consumed event from topic {topic}: key = {key:12} value = {value:12}".format(
                topic=msg.topic(), key=msg.key().decode('utf-8'), value=msg.value().decode('utf-8')))

            data = loads(msg.value().decode('utf-8').replace("\'", "\"").replace('None', 'null'))
            for i in range(len(data["final_score"])):
                cursor.execute(
                    "INSERT INTO score_table("
                                    "semester, "
                                    "course_name, "
                                    "group_name, "
                                    "final_score, "
                                    "score) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (data["semester"],
                     data["course_name"],
                     data["group_name"],
                     data["final_score"][i],
                     [int(i) if type(i) == str else None for i in data["score"][i]]))

except KeyboardInterrupt:
    pass
finally:
    # Leave group and commit final offsets
    consumer.close()
    greenplum.close()
