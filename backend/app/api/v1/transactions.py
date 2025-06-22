# backend/app/api/v1/transactions.py

from fastapi import APIRouter, Depends, Request, status

from app.api.dependencies import get_transaction_service
from app.middlewares.advanced_rate_limiting import apply_endpoint_limits
from app.schemas.transaction import TransactionCreate, TransactionRead
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions")

@router.post("/", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
@apply_endpoint_limits("orders")
async def create_tx(
    request: Request,
    payload: TransactionCreate,
    svc: TransactionService = Depends(get_transaction_service),
):
    return await svc.create(payload)

@router.get("/", response_model=list[TransactionRead])
async def list_tx(svc: TransactionService = Depends(get_transaction_service)):
    return await svc.list()

