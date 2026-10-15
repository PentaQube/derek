from typing import Optional
from xml.dom import NotFoundErr
from sqlalchemy import and_, select
from sqlalchemy.orm import Session
from src.models.question import AnswerType, Question
from src.core.exceptions import NotFoundError


def get_answer_type(
    *, session: Session, id: Optional[int] = None, display_name: Optional[str] = None
) -> AnswerType:

    if id is None and display_name is None:
        raise ValueError("Either id or name must be provided")

    conditions = []
    if id is not None:
        conditions.append(AnswerType.id == id)
    if display_name is not None:
        conditions.append(AnswerType.display_name == display_name)

    return session.scalar(select(AnswerType).where(and_(*conditions)))


def get_answer_type_or_raise(*, session: Session, id: int) -> AnswerType:
    answerType = get_answer_type(session=session, id=id)
    if answerType is None:
        raise NotFoundError(f"Answer type with ID {id} not found.")
    return answerType


def get_question(*, session: Session, id: int) -> Question | None:
    return session.scalar(select(Question).where(Question.id == id))


def get_question_or_raise(*, session: Session, id: int) -> Question:
    question = session.scalar(select(Question).where(Question.id == id))
    if not question:
        raise NotFoundError("Question not found.")
    return question
