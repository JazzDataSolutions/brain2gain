# backend/app/services/transaction_service.py
from typing import List
from app.models.transaction import Transaction
from app.repositories.base import IRepository
from app.schemas.transaction import TransactionCreate, TransactionRead

class TransactionService:
    def __init__(self, repo: IRepository[Transaction]):
        self.repo = repo

    async def create(self, data: TransactionCreate) -> TransactionRead:
        tx = Transaction(**data.dict())
        saved = await self.repo.add(tx)
        return TransactionRead.from_orm(saved)1

    async def list(self) -> List[TransactionRead]:
        items = await self.repo.get_all()
        return [TransactionRead.model_validate(i) for i in items]

