from queue import Queue
from threading import Lock

import pika

from asyncio import Queue as AsyncQueue
from asyncio import Lock as AsyncLock
import aio_pika


class PhiliaRabbitConnectionPool:

    def __init__(self, rabbit_url: str, max_size: int = 3):
        self.rabbit_url = rabbit_url
        self.max_size = max_size
        self.queue = Queue(maxsize=self.max_size)
        self._create_connections()
        self.lock = Lock()

    def _get_connection(self):
        return pika.BlockingConnection(self._get_parameters())

    def _create_connections(self):
        for _ in range(self.max_size):
            # don't block the process if there is no any slot to put connection on
            self.queue.put_nowait(
                self._get_connection()
            )

    def _get_parameters(self):
        params = pika.URLParameters(self.rabbit_url)
        params.heartbeat = 30
        params.blocked_connection_timeout = 300
        return params

    def get_connection(self):
        self.lock.acquire()
        try:
            connection = self.queue.get(block=False)
        finally:
            self.lock.release()

        if not connection.is_open:
            return self._get_connection()
        return connection

    def get_connection_with_channel(self):
        connection = self.get_connection()
        return connection, connection.channel()

    def release(self, connection):
        self.queue.put_nowait(connection)


class PhiliaRabbitConnectionPoolAsync:

    def __init__(self, rabbit_url: str, max_size: int = 3):
        self.rabbit_url = rabbit_url
        self.max_size = max_size
        self.queue = AsyncQueue(maxsize=self.max_size)
        self.lock = AsyncLock()

    async def _get_connection(self):
        return await aio_pika.connect_robust(
            url=self.rabbit_url,
            heartbeat=30,
            timeout=300
        )

    async def _create_connections(self):
        for _ in range(self.max_size):
            # don't block the process if there is no any slot to put connection on
            await self.queue.put(
                self._get_connection()
            )

    async def get_connection(self):
        await self.lock.acquire()
        try:
            connection = await self.queue.get()
        finally:
            self.lock.release()

        if not connection.is_open:
            return self._get_connection()
        return connection

    async def get_connection_with_channel(self):
        connection = await self.get_connection()
        return connection, await connection.channel()

    async def release(self, connection):
        await self.queue.put(connection)
