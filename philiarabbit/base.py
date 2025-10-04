from logging import Logger
from typing import Any
import socket
import pika
from pika.exceptions import (
    AMQPConnectionError,
    ProbableAuthenticationError,
    ProbableAccessDeniedError,
    StreamLostError,
)


class PhiliaRabbitBase:
    """ 
        In this class we implement some usefull methods that 
        uses in child classes.

    """
    
    pool: Any = None
    logger: Logger | None = None
    rabbit_url: str | None = None
    
    connection = None 
    channel = None
    
    def _log(self, *args, **kwargs):
        if self.logger is not None and isinstance(self.logger, Logger):
            self.logger.warning(*args, **kwargs)
            
    def _get_default_parameters(self) -> pika.URLParameters:
        if self.rabbit_url is None:
            raise ValueError("invalid rabbit_url")
        params = pika.URLParameters(self.rabbit_url)
        params.heartbeat = 60
        params.blocked_connection_timeout = 200
        params.socket_timeout = 200
        return params
    
    def _connect(self, make_channel: bool = False, parameters: pika.URLParameters | None = None):
        if self.rabbit_url is None:
            raise ValueError("invalid rabbit_url")
        
        self.connection = pika.BlockingConnection(
            parameters or self._get_default_parameters()
        )
        if make_channel:
            self.channel = self.connection.channel() 
        return self.connection
        
    def _disconnect(self):
        if self.channel and self.channel.is_open:
            self._log("[+] Channel closed")
            self.channel.close()

        if self.pool is not None:
            self.pool.release(self.connection)
            self._log("[+] Connection released in pool")
            return

        if self.connection and self.connection.is_open:
            self._log("[+] Connection Closed")
            self.connection.close()
    
    def _check_connection(self, connection: pika.BlockingConnection | None, make_new_connection: bool = True) -> pika.BlockingConnection | None:
        if connection is None:
            return self._connect(make_channel=False)
        
        try:
            if not connection.is_open:
                return self._connect(make_channel=False)
            connection.process_data_events(0)
            self._log("[+] Connection is OK")
            return connection
        except (
                AMQPConnectionError,
                ProbableAuthenticationError,
                ProbableAccessDeniedError,
                socket.gaierror,
                ConnectionRefusedError,
                StreamLostError,
                Exception,
        ):
            self._log(
                msg="[-] reconnecting in _check_connection()...",
                extra=locals()
            )
            if make_new_connection:
                return self._connect(make_channel=False)