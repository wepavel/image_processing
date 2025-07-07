from base_sync.services import (
    RabbitService
)
from base_sync.services import (
    ImageRequestsService,
    ProcessAbstractFabric
)
from config import config
from services import (
    TasksService,
    TasksWorker,
)
from . import connections


def rabbit() -> RabbitService:
    """."""
    return RabbitService(config.rabbit)


def tasks_service() -> TasksService:
    """."""
    return TasksService(
        rabbit=rabbit(),
        pg_connection=connections.pg.acquire_session(),
    )


def process_fabric() -> ProcessAbstractFabric:
    """."""
    return ProcessAbstractFabric()


def image_requests() -> ImageRequestsService:
    """."""
    return ImageRequestsService(
        config=config.image_requests
    )


def tasks_mule() -> TasksWorker:
    """."""
    return TasksWorker(
        rabbit=rabbit(),
        pg_connection=connections.pg.acquire_session(),
        temp_dir=config.tmp_dir,
        image_requests=image_requests(),
        image_process_fabric=process_fabric()
    )
