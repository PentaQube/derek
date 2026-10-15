from sqlalchemy import select
from typing import Optional
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_session
from src.models.community import Community


def validate_community_id(
    community_id: Optional[int] = None, session: Session = Depends(get_session)
):
    message_404 = f"Community with ID {community_id} not found."

    if community_id:
        status_data = session.scalar(
            select(Community).where(Community.id == community_id)
        )
        if not status_data:
            raise HTTPException(status_code=404, detail=message_404)
    return community_id
