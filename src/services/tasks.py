import pika
import sqlalchemy as sa
from sqlalchemy.orm import Session as PGSession

from base_sync.base_module import (
    sa_operator,
    ModuleException,
)
from base_sync.models import TaskIdentMessageModel
from base_sync.services import RabbitService
from models import ProcessingTask

from logging import getLogger
from datetime import datetime
from models import CreationModel


class TasksService:
    """."""

    def __init__(
            self,
            rabbit: RabbitService,
            pg_connection: PGSession,
    ):
        """."""
        self._rabbit = rabbit
        self._pg = pg_connection
        self._logger = getLogger(__name__)

    def create_task(self, data) -> ProcessingTask:
        """."""

        data = CreationModel.load(data)

        task = ProcessingTask(
            image_id=data.image_id,
            function_type=data.function_type,
            function_args=data.function_args,
            updated_at=datetime.now(),
        )

        with self._pg.begin():
            self._pg.add(task)

        task.reload()
        message = TaskIdentMessageModel.lazy_load(
            TaskIdentMessageModel.T(task.task_id)
        )

        published = self._rabbit.publish(
            message, properties=pika.BasicProperties()
        )
        if published:
            return task

        with self._pg.begin():
            self._pg.delete(task)

        raise ModuleException(
            'Не удалось отправить сообщения об обработке задач'
        )

    def get_all(self) -> list[ProcessingTask]:
        """."""
        with self._pg.begin():
            q = self._pg.query(ProcessingTask)

            q = q.order_by(sa.desc(ProcessingTask.created_at))
            return q.all()

    def get(self, task_id: int) -> ProcessingTask:
        with self._pg.begin():
            task: ProcessingTask = self._pg.query(
                ProcessingTask
            ).filter(
                sa_operator.eq(ProcessingTask.task_id, task_id)
            ).one_or_none()
            if task:
                return task

        raise ModuleException('Задача не найдена', code=404)
