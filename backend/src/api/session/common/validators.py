from sqlalchemy import select
from typing import Optional
from fastapi import Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from src.core.database import get_session
from src.models.session import Session as SessionModel, SessionStatus


def validate_session_id(
    session_id: Optional[int] = None, session: Session = Depends(get_session)
):
    message_404 = f"Session with ID {session_id} not found."

    if session_id:
        session_data = session.scalar(
            select(SessionModel).where(SessionModel.id == session_id)
        )
        if not session_data:
            raise HTTPException(status_code=404, detail=message_404)
    return session_id


def validate_session_status_id(
    session_status_id: Optional[int] = None, session: Session = Depends(get_session)
):
    message_404 = f"Session status with ID {session_status_id} not found."

    if session_status_id:
        status_data = session.scalar(
            select(SessionStatus).where(SessionStatus.id == session_status_id)
        )
        if not status_data:
            raise HTTPException(status_code=404, detail=message_404)
    return session_status_id
