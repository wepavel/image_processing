import os.path
import shutil
import tempfile
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Session as PGSession

from base_sync.base_module import BaseMule, sa_operator
from base_sync.base_module import ModuleException
from base_sync.models import TaskIdentMessageModel
from base_sync.services import RabbitService
from services.file_storage import FileStorageService
from services.calc import ProcessAbstractFactory
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
            file_storage: FileStorageService,
            image_process_factory: ProcessAbstractFactory
    ):
        """Инициализация сервиса"""
        self._rabbit = rabbit
        self._pg = pg_connection
        self._temp_dir = temp_dir
        self._logger = getLogger(__name__)
        self._file_storage = file_storage
        self._image_process_factory = image_process_factory

    def _handle(self, task: ProcessingTask):
        """Обработка задачи"""
        self._logger.info('Обработка задачи', extra={'task': task.task_id})
        task.reload()

        try:
            with tempfile.TemporaryDirectory(prefix=str(task.task_id)) as temp_dir:
                path = self._file_storage.save_image(task.image_id, temp_dir)

                img_processor = self._image_process_factory.get(task.function_type)

                img_name = os.path.basename(path)
                name, ext = os.path.splitext(img_name)
                new_img_name = f"{name}_processed{ext}"
                new_img_path = os.path.join(temp_dir, new_img_name)

                img_processor.process(src_path=path, dest_path=new_img_path, params=task.function_args)

                new_img_id = self._file_storage.upload_image(new_img_path)

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
                return None

            return task.reload()

    def _handle_message(self, message: TaskIdentMessageModel, **_):
        """Обработка сообщения от брокера"""
        task_id = message.payload.task_id

        if not (task := self._get_task(task_id)):
            self._logger.warning('Задача не найдена', extra={'task_id': task_id})
            return

        self._update_status(task, TaskStatus.PROCESSING)

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
