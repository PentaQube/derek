from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, select, exists
from src.models.session import SessionQuestion
from src.core.exceptions import NotFoundError, AlreadyExistsError


def get_session_question(
    *,
    session: Session,
    id: Optional[int] = None,
) -> SessionQuestion | None:
    if id is None:
        raise ValueError("id must be provided")

    conditions = [SessionQuestion.id == id]
    return session.scalar(select(SessionQuestion).where(or_(*conditions)))


def get_session_question_or_raise(*, session: Session, id: int) -> SessionQuestion:
    session_question = get_session_question(session=session, id=id)
    if session_question is None:
        raise NotFoundError(f"Session question with ID {id} not found.")
    return session_question


def is_question_used_in_session(*, session: Session, id: int) -> bool:
    return session.query(exists().where(SessionQuestion.question_id == id)).scalar()


def ensure_question_not_used_in_session(*, session: Session, id: int) -> None:
    if is_question_used_in_session(session=session, id=id):
        raise AlreadyExistsError(
            "This question cannot be deleted as it is currently used in a session."
        )
