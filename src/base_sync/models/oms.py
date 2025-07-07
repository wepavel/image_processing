import dataclasses as dc
from datetime import datetime

from ..base_module import Model, ValuedEnum, OMSPgConfig

OMSPostgresConfig = OMSPgConfig


class OMSFileTaskStatus(ValuedEnum):
    """."""

    NEW = 'new'
    PROCESSING = 'processing'
    DONE = 'done'
    ERROR = 'error'


@dc.dataclass
class OMSFileTask(Model):
    """."""

    src_file_id: int = dc.field()
    id: int = dc.field(default=None)
    task_status: OMSFileTaskStatus = dc.field(default=OMSFileTaskStatus.NEW)
    file_id: str = dc.field(default=None)
    data: dict = dc.field(default_factory=dict)
    created_at: datetime = dc.field(default_factory=datetime.now)
    updated_at: datetime = dc.field(default_factory=datetime.now)
    duration: int = dc.field(default=0)
