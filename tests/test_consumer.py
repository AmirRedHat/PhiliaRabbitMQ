import sys

from pika.exchange_type import ExchangeType

sys.path.insert(0, '../')

from philiarabbit.consumer import PhiliaRabbitConsumer, AsyncPhiliaRabbitConsumer



RABBIT_URL = "amqp://guest:guest@localhost:5672"
def start_consumer():

    def consumer_callback(ch, method, properties, body):
        print("consumer callback")
        print("data:")
        print(body)

    consumer = PhiliaRabbitConsumer(
        rabbit_url=RABBIT_URL,
        queue_name="test_queue",
        exchange_name="exchange_test",
        routing_keys=["data.*"],
        exchange_type=ExchangeType.topic
    )
    consumer.run(consumer_callback)

def start_consumer_with_default_exchange():
    def consumer_callback(ch, method, properties, body):
        print("consumer callback")
        print("data:")
        print(body)

    consumer = PhiliaRabbitConsumer(
        rabbit_url=RABBIT_URL,
        queue_name="Default",
        exchange_name="",
        exchange_type=ExchangeType.topic
    )
    consumer.run(consumer_callback)


async def async_start_consumer():
    async def consumer_callback(body):
        print("consumer callback")
        print("data:")
        print(body)

    consumer = AsyncPhiliaRabbitConsumer(
        rabbit_url=RABBIT_URL,
        queue_name="test_queue",
        exchange_name="exchange_test",
        routing_keys=["data.*"],
        exchange_type=ExchangeType.topic
    )
    await consumer.run(consumer_callback)


if __name__ == "__main__":
    ...
    # start_consumer()
    # asyncio.run(async_start_consumer())
    start_consumer_with_default_exchange()