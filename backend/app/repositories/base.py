from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List

T = TypeVar("T")

class IRepository(ABC, Generic[T]):
    @abstractmethod
    async def add(self, obj: T) -> T: ...
    @abstractmethod
    async def get_all(self) -> List[T]: ...

