"""."""
import dataclasses as dc
import os

import yaml

from base_sync.base_module import (
    OMSPgConfig,
    Model,
)

from base_sync.models import RabbitFullConfig
from models import FileStorageConfig


@dc.dataclass
class ServiceConfig(Model):
    """."""

    rabbit: RabbitFullConfig = dc.field()
    pg: OMSPgConfig = dc.field()
    file_storage: FileStorageConfig = dc.field()
    tmp_dir: str = dc.field(default='/tmp')


config: ServiceConfig = ServiceConfig.load(
    yaml.safe_load(open(os.getenv('YAML_PATH', "/config.yaml"))) or {}
)
