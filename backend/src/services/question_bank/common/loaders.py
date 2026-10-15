from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, select
from src.models.question_bank import QuestionBank
from src.core.exceptions import NotFoundError


# todo -- add name if needed
def get_QB(*, session: Session, id: Optional[int] = None) -> QuestionBank:

    if id is None:
        raise ValueError("Id  must be provided")

    conditions = []
    if id is not None:
        conditions.append(QuestionBank.id == id)

    QB = session.scalar(select(QuestionBank).where(or_(*conditions)))

    return QB


def get_QB_or_raise(
    *,
    session: Session,
    id: Optional[int] = None,
) -> QuestionBank:
    QuestionBank = get_QB(session=session, id=id)

    if QuestionBank is None:
        raise NotFoundError(f"Question bank with ID {id} not found.")

    return QuestionBank
