from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from backend.db.session import get_db
from backend.db.models import AutomationLog

router = APIRouter(prefix="/logs", tags=["logs"])


class LogOut(BaseModel):
    id: uuid.UUID
    event_type: str | None
    message: str | None
    log_metadata: dict | None
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


@router.get("/", response_model=list[LogOut])
async def get_logs(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AutomationLog).order_by(AutomationLog.created_at.desc()).limit(limit)
    )
    return result.scalars().all()
