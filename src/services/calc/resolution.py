from osgeo import gdal

from .base import FuncService
from models.calc import ResolutionChangeParams


class ResolutionChangeService(FuncService):
    """."""

    function_type = "change_resolution"

    def process(self, src_path: str, dest_path: str, params: dict) -> None:
        params = ResolutionChangeParams.load(params)

        src_ds = gdal.Open(src_path)
        if not src_ds:
            raise RuntimeError(f"Не удалось открыть: {src_path}")

        gdal.Warp(
            destNameOrDestDS=dest_path,
            srcDSOrSrcDSTab=src_ds,
            xRes=params.x_res,
            yRes=params.y_res,
            format="GTiff"
        )
