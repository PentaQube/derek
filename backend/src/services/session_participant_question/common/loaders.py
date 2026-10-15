from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.exceptions import NotFoundError
from src.models.session import AnswerStatus, SessionParticipant, SessionQuestion


def get_answer_status_or_raise(*, session: Session, code: str) -> AnswerStatus:
    obj = session.scalar(select(AnswerStatus).where(AnswerStatus.code == code))
    if obj is None:
        raise NotFoundError(f"Answer status not found: code {code}.")
    return obj


def get_participant_by_session_user_or_raise(
    *, session: Session, session_id: int, user_id: int
) -> SessionParticipant:
    obj = session.scalar(
        select(SessionParticipant).where(
            SessionParticipant.session_id == session_id,
            SessionParticipant.user_id == user_id,
        )
    )
    if obj is None:
        raise NotFoundError(
            f"Session participant not found for session ID {session_id} and user ID {user_id}."
        )
    return obj


def get_participant_or_raise(*, session: Session, id: int) -> SessionParticipant:
    obj = session.get(SessionParticipant, id)
    if obj is None:
        raise NotFoundError(f"Session participant not found: ID {id}.")
    return obj


def get_session_question_by_session_question_or_raise(
    *, session: Session, session_id: int, question_id: int
) -> SessionQuestion:
    obj = session.scalar(
        select(SessionQuestion).where(
            SessionQuestion.session_id == session_id,
            SessionQuestion.question_id == question_id,
        )
    )
    if obj is None:
        raise NotFoundError(
            f"Session question not found for session ID {session_id} and question ID {question_id}."
        )
    return obj
