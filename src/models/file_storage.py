import dataclasses as dc

from base_sync.base_module import Model


@dc.dataclass
class FileStorageConfig(Model):
    """."""

    host: str = dc.field(default='localhost')
    port: int = dc.field(default=80)
    schema: str = dc.field(default='http')
    path_prefix: str = dc.field(default='/')
    chunk_size: int = dc.field(default=1024 * 1024 * 5)  # 5MB

    @property
    def base_url(self) -> str:
        return f'{self.schema}://{self.host}:{self.port}/{self.path_prefix}'
