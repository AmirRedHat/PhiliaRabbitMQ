from typing import Callable

import aio_pika
import pika
from pika.exchange_type import ExchangeType


class PhiliaRabbitConsumer:

    def __init__(
            self,
            rabbit_url: str,
            queue_name: str,
            exchange_name: str = "",
            routing_keys: list = None,
            exchange_type: ExchangeType = None,
            qos: int = 1
    ) -> None:
        self.rabbit_url = rabbit_url
        self.queue_name = queue_name
        self.exchange_name = exchange_name
        # internal variables
        self.connection = None
        self.channel = None
        # setup method calls
        self._setup_queue(
            routing_keys=routing_keys,
            exchange_type=exchange_type,
            qos=qos,
        )

    def _get_channel(self):
        if self.connection is None:
            self.connection = pika.BlockingConnection(
                pika.URLParameters(self.rabbit_url)
            )
        if self.channel is None:
            self.channel = self.connection.channel()

    def _close_connections(self):
        if self.connection is not None and self.connection.is_open:
            self.connection.close()
        if self.channel is not None and self.channel.is_open:
            self.channel.close()

    def _setup_queue(
            self,
            routing_keys: list[str] = None,
            exchange_type: ExchangeType = None,
            qos: int = 1
    ):
        self._get_channel()
        self.channel.basic_qos(prefetch_count=qos)

        queue = self.channel.queue_declare(self.queue_name, durable=True)
        self.channel.exchange_declare(
            self.exchange_name,
            exchange_type,
            durable=True
        )

        routing_keys = routing_keys or [self.queue_name]
        for routing_key in routing_keys:
            self.channel.queue_bind(
                queue=self.queue_name,
                exchange=self.exchange_name,
                routing_key=routing_key
            )
            print(f"{routing_key=} | {self.queue_name=} | {self.exchange_name=}")

        return queue

    def run(self, callback: Callable, auto_ack: bool = True):
        """

        def consumer_callback(ch, method, properties, body):
            ...
            # body is data received from producer

        :param callback: the function to call
        :param auto_ack: auto_ack parameter in rabbit consumer
        :return: none
        """
        print("Starting RabbitMQ Consumer")
        try:
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=callback,
                auto_ack=auto_ack
            )
            self.channel.start_consuming()
        finally:
            self._close_connections()


class AsyncPhiliaRabbitConsumer:

    def __init__(
            self,
            rabbit_url: str,
            queue_name: str,
            exchange_name: str = "",
            routing_keys: list = None,
            exchange_type: aio_pika.ExchangeType = None,
            qos: int = 1
    ) -> None:
        self.rabbit_url = rabbit_url
        self.queue_name = queue_name
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type
        self.qos = qos
        self.routing_keys = routing_keys

    async def _get_channel(self):
        connection = await aio_pika.connect_robust(self.rabbit_url)
        return await connection.channel()

    async def _get_queue(self):
        channel = await self._get_channel()
        await channel.set_qos(prefetch_count=self.qos)

        queue = await channel.declare_queue(self.queue_name, durable=True)
        exchange = await channel.declare_exchange(
            self.exchange_name,
            self.exchange_type,
            durable=True
        )

        routing_keys = self.routing_keys or [self.queue_name]
        for routing_key in routing_keys:
            await queue.bind(exchange, routing_key=routing_key)

        return queue

    async def run(self, callback: Callable):
        queue = await self._get_queue()
        print("Starting RabbitMQ Consumer")
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    await callback(
                        message.body
                    )
                    # TODO : get callback for handling exception
