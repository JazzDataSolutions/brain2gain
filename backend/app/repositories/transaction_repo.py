# backend/app/repositories/transaction_repo.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.repositories.base import IRepository


class TransactionRepository(IRepository[Transaction]):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, obj: Transaction) -> Transaction:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def get_all(self) -> list[Transaction]:
        res = await self.session.execute(select(Transaction))
        return res.scalars().all()
