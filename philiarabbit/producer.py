from typing import Any

import pika
from pika.delivery_mode import DeliveryMode

import aio_pika


class PhiliaRabbitProducer:

    def __init__(
            self,
            rabbit_url: str = None,
            queue_name: str = None,
            routing_key: str = None,
            exchange: str = None,
            connection_pool: Any = None
    ):
        """
            generate an instance of philia rabbit class
            :param rabbit_url: the url of rabbitmq instance
            :param routing_key: the routing_key that you want to send data
            :param exchange: destination exchange
            :param connection_pool: connection pool class. in this class you must have get_connection()
            and release() methods (async).
        """
        self.rabbit_url = rabbit_url
        self.queue_name = queue_name
        self.routing_key = routing_key
        self.exchange = exchange
        self.pool = connection_pool
        if not hasattr(self.pool, "get_connection") or not hasattr(self.pool, "release"):
            raise ValueError("invalid connection pool structure "
                             "| get_connection() and release() is required")

        # internal variables
        self.connection = None
        self.channel = None

    def _connect(self):
        self.connection = pika.BlockingConnection(
            pika.URLParameters(self.rabbit_url)
        )
        self.channel = self.connection.channel()

    def connect(self):
        if self.pool is not None:
            self.connection = self.pool.get_connection()
            self.channel = self.connection.channel()
        # TODO: implement retry mechanism
        self._connect()

    def disconnect(self):
        if self.channel and self.channel.is_open:
            self.channel.close()

        if self.pool is not None:
            self.pool.release(self.connection)
            return

        if self.connection and self.connection.is_open:
            self.connection.close()

    def publish(self, data: Any, disconnect: bool = True):
        if self.connection is None or self.channel is None:
            self.connect()
        try:
            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=self.routing_key,
                body=data,
                properties=pika.BasicProperties(
                    delivery_mode=DeliveryMode.Persistent,
                ),
            )
        finally:
            if disconnect:
                self.disconnect()


class PhiliaRabbitProducerAsync:

    def __init__(
            self,
            rabbit_url: str = None,
            routing_key: str = None,
            exchange: str = None,
            connection_pool: Any = None
    ):
        """
        generate an instance of philia rabbit class
        :param rabbit_url: the url of rabbitmq instance
        :param routing_key: the routing_key that you want to send data
        :param exchange: destination exchange
        :param connection_pool: connection pool class. in this class you must have get_connection()
        and release() methods (async).
        """
        self.rabbit_url = rabbit_url
        self.routing_key = routing_key
        self.exchange = exchange
        self.pool = connection_pool
        if not hasattr(self.pool, "get_connection") or not hasattr(self.pool, "release"):
            raise ValueError("invalid connection pool structure "
                             "| get_connection() and release() is required")

        # internal variables
        self.connection = None
        self.channel = None

    async def _connect(self, loop=None):
        self.connection = await aio_pika.connect_robust(
            url=self.rabbit_url,
            loop=None
        )
        self.channel = await self.connection.channel()

    async def connect(self):
        if self.pool is not None:
            self.connection = await self.pool.get_connection()
            self.channel = await self.connection.channel()
        # TODO: implement retry mechanism
        await self._connect()

    async def disconnect(self):
        if self.channel and self.channel.is_open:
            await self.channel.close()

        if self.pool is not None:
            await self.pool.release(self.connection)
            return

        if self.connection and self.connection.is_open:
            await self.connection.close()

    async def publish(self, data: Any, disconnect: bool = True):
        if self.connection is None or self.channel is None:
            await self.connect()
        try:
            await self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=self.routing_key,
                body=data,
                properties=pika.BasicProperties(
                    delivery_mode=DeliveryMode.Persistent,
                ),
            )
        finally:
            if disconnect:
                await self.disconnect()
