from typing import Callable

import aio_pika
from pika.exchange_type import ExchangeType

from philiarabbit.base import PhiliaRabbitBase


class PhiliaRabbitConsumer(PhiliaRabbitBase):

    def __init__(
            self,
            rabbit_url: str,
            queue_name: str,
            exchange_name: str = "",
            routing_keys: list = [],
            exchange_type: ExchangeType | None = None,
            qos: int = 1
    ) -> None:
        self.rabbit_url = rabbit_url
        self.queue_name = queue_name
        self.exchange_name = exchange_name
        self.is_default_exchange = not bool(self.exchange_name)
        # setup method calls
        if not isinstance(routing_keys, list):
            raise ValueError("routing_keys must be a list")
        self._setup_queue(
            routing_keys=routing_keys,
            exchange_type=exchange_type,
            qos=qos,
        )

    def _get_channel(self):
        if self.connection is None:
            self.connection = self._connect()
        
        self.connection = self._check_connection(self.connection)
        if self.channel is None and self.connection is not None:
            self.channel = self.connection.channel()

    def _setup_queue(
            self,
            routing_keys: list[str] = [],
            exchange_type: ExchangeType | None = None,
            qos: int = 1
    ):
        self._get_channel()
        self.channel.basic_qos(prefetch_count=qos)

        queue = self.channel.queue_declare(
            self.queue_name, 
            durable=True,
            auto_delete=False,
        )
        
        # automatic binding queue to exchange
        if not self.is_default_exchange:
            if not exchange_type:
                raise ValueError("exchange_type cannot be none for declaring")
            self.channel.exchange_declare(
                self.exchange_name,
                exchange_type,
                durable=True
            )
            routing_keys = routing_keys if routing_keys else [self.queue_name]
            for routing_key in routing_keys:
                self.channel.queue_bind(
                    queue=self.queue_name,
                    exchange=self.exchange_name,
                    routing_key=routing_key
                )

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
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=callback,
            auto_ack=auto_ack
        )
        try:
            self.channel.start_consuming()
        finally:
            self._disconnect()


class AsyncPhiliaRabbitConsumer:

    def __init__(
            self,
            rabbit_url: str,
            queue_name: str,
            exchange_name: str = "",
            routing_keys: list = [],
            exchange_type: aio_pika.ExchangeType | None = None,
            qos: int = 1
    ) -> None:
        self.rabbit_url = rabbit_url
        self.queue_name = queue_name
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type
        self.qos = qos
        self.is_default_exchange = not bool(self.exchange_name)
        if not isinstance(routing_keys, list):
            raise ValueError("routing_keys must be a list")
        self.routing_keys = routing_keys

    async def _get_channel(self):
        connection = await aio_pika.connect_robust(self.rabbit_url)
        return await connection.channel()

    async def _get_queue(self):
        channel = await self._get_channel()
        await channel.set_qos(prefetch_count=self.qos)

        queue = await channel.declare_queue(self.queue_name, durable=True)
        if not self.is_default_exchange:
            if not self.exchange_type:
                raise ValueError("exchange_type cannot be none for declaring")
            exchange = await channel.declare_exchange(
                self.exchange_name,
                self.exchange_type,
                durable=True
            )

            routing_keys = self.routing_keys if self.routing_keys else [self.queue_name]
            for routing_key in routing_keys:
                await queue.bind(exchange, routing_key=routing_key)

        return queue

    async def run(self, callback: Callable):
        queue = await self._get_queue()
        print("Starting RabbitMQ Consumer Asyncly")
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    await callback(
                        message.body
                    )
                    # TODO : get callback for handling exception
