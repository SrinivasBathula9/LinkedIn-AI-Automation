import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.db.models import Profile, ConnectionRequest

router = APIRouter(prefix="/profiles", tags=["profiles"])


class ProfileOut(BaseModel):
    id: uuid.UUID
    linkedin_url: str
    full_name: str | None
    title: str | None
    company: str | None
    region: str | None
    relevance_score: float | None
    classifier_confidence: float | None
    is_relevant: bool | None

    model_config = {"from_attributes": True}


@router.get("/queue", response_model=list[ProfileOut])
async def get_profile_queue(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Return pending profiles sorted by relevance score descending."""
    # Profiles not yet sent — no connection_request with sent status
    sent_profile_ids = select(ConnectionRequest.profile_id).where(
        ConnectionRequest.status.in_(["sent", "accepted", "skipped"])
    )
    result = await db.execute(
        select(Profile)
        .where(
            Profile.is_relevant == True,
            Profile.id.not_in(sent_profile_ids),
        )
        .order_by(Profile.relevance_score.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.post("/skip/{profile_id}", status_code=200)
async def skip_profile(profile_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Manually skip a profile — create a skipped connection request."""
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    cr = ConnectionRequest(profile_id=profile_id, status="skipped")
    db.add(cr)
    await db.commit()
    return {"status": "skipped", "profile_id": str(profile_id)}
