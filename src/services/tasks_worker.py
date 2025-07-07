import os.path
import shutil
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Session as PGSession

from base_sync.base_module import BaseMule, sa_operator
from base_sync.base_module import ModuleException
from base_sync.models import TaskIdentMessageModel
from base_sync.services import RabbitService
from base_sync.services import (
    ImageRequestsService,
    ProcessAbstractFabric
)
from models import (
    TaskStatus,
    ProcessingTask,
)
from logging import getLogger


class TasksWorker(BaseMule):
    """Сервис обработки задач"""

    def __init__(
            self,
            rabbit: RabbitService,
            pg_connection: PGSession,
            temp_dir: str,
            image_requests: ImageRequestsService,
            image_process_fabric: ProcessAbstractFabric
    ):
        """Инициализация сервиса"""
        self._rabbit = rabbit
        self._pg = pg_connection
        self._temp_dir = temp_dir
        self._logger = getLogger(__name__)
        self._image_requests = image_requests
        self._image_process_fabric = image_process_fabric

    def _work_dir(self, task_id: int) -> str:
        """Создание временной папки"""
        temp_dir = os.path.join(self._temp_dir, str(task_id))
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

    def _handle(self, task: ProcessingTask):
        """Обработка задачи"""
        self._logger.info('Обработка задачи', extra={'task': task.task_id})
        task = ProcessingTask.load(task.dump())

        temp_dir = self._work_dir(task.task_id)
        try:
            path = self._image_requests.save_image(task.image_id, temp_dir)

            img_processor = self._image_process_fabric.create(task.function_type)

            args = task.function_args.copy()
            args['input_path'] = path
            img_name = path.split('/')[-1]
            new_img_name = img_name.split('.')[0] + '_processed.' + img_name.split('.')[1]
            new_img_path = os.path.join(temp_dir, new_img_name)
            args['output_path'] = new_img_path

            img_processor.process(**args)

            new_img_id = self._image_requests.upload_image(new_img_path)

            task.new_image_id = new_img_id

            self._update_status(task, TaskStatus.DONE)
        except Exception as e:
            self._logger.critical(
                'Ошибка обработки задачи',
                exc_info=True,
                extra={'e': e, 'task': task.task_id}
            )
            self._update_status(task, TaskStatus.ERROR)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            self._logger.info(
                'Обработка задачи завершена',
                extra={'task': task.task_id}
            )

    def _update_status(self, task: ProcessingTask, status: TaskStatus):
        """Обновление статуса задачи"""
        task.status = status
        updated = datetime.now()
        task.duration = (updated - task.updated_at).total_seconds()
        task.updated_at = updated
        self._logger.info(
            'Изменение статуса задачи',
            extra={'task_id': task.task_id, 'status': task.status}
        )
        with self._pg.begin():
            if self._pg.get(ProcessingTask, task.task_id,
                            with_for_update=True):
                self._pg.merge(task)
                return task.reload()

    def _get_task(self, task_id: int) -> ProcessingTask | None:
        """Получение задачи из БД"""
        with self._pg.begin():
            task: ProcessingTask = self._pg.execute(
                sa.select(ProcessingTask).filter(
                    sa.and_(
                        sa_operator.eq(ProcessingTask.task_id, task_id),
                        sa_operator.in_(
                            ProcessingTask.status,
                            [
                                TaskStatus.NEW,
                                # В случае ручного восстановления работы
                                TaskStatus.PROCESSING
                            ]
                        )
                    )
                ).limit(1)
            ).scalar()
            if not task:
                return

            task.status = TaskStatus.PROCESSING
            task.updated_at = datetime.now()
            self._pg.merge(task)
            return task.reload()

    def _handle_message(self, message: TaskIdentMessageModel, **_):
        """Обработка сообщения от брокера"""
        task_id = message.payload.task_id
        task = self._get_task(task_id)
        if not task:
            self._logger.warning('Задача не найдена', extra={'task_id': task_id})
            return

        try:
            self._handle(task)
        except Exception as e:
            exc_data = {'e': e}
            if isinstance(e, ModuleException):
                exc_data.update(e.data)
            self._logger.critical(
                'Ошибка верхнего уровня обработчика задачи',
                extra=exc_data, exc_info=True
            )
            self._update_status(task, TaskStatus.ERROR)

    def run(self):
        """Запуск прослушивания очереди брокера сообщений"""
        self._rabbit.run_consume(self._handle_message, TaskIdentMessageModel)
