from __future__ import annotations


class OrganRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, object] = {}

    def register(self, organ: str, factory: object) -> None:
        self._factories[organ] = factory

    def build(self, spec: dict[str, object]):
        organ = str(spec["organ"])
        factory = self._factories[organ]
        kwargs = dict(spec)
        kwargs.pop("organ")
        return factory(**kwargs)

    def build_many(self, specs: list[dict[str, object]]) -> list[object]:
        return [self.build(spec) for spec in specs]
