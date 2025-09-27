from typing import Any

import pika
from pika.delivery_mode import DeliveryMode
from pika.exceptions import StreamLostError, ConnectionClosed, AMQPConnectionError

import aio_pika


class PhiliaRabbitProducer:

    def __init__(
            self,
            rabbit_url: str,
            routing_key: str = "Default",
            exchange_name: str = "",
            connection_pool: Any = None
    ):
        """
            generate an instance of philia rabbit class
            :param rabbit_url: the url of rabbitmq instance
            :param routing_key: the routing_key that you want to send data
            :param exchange_name: destination exchange
            :param connection_pool: connection pool class. in this class you must have get_connection()
            and release() methods (async).
        """
        self.rabbit_url = rabbit_url
        self.routing_key = routing_key
        self.exchange_name = exchange_name
        self.pool = connection_pool
        if (
                self.pool is not None and
                (
                    not hasattr(self.pool, "get_connection") or
                    not hasattr(self.pool, "release")
                )
        ):
            raise ValueError("invalid connection pool structure "
                             "| get_connection() and release() is required")

        # internal variables
        self.connection = None
        self.channel = None
        
    def _check_connection(self, connection: pika.BlockingConnection):
        try:
            if not connection.is_open:
                return self._connect(make_channel=False)
            connection.process_data_events(0)
            return connection
        except (
                StreamLostError,
                AttributeError,
                ConnectionClosed,
                AMQPConnectionError,
                OSError,
        ):
            print("- reconnecting in _check_connection()...")
            return self._connect(make_channel=False)

    def _connect(self, make_channel: bool = True):
        self.connection = pika.BlockingConnection(
            pika.URLParameters(self.rabbit_url)
        )
        if make_channel:
            self.channel = self.connection.channel()

    def connect(self):
        if self.pool is not None:
            self.connection = self.pool.get_connection()
            self.connection = self._check_connection(self.connection)
            self.channel = self.connection.channel()
            return
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
                exchange=self.exchange_name,
                routing_key=self.routing_key,
                body=data,
                properties=pika.BasicProperties(
                    delivery_mode=DeliveryMode.Persistent,
                ),
            )
        finally:
            if disconnect:
                self.disconnect()


class AsyncPhiliaRabbitProducer:

    def __init__(
            self,
            rabbit_url: str,
            routing_key: str = "Default",
            exchange_name: str = "",
            connection_pool: Any = None
    ):
        """
        generate an instance of philia rabbit class
        :param rabbit_url: the url of rabbitmq instance
        :param routing_key: the routing_key that you want to send data
        :param exchange_name: destination exchange
        :param connection_pool: connection pool class. in this class you must have get_connection()
        and release() methods (async).
        """
        self.rabbit_url = rabbit_url
        self.routing_key = routing_key
        self.exchange_name = exchange_name
        self.pool = connection_pool
        if (
                self.pool is not None and
                (
                        not hasattr(self.pool, "get_connection") or
                        not hasattr(self.pool, "release")
                )
        ):
            raise ValueError("invalid connection pool structure "
                             "| get_connection() and release() is required")

        # internal variables
        self.connection = None
        self.channel = None

    async def _connect(self, loop=None):
        self.connection = await aio_pika.connect_robust(
            url=self.rabbit_url,
            loop=loop
        )
        self.channel = await self.connection.channel()

    async def connect(self, loop=None):
        if self.pool is not None:
            self.connection = await self.pool.get_connection()
            self.channel = await self.connection.channel()
            return
        # TODO: implement retry mechanism
        await self._connect(loop=loop)

    async def disconnect(self):
        if self.channel and self.channel.is_open:
            await self.channel.close()

        if self.pool is not None:
            await self.pool.release(self.connection)
            return

        if self.connection and self.connection.is_open:
            await self.connection.close()

    async def publish(self, data: bytes, disconnect: bool = True):
        if self.connection is None or self.channel is None:
            await self.connect()
        try:
            await self.channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=self.routing_key,
                body=data,
                properties=pika.BasicProperties(
                    delivery_mode=DeliveryMode.Persistent,
                ),
            )
        finally:
            if disconnect:
                await self.disconnect()
