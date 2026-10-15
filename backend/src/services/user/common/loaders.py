from typing import Optional

from pydantic import EmailStr
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from src.core.exceptions import NotFoundError
from src.models.user import User, UserStatus


def get_user(
    *, session: Session, id: Optional[int] = None, email: Optional[EmailStr] = None
) -> User:
    if id is None and email is None:
        raise ValueError("Either id or email must be provided")

    query = select(User)

    if id is not None:
        query = query.where(User.id == id)

    if email is not None:
        query = query.where(User.email == email)

    return session.scalar(query)


def get_user_or_raise(
    *, session: Session, id: Optional[int] = None, email: Optional[EmailStr] = None
) -> User:
    user = get_user(session=session, id=id, email=email)
    if user is None:
        identifier = id if id is not None else email
        raise NotFoundError(f"User with identifier {identifier} not found.")

    return user


def get_user_status(
    *, session: Session, id: Optional[int] = None, code: Optional[str] = None
) -> UserStatus:
    if id is None and code is None:
        raise ValueError("Either id or code must be provided")

    conditions = []
    if id is not None:
        conditions.append(UserStatus.id == id)
    if code is not None:
        conditions.append(UserStatus.code == code)

    user_status = session.scalar(select(UserStatus).where(or_(*conditions)))

    return user_status


def get_user_status_or_raise(
    *, session: Session, id: Optional[int] = None, code: Optional[str] = None
) -> UserStatus:
    user_status = get_user_status(session=session, id=id, code=code)

    if user_status is None:
        identifier = id if id is not None else code
        raise NotFoundError(f"User with identifier {identifier} not found.")

    return user_status


def validate_user_ids_or_raise(session: Session, user_ids: list[int]) -> list[int]:
    if not user_ids:
        return []
    existing_users = session.scalars(select(User.id).where(User.id.in_(user_ids))).all()

    if not existing_users:
        raise NotFoundError("None of the provided user IDs exist.")
    return list(existing_users)
