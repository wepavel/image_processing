from base_sync.base_module import Model


class FuncService(Model):
    """."""

    function_type: str = None

    def process(self, src_path: str, dest_path: str, params: dict) -> None:
        raise NotImplementedError


class ProcessAbstractFactory:
    """."""

    _registry: dict[str, FuncService] = {}

    def add_registry(self, instance: FuncService) -> None:
        if not isinstance(instance, FuncService):
            raise TypeError(f"Ожидался экземпляр FuncService, получено: {type(instance)}")

        if not getattr(instance, "function_type", None):
            raise ValueError(f"У экземпляра {type(instance).__name__} должен быть задан атрибут function_type")

        self._registry[instance.function_type] = instance

    def get(self, kind: str) -> FuncService:
        instance = self._registry.get(kind)
        if not instance:
            raise ValueError(f"Неизвестный тип: {kind}")
        return instance
