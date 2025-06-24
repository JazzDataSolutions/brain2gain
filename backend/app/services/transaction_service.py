# backend/app/services/transaction_service.py

from app.models.transaction import Transaction
from app.repositories.base import IRepository
from app.schemas.transaction import TransactionCreate, TransactionRead


class TransactionService:
    def __init__(self, repo: IRepository[Transaction]):
        self.repo = repo

    async def create(self, data: TransactionCreate) -> TransactionRead:
        tx = Transaction(**data.dict())
        saved = await self.repo.add(tx)
        return TransactionRead.from_orm(saved)

    async def list(self) -> list[TransactionRead]:
        items = await self.repo.get_all()
        return [TransactionRead.model_validate(i) for i in items]
