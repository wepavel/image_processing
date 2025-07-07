import dataclasses as dc

from base_sync.base_module import Model


@dc.dataclass
class ImageRequestsConfig(Model):
    """."""

    host: str = dc.field(default='localhost')
    port: int = dc.field(default=80)
    schema: str = dc.field(default='http')
    path_prefix: str = dc.field(default='/')
    chunk_size: int = dc.field(default=1024 * 1024 * 5)  # 5MB
