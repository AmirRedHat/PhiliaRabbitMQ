import logging
from typing import Any

import pika
from pika.delivery_mode import DeliveryMode
import aio_pika

from philiarabbit.base import PhiliaRabbitBase


class PhiliaRabbitProducer(PhiliaRabbitBase):

    def __init__(
            self,
            rabbit_url: str,
            routing_key: str = "Default",
            exchange_name: str = "",
            connection_pool: Any = None,
            logger: logging.Logger | None = None,
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
        self.logger = logger
        if (
                self.pool is not None and
                (
                    not hasattr(self.pool, "get_connection") or
                    not hasattr(self.pool, "release")
                )
        ):
            raise ValueError("invalid connection pool structure "
                             "| get_connection() and release() is required")

    def connect(self):
        """ 
            Get connection and make channel and setup them on self.connection and self.channel variable
        """
        if self.pool is not None:
            self._log("[+] Getting connection from pool")
            self.connection = self.pool.get_connection()
            self.connection = self._check_connection(self.connection)
            if self.connection is None:
                raise ValueError("connection cannot be none")
            self.channel = self.connection.channel()
            return
        self._connect(make_channel=True)

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
                self._disconnect()


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
