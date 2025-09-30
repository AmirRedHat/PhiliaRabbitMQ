import logging
from queue import Queue
from queue import Empty
from threading import Lock

import pika

from asyncio import Queue as AsyncQueue
from asyncio.queues import QueueEmpty as AsyncQueueEmpty
from asyncio import Lock as AsyncLock
import aio_pika
from aio_pika.abc import AbstractRobustConnection
from aio_pika.exceptions import (
    AMQPConnectionError as AMQPConnectionErrorAsync,
    ConnectionClosed as ConnectionClosedAsync
)

from philiarabbit.base import PhiliaRabbitBase


class PhiliaRabbitConnectionPool(PhiliaRabbitBase):

    def __init__(
            self,
            rabbit_url: str,
            max_size: int = 3,
            logger: logging.Logger | None = None,
    ):
        self.logger = logger
        self.rabbit_url = rabbit_url
        self.max_size = max_size
        self.queue = Queue(maxsize=self.max_size)
        self._create_connections()
        self.lock = Lock()

    def _create_connections(self):
        for _ in range(self.max_size):
            # don't block the process if there is no any slot to put connection on
            self.queue.put_nowait(
                self._connect()
            )
        self._log(f"{self.max_size} connections created")

    def get_connection(self):
        with self.lock:
            try:
                connection = self.queue.get(block=False)
            except Empty:
                return self._connect()

        return self._check_connection(connection)

    def get_connection_with_channel(self):
        connection = self.get_connection()
        if connection is None:
            raise ValueError("connection cannot be none")
        return connection, connection.channel()

    def release(self, connection: pika.BlockingConnection | None):
        self.queue.put_nowait(
            self._check_connection(connection)
        )


class AsyncPhiliaRabbitConnectionPool:

    def __init__(
            self,
            rabbit_url: str,
            max_size: int = 3,
            logger: logging.Logger | None = None,
    ):
        self.logger = logger
        self.rabbit_url = rabbit_url
        self.max_size = max_size
        self.queue = AsyncQueue(maxsize=self.max_size)
        self.lock = AsyncLock()

    async def _log(self, *args, **kwargs):
        if self.logger is not None:
            self.logger.warning(*args, **kwargs)

    async def _get_connection(self):
        return await aio_pika.connect_robust(
            url=self.rabbit_url,
            heartbeat=60,
            timeout=300
        )

    async def _ensure_connection_is_ok(self, connection: AbstractRobustConnection):
        try:
            if connection.is_closed:
                return await self._get_connection()
            return connection
        except (
                ConnectionClosedAsync,
                AMQPConnectionErrorAsync,
                OSError,
        ):
            await self._log(f"[!] Connection is corrupted: {connection.is_closed=} | Reconnecting...")
            return self._get_connection()

    async def _create_connections(self):
        for _ in range(self.max_size):
            # don't block the process if there is no any slot to put connection on
            await self.queue.put(
                self._get_connection()
            )

    async def get_connection(self):
        async with self.lock:
            try:
                connection = await self.queue.get()
            except AsyncQueueEmpty:
                return await self._get_connection()

        return await self._ensure_connection_is_ok(connection)

    async def get_connection_with_channel(self):
        connection = await self.get_connection()
        return connection, await connection.channel()

    async def release(self, connection):
        await self.queue.put(
            await self._ensure_connection_is_ok(connection)
        )
