import dataclasses as dc

from base_sync.base_module import Model


@dc.dataclass
class ProjectionChangeParams(Model):
    """."""

    target_srs: str = dc.field()


@dc.dataclass
class ResolutionChangeParams(Model):
    """."""

    x_res: float = dc.field()
    y_res: float = dc.field()
