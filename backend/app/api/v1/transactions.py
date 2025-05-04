# backend/app/api/v1/transactions.py
from fastapi import APIRouter, Depends, status
from typing import List
from app.schemas.transaction import TransactionCreate, TransactionRead
from app.services.transaction_service import TransactionService
from app.api.dependencies import get_transaction_service

router = APIRouter(prefix="/transactions")

@router.post("/", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
async def create_tx(
    payload: TransactionCreate,
    svc: TransactionService = Depends(get_transaction_service),
):
    return await svc.create(payload)

@router.get("/", response_model=List[TransactionRead])
async def list_tx(svc: TransactionService = Depends(get_transaction_service)):
    return await svc.list()

