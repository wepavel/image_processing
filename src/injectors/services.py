from base_sync.services import (
    RabbitService
)
from services.file_storage import FileStorageService
from services.calc import (
    ProcessAbstractFactory,
    ResolutionChangeService,
    ProjectionChangeService
)
from config import config
from services import (
    TasksService,
    TasksWorker,
)
from . import connections


def process_factory() -> ProcessAbstractFactory:
    process_factory = ProcessAbstractFactory()
    process_factory.add_registry(ResolutionChangeService())
    process_factory.add_registry(ProjectionChangeService())
    return process_factory


def rabbit() -> RabbitService:
    """."""
    return RabbitService(config.rabbit)


def tasks_service() -> TasksService:
    """."""
    return TasksService(
        rabbit=rabbit(),
        pg_connection=connections.pg.acquire_session(),
    )


def file_storage() -> FileStorageService:
    """."""
    return FileStorageService(
        base_url=config.file_storage.base_url,
        chunk_size=config.file_storage.chunk_size,
    )


def tasks_mule() -> TasksWorker:
    """."""
    return TasksWorker(
        rabbit=rabbit(),
        pg_connection=connections.pg.acquire_session(),
        temp_dir=config.tmp_dir,
        file_storage=file_storage(),
        image_process_factory=process_factory()
    )
