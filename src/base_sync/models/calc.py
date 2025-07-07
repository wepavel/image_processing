from osgeo import gdal

from base_sync.base_module import Model


class FuncService(Model):
    """."""

    function_type: str = None

    def process(self, **kwargs) -> None:
        raise NotImplementedError


class ResolutionChangeService(FuncService):
    """."""

    function_type = "change_resolution"

    def process(self, **kwargs) -> None:
        input_path, output_path, srs = kwargs["input_path"], kwargs["output_path"], kwargs["target_srs"]
        x_res, y_res = kwargs["x_res"], kwargs["y_res"]
        src_ds = gdal.Open(input_path)
        if not src_ds:
            raise RuntimeError(f"Не удалось открыть: {input_path}")

        gdal.Warp(
            destNameOrDestDS=output_path,
            srcDSOrSrcDSTab=src_ds,
            width=x_res,
            height=y_res,
            format="GTiff"
        )


class ProjectionChangeService(FuncService):
    function_type = "change_projection"

    def process(self, **kwargs) -> None:
        input_path, output_path, srs = kwargs["input_path"], kwargs["output_path"], kwargs["target_srs"]
        src_ds = gdal.Open(input_path)
        if not src_ds:
            raise RuntimeError(f"Не удалось открыть: {input_path}")
        gdal.Warp(destNameOrDestDS=output_path, srcDSOrSrcDSTab=src_ds, dstSRS=srs, format="GTiff")


class ProcessAbstractFabric:
    _registry: dict[str, type[FuncService]] = {}

    @classmethod
    def populate_registry(cls):
        for subclass in FuncService.__subclasses__():
            type_key = getattr(subclass, "function_type", None)
            if type_key:
                cls._registry[type_key] = subclass

    @classmethod
    def create(cls, kind: str, **kwargs) -> FuncService:
        if not cls._registry:
            cls.populate_registry()
        klass = cls._registry.get(kind)
        if not klass:
            raise ValueError(f"Unknown type: {kind}")
        return klass(**kwargs)
