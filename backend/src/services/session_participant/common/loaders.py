from sqlalchemy import select
from sqlalchemy.orm import Session
from src.core.exceptions import NotFoundError
from src.models.session import SessionParticipant


def get_participant(*, session: Session, id: int) -> SessionParticipant | None:
    stmt = select(SessionParticipant).where(SessionParticipant.id == id)
    participant = session.scalar(stmt)
    return participant


def get_participant_or_raise(*, session: Session, id: int) -> SessionParticipant:
    participant = get_participant(session=session, id=id)

    if not participant:
        raise NotFoundError(f"Session participant with ID {id} not found.")

    return participant


def get_participant_by_session_user(
    *, session: Session, session_id: int, user_id: int
) -> SessionParticipant | None:
    stmt = select(SessionParticipant).where(
        SessionParticipant.session_id == session_id,
        SessionParticipant.user_id == user_id,
    )
    return session.scalar(stmt)
