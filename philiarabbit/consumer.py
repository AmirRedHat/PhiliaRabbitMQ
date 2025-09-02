from typing import Callable

import aio_pika
import pika


class PhiliaRabbitConsumer:

    def __init__(self, rabbit_url: str, queue_name: str, exchange_name: str = "") -> None:
        self.rabbit_url = rabbit_url
        self.queue_name = queue_name
        self.exchange_name = exchange_name
        # internal variables
        self.connection = None
        self.channel = None
        # setup method calls
        self._setup_queue()


    def _get_channel(self):
        if self.connection is None:
            self.connection = pika.BlockingConnection(
                pika.URLParameters(self.rabbit_url)
            )
        if self.channel is None:
            self.channel = self.connection.channel()

    def _setup_queue(self, routing_keys: list[str] = None, qos: int = 1):
        self._get_channel()
        self.channel.basic_qos(prefetch_count=qos)

        queue = self.channel.queue_declare(self.queue_name, durable=True)
        self.channel.exchange_declare(
            self.exchange_name,
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )

        routing_keys = routing_keys or [self.queue_name]
        for routing_key in routing_keys:
            self.channel.queue_bind(
                queue=self.queue_name,
                exchange=self.exchange_name,
                routing_key=routing_key
            )

        return queue

    def run(self, callback: Callable, auto_ack: bool = True):
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=callback,
            auto_ack=auto_ack
        )
        self.channel.start_consuming()


class PhiliaRabbitConsumerAsync:

    def __init__(self, rabbit_url: str, queue_name: str, exchange_name: str = "") -> None:
        self.rabbit_url = rabbit_url
        self.queue_name = queue_name
        self.exchange_name = exchange_name

    async def _get_channel(self):
        connection = await aio_pika.connect_robust(self.rabbit_url)
        return await connection.channel()

    async def _get_queue(self, routing_keys: list[str] = None, qos: int = 1):
        channel = await self._get_channel()
        await channel.set_qos(prefetch_count=qos)

        queue = await channel.declare_queue(self.queue_name, durable=True)
        exchange = await channel.declare_exchange(
            self.exchange_name,
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )

        routing_keys = routing_keys or [self.queue_name]
        for routing_key in routing_keys:
            await queue.bind(exchange, routing_key=routing_key)

        return queue

    async def run(self, callback: Callable, routing_keys: list[str] = None, qos: int = 1):
        queue = await self._get_queue(routing_keys=routing_keys, qos=qos)
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    await callback(
                        message.body
                    )
                    # TODO : get callback for handling exception