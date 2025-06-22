"""
Base Repository Pattern Implementation
Provides abstract base classes following SOLID principles
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

# Type variables for generic repository
ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseRepository(ABC, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Abstract base repository implementing common CRUD operations.
    
    This class follows the Repository Pattern and SOLID principles:
    - Single Responsibility: Only handles data access
    - Open/Closed: Extensible through inheritance, closed for modification
    - Liskov Substitution: All implementations must be substitutable
    - Interface Segregation: Minimal interface for basic operations
    - Dependency Inversion: Depends on abstractions (AsyncSession)
    """

    def __init__(self, session: AsyncSession, model: type[ModelType]):
        self.session = session
        self.model = model

    @abstractmethod
    async def get_by_id(self, id: Any) -> ModelType | None:
        """Get entity by ID"""
        pass

    @abstractmethod
    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: dict[str, Any] | None = None
    ) -> list[ModelType]:
        """Get multiple entities with pagination and filtering"""
        pass

    @abstractmethod
    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create new entity"""
        pass

    @abstractmethod
    async def update(
        self,
        db_obj: ModelType,
        obj_in: UpdateSchemaType
    ) -> ModelType:
        """Update existing entity"""
        pass

    @abstractmethod
    async def delete(self, id: Any) -> bool:
        """Delete entity by ID"""
        pass

    @abstractmethod
    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count entities with optional filtering"""
        pass

    @abstractmethod
    async def exists(self, id: Any) -> bool:
        """Check if entity exists"""
        pass


class SearchableRepository(BaseRepository[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Repository interface for entities that support search functionality.
    
    Extends base repository with search capabilities following
    Interface Segregation Principle - only entities that need search
    should implement this interface.
    """

    @abstractmethod
    async def search(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100,
        filters: dict[str, Any] | None = None
    ) -> list[ModelType]:
        """Search entities by text query"""
        pass

    @abstractmethod
    async def search_count(
        self,
        query: str,
        filters: dict[str, Any] | None = None
    ) -> int:
        """Count search results"""
        pass


# Strategy Pattern for Business Rules
class BusinessRuleStrategy(ABC):
    """
    Abstract strategy for business rules validation.
    
    Implements Strategy Pattern following Open/Closed Principle:
    - Allows different validation strategies without modifying core logic
    """

    @abstractmethod
    async def validate(self, entity: Any, context: dict[str, Any] | None = None) -> bool:
        """Validate business rule"""
        pass

    @abstractmethod
    def get_error_message(self) -> str:
        """Get validation error message"""
        pass


class BusinessRuleEngine:
    """
    Engine for applying business rules using Strategy Pattern.
    """

    def __init__(self):
        self.rules: list[BusinessRuleStrategy] = []

    def add_rule(self, rule: BusinessRuleStrategy) -> None:
        """Add business rule"""
        self.rules.append(rule)

    async def validate_all(self, entity: Any, context: dict[str, Any] | None = None) -> None:
        """Validate all business rules"""
        for rule in self.rules:
            if not await rule.validate(entity, context):
                raise ValueError(rule.get_error_message())

    def clear_rules(self) -> None:
        """Clear all rules"""
        self.rules.clear()


# Legacy compatibility
T = TypeVar("T")

class IRepository(ABC, Generic[T]):
    @abstractmethod
    async def add(self, obj: T) -> T: ...
    @abstractmethod
    async def get_all(self) -> list[T]: ...
