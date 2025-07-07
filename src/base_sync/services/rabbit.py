import json
import time
import typing as t
from contextlib import contextmanager
from copy import deepcopy

import pika
from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from pika.adapters.blocking_connection import BlockingChannel

# from ..base_module import ClassesLoggerAdapter, ModuleException
from ..base_module import ModuleException
from logging import getLogger
# from ..flask import FormatDumps
from ..models.rabbit import (
    RabbitFullConfig,
    RabbitConsumerConfig,
    RabbitPublisherConfig,
    MessageModel,
    JsonMessageModel
)


class RabbitService:
    """."""

    @property
    def _can_consume(self):
        return isinstance(self._config, RabbitConsumerConfig)

    @property
    def _can_publish(self):
        return isinstance(self._config, RabbitPublisherConfig)

    @property
    def config(self):
        return deepcopy(self._config)

    def __init__(
            self,
            config: t.Union[RabbitFullConfig, t.Union[
                RabbitConsumerConfig, RabbitPublisherConfig]]
    ):
        """."""
        self._config = config
        self._logger = getLogger(__name__)

    @contextmanager
    def _queue_connection(self) -> t.ContextManager[BlockingChannel]:
        connection = BlockingConnection(
            ConnectionParameters(
                host=self._config.host,
                port=self._config.port,
                credentials=PlainCredentials(
                    username=self._config.user,
                    password=self._config.password
                ),
                heartbeat=0,
            )
        )
        channel = connection.channel()
        channel.exchange_declare(
            exchange=self._config.exchange,
            exchange_type='direct',
            durable=True
        )
        channel.queue_declare(
            queue=self._config.queue_name,
            durable=True,
            arguments={'x-max-priority': 5}
        )
        channel.queue_bind(
            exchange=self._config.exchange,
            queue=self._config.queue_name,
            routing_key=self._config.routing_key
        )
        yield channel
        channel.close()
        connection.close()

    def declare_dlx(
            self,
            routing_key: str,
            dlx_queue_name: str,
            message_ttl: int,
            dlx_exchange: str = '',
            max_priority: int = 5,
    ):
        with self._queue_connection() as channel:
            channel.queue_declare(
                queue=dlx_queue_name,
                passive=False,
                durable=True,
                arguments={
                    'x-message-ttl': message_ttl * 1000,
                    'x-dead-letter-exchange': dlx_exchange,
                    'x-dead-letter-routing-key': routing_key,
                    'x-max-priority': max_priority
                }
            )

    def _make_properties(
            self,
            properties: pika.BasicProperties
    ) -> pika.BasicProperties:
        properties = properties or pika.BasicProperties()
        properties.delivery_mode = pika.spec.PERSISTENT_DELIVERY_MODE
        if not properties.reply_to and self._config.reply_to:
            properties.reply_to = self._config.reply_to

        return properties

    def publish(
            self,
            message: MessageModel,
            properties: pika.BasicProperties = None,
            publish_to: str = None,
            exchange: str = None
    ) -> bool:
        if not self._can_publish:
            raise ModuleException('Конфиг не соответствует конфигу отправки')

        publish_to = publish_to or self._config.routing_key
        exchange = exchange or self._config.exchange
        properties = self._make_properties(properties)

        try:
            with self._queue_connection() as channel:
                channel.basic_publish(
                    exchange=exchange,
                    routing_key=publish_to,
                    body=json.dumps(message.dump()).encode(),
                    properties=properties
                )
                self._logger.info(
                    'Отправлено сообщение',
                    extra={'queue': publish_to}
                )
                return True
        except Exception as e:
            self._logger.error(
                'Ошибка отправки сообщения',
                extra={
                    'msg_payload': message, 'exchange': exchange,
                    'publish_to': publish_to,
                    'properties': properties, 'e': e
                },
                exc_info=True
            )
            return False

    def publish_many(
            self,
            messages: t.List[MessageModel],
            properties: pika.BasicProperties = None,
            publish_to: str = None,
            exchange: str = None
    ):
        if not self._can_publish:
            raise ModuleException('Конфиг не соответствует конфигу отправки')

        publish_to = publish_to or self._config.routing_key
        exchange = exchange or self._config.exchange
        properties = self._make_properties(properties)

        try:
            with self._queue_connection() as channel:
                for message in messages:
                    self._logger.info(
                        'Отправлено сообщение',
                        extra={'queue': publish_to}
                    )
                    channel.basic_publish(
                        exchange=exchange,
                        routing_key=publish_to,
                        body=json.dumps(message).encode(),
                        properties=properties
                    )
                return True
        except Exception as e:
            self._logger.error(
                'Ошибка отправки сообщений',
                extra={
                    'messages': messages, 'exchange': exchange,
                    'publish_to': publish_to,
                    'properties': properties, 'e': e
                },
                exc_info=True
            )
            return False

    def _receiver_proxy(self, receiver, message_type: t.Type[MessageModel]):
        def _handle_message(
                ch: BlockingChannel,
                method: pika.spec.Basic.Deliver,
                properties: pika.BasicProperties,
                body: bytes
        ):
            nonlocal self
            try:
                message = message_type.load(json.loads(body))
            except Exception as e:
                self._logger.warning(
                    'Сообщение не подходит под формат',
                    extra={'body': body, 'e': e}
                )
                ch.basic_ack(method.delivery_tag)
                return

            try:
                message_handled = receiver(
                    message=message, channel=ch, method=method,
                    properties=properties
                )
                not message_handled and ch.basic_ack(method.delivery_tag)
            except Exception as e:
                self._logger.error(
                    'Ошибка обработки сообщения', exc_info=True,
                    extra={'body': body, 'e': e}
                )
                ch.basic_nack(method.delivery_tag)

        return _handle_message

    def run_consume(
            self, receiver,
            message_type: t.Type[MessageModel] = JsonMessageModel
    ):
        if not self._can_consume:
            raise ModuleException(
                'Конфиг не соответствует конфигу прослушивания'
            )

        while True:
            try:
                self._logger.info(
                    'Запуск прослушивания очереди',
                    extra={'queue': self._config.queue_name}
                )
                with self._queue_connection() as channel:
                    channel.basic_qos(prefetch_count=1)
                    channel.queue_declare(
                        queue=self._config.queue_name,
                        durable=True,
                        arguments={'x-max-priority': self._config.max_priority}
                    )
                    channel.basic_consume(
                        queue=self._config.queue_name,
                        auto_ack=False,
                        exclusive=False,
                        on_message_callback=self._receiver_proxy(
                            receiver,
                            message_type
                        )
                    )
                    channel.start_consuming()
            except Exception as e:
                self._logger.error(
                    'Ошибка подключения или прослушивания очереди',
                    extra={'queue': self._config.queue_name, 'e': e},
                    exc_info=True
                )

            time.sleep(self._config.error_timeout)
