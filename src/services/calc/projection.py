from osgeo import gdal

from .base import FuncService
from models.calc import ProjectionChangeParams


class ProjectionChangeService(FuncService):
    """."""

    function_type = "change_projection"

    def process(self, src_path: str, dest_path: str, params: dict) -> None:
        params = ProjectionChangeParams.load(params)

        src_ds = gdal.Open(src_path)
        if not src_ds:
            raise RuntimeError(f"Не удалось открыть: {src_path}")
        gdal.Warp(destNameOrDestDS=dest_path, srcDSOrSrcDSTab=src_ds, dstSRS=params.target_srs, format="GTiff")
