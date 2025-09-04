import logging
import sys
from flask import Flask, jsonify

sys.path.insert(0, '../')
from philiarabbit.connection_pool import (
    PhiliaRabbitConnectionPool
)

app = Flask(__name__)
logger = logging.getLogger(__name__)
pool = PhiliaRabbitConnectionPool(
    rabbit_url="amqp://root:root@localhost:5672",
    max_size=2,
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
