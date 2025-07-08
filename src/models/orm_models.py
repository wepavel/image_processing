"""."""

import typing as t
import dataclasses as dc
import typing
from datetime import datetime

import sqlalchemy as sa

from base_sync.base_module import ValuedEnum, BaseOrmMappedModel, Model

SCHEMA_NAME = 'tasks'


class TaskStatus(ValuedEnum):
    """."""

    NEW = 'new'
    PROCESSING = 'processing'
    ERROR = 'error'
    DONE = 'done'


@dc.dataclass
class CreationModel(Model):
    """."""

    image_id: str = dc.field()
    function_type: str = dc.field()
    function_args: t.Optional[dict] = dc.field(default_factory=dict)


@dc.dataclass
class ProcessingTask(BaseOrmMappedModel):
    """."""

    __tablename__ = 'image_processing_tasks'
    __table_args__ = {'schema': SCHEMA_NAME}

    task_id: typing.Optional[int] = dc.field(
        default=None,
        metadata={'sa': sa.Column(sa.Integer, primary_key=True)}
    )
    status: TaskStatus = dc.field(
        default=TaskStatus.NEW,
        metadata={
            'sa': sa.Column(
                sa.Enum(TaskStatus, name='image_processing_status',
                        schema=SCHEMA_NAME)
            )
        }
    )
    image_id: str = dc.field(
        default=None,
        metadata={'sa': sa.Column(sa.String)}
    )
    new_image_id: typing.Optional[str] = dc.field(
        default=None,
        metadata={'sa': sa.Column(sa.String)}
    )
    function_type: str = dc.field(
        default=None,
        metadata={'sa': sa.Column(sa.String)}
    )
    function_args: typing.Optional[dict] = dc.field(
        default=None,
        metadata={'sa': sa.Column(sa.JSON)}
    )
    created_at: typing.Optional[datetime] = dc.field(
        default_factory=datetime.now,
        metadata={'sa': sa.Column(sa.DateTime)}
    )
    updated_at: typing.Optional[datetime] = dc.field(
        default=None,
        metadata={'sa': sa.Column(sa.DateTime)}
    )
    duration: typing.Optional[float] = dc.field(
        default=None,
        metadata={'sa': sa.Column(sa.Float)}
    )


BaseOrmMappedModel.REGISTRY.mapped(ProcessingTask)
