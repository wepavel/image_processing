from base_sync.injectors import PgConnectionInj
from config import config
from models import *  # noqa

pg = PgConnectionInj(
    conf=config.pg,
)
