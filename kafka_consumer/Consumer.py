from confluent_kafka import Consumer
#import greenplumpython as gp

from json import loads
import os

conf = {'bootstrap.servers': "kafka:29092",
        'group.id': "tsuscore",
        'auto.offset.reset': 'smallest'}

consumer = Consumer(conf)

#consumer = KafkaConsumer(
#    'tsuscore',
#    bootstrap_servers=['localhost:29092'],
#    auto_offset_reset='earliest',
#    enable_auto_commit=True,
#    group_id='my-group',
#    value_deserializer=lambda x: loads(x.decode('utf-8')))

#db = gp.database(
#        params={
#          "host": os.getenv('GREENPLUM_HOST'),
#          "dbname": os.getenv('GREENPLUM_DB'),
#          "user": os.getenv('GREENPLUM_USER'),
#          "password": os.getenv('PGPASSWORD'),
#          "port": 5433,
#        }
#)
#cursor = db.cursor()
#cursor.execute("CREATE TABLE IF NOT EXISTS "
#               "score_table("
#               "semester text NOT NULL,"
#               "course_name text NOT NULL,"
#               "group_name text NOT NULL,"
#               "final_score int NOT NULL,"
#               "score int[]) ;")


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
            # Extract the (optional) key and value, and print.

            print("Consumed event from topic {topic}: key = {key:12} value = {value:12}".format(
                topic=msg.topic(), key=msg.key().decode('utf-8'), value=msg.value().decode('utf-8')))
except KeyboardInterrupt:
    pass
finally:
    # Leave group and commit final offsets
    consumer.close()
