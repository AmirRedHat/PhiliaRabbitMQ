

# Documentation:
https://github.com/AmirRedHat/PhiliaRabbitMQ

# Description
This project made for philia.
In this project we package the rabbitmq utils.
* producer 
* consumer 
* connection pool

# Consumer 
The consumer implemented in two version (sync and async).
Both of them accept an `callback` function as argument and received data from producer 
will pass to callback


Sync Version : 
```python
def consumer_callback(ch, method, properties, body):
    ...
    # body is received data from producer

from philiarabbit.consumer import PhiliaRabbitConsumer
from pika.exchange_type import ExchangeType
consumer = PhiliaRabbitConsumer(
    rabbit_url="",
    queue_name="",
    exchange_name="",
    routing_keys=[],
    exchange_type=ExchangeType.topic  # TOPIC or DIRECT
)
consumer.run(consumer_callback)
```

Async Version :
```python
async def consumer_callback(body):
    ...
    # body is received data from producer

from philiarabbit.consumer import AsyncPhiliaRabbitConsumer
import aio_pika
import asyncio
consumer = AsyncPhiliaRabbitConsumer(
    rabbit_url="",
    queue_name="",
    exchange_name="",
    routing_keys=[],
    exchange_type=aio_pika.ExchangeType.TOPIC  # TOPIC or DIRECT
)
asyncio.run(consumer.run(consumer_callback))
```

# Producer
The producer is implemented in two version (sync and async).
just define exchange_name and routing_key then publish the message.
you can also manage the connections by passing connection pool object.


# Connection Pool
The connection pool is implemented in two version (sync and async).
This class will manage your rabbitmq connections and keep them in queue for heavy-call
cases

Example : 
```python
from philiarabbit.connection_pool import PhiliaRabbitConnectionPool
pool = PhiliaRabbitConnectionPool(
    rabbit_url="",
    max_size=2,
    logger=None  # you can pass a logger instance
)
connection, channel = pool.get_connection_with_channel()
# you can use the connection and channel in your codebase
```

Example of connection pool with producer :
```python
from philiarabbit.connection_pool import PhiliaRabbitConnectionPool
pool = PhiliaRabbitConnectionPool(
    rabbit_url="",
    max_size=2,
    logger=None  # you can pass a logger instance
)

from philiarabbit.producer import PhiliaRabbitProducer
producer = PhiliaRabbitProducer(
        rabbit_url="",
        routing_key="",
        exchange_name="",
    )
producer.publish(data=bytes)
```

# Test
The integration tests wrote in `/tests/` directory.