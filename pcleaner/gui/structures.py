from typing import Generic, TypeVar, Optional, Protocol

from PIL import Image


T = TypeVar("T")


class Shared(Generic[T]):
    def __init__(self, initial_value: Optional[T] = None) -> None:
        self._container = {"data": initial_value}

    def get(self) -> Optional[T]:
        return self._container["data"]

    def set(self, value: T) -> None:
        self._container["data"] = value

    def is_none(self) -> bool:
        return self._container["data"] is None


class OCRModel(Protocol):
    def __call__(self, image: Image) -> str:
        ...
