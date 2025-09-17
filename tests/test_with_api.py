import logging
import sys
from flask import Flask, json

from philiarabbit.producer import PhiliaRabbitProducer

sys.path.insert(0, '../')
from philiarabbit.connection_pool import (
    PhiliaRabbitConnectionPool
)


RABBIT_URL = "amqp://guest:guest@localhost:5672"
app = Flask(__name__)
logger = logging.getLogger(__name__)
pool = PhiliaRabbitConnectionPool(
    rabbit_url=RABBIT_URL,
    max_size=20,
    logger=logger
)


@app.route("/cp")
def test_connection_pool():
    connection, channel = pool.get_connection_with_channel()
    data = {
        "connection_is_open": connection.is_open,
        "channel_is_open": channel.is_open,
    }
    channel.close()
    pool.release(connection)
    return data

@app.route("/pro")
def test_producer():
    PhiliaRabbitProducer(
        rabbit_url=RABBIT_URL,
        connection_pool=pool
    ).publish(json.dumps({"data": {"amir": "hosein"}}).encode())
    return {"detail": "message published"}