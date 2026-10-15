from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, select
from src.models.session import SessionStatus, Session as SessionModel
from src.core.exceptions import NotFoundError


def get_session_status(
    *, session: Session, id: Optional[int] = None, code: Optional[str] = None
) -> SessionStatus:
    if id is None and code is None:
        raise ValueError("Either id or code must be provided")

    conditions = []
    if id is not None:
        conditions.append(SessionStatus.id == id)
    if code is not None:
        conditions.append(SessionStatus.code == code)

    session_status = session.scalar(select(SessionStatus).where(or_(*conditions)))

    return session_status


def get_session_status_or_raise(
    *, session: Session, id: Optional[int] = None, code: Optional[str] = None
) -> SessionStatus:
    session_status = get_session_status(session=session, id=id, code=code)

    if session_status is None:
        identifier = id if id is not None else code
        raise NotFoundError(
            f"Session status with identifier {identifier} not found."
        )

    return session_status


def get_session(
    *,
    session: Session,
    id: Optional[int] = None,
    name: Optional[str] = None,
) -> SessionModel | None:
    if id is None and name is None:
        raise ValueError("Either id or name must be provided")

    conditions = []
    if id is not None:
        conditions.append(SessionModel.id == id)
    if name is not None:
        conditions.append(SessionModel.name == name)

    return session.scalar(select(SessionModel).where(or_(*conditions)))


def get_session_or_raise(*, session: Session, id: int) -> SessionModel:
    session_data = get_session(session=session, id=id)

    if session_data is None:
        raise NotFoundError(f"Session with identifier {id} not found.")

    return session_data
