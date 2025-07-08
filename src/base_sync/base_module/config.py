import dataclasses as dc

from . import Model


@dc.dataclass
class PgConfig(Model):
    """."""

    host: str = dc.field()
    port: int = dc.field()
    user: str = dc.field()
    password: str = dc.field()
    database: str = dc.field()
    max_pool_connections: int = dc.field(default=100)
    debug: bool = dc.field(default=False)
    schema: str = dc.field(default='public')


@dc.dataclass
class OMSPgConfig(PgConfig):
    """."""

    host: str = dc.field()
    port: int = dc.field()
    user: str = dc.field()
    password: str = dc.field()
    database: str = dc.field()
    schema: str = dc.field(default='tasks')


@dc.dataclass
class OMSSessionConfig(Model):
    """."""

    user: str = dc.field(default='')
    project: str = dc.field(default='')
