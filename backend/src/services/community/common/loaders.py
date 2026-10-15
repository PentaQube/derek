from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, select

from src.models.community import Community, CommunityUser
from src.models.user import User
from src.core.exceptions import NotFoundError
from .statements import base_select_stmt


def get_community(
    *, session: Session, id: Optional[int] = None, name: Optional[str] = None
) -> Community:
    if id is None and name is None:
        raise ValueError("Either id is or name must be provided")
    conditions = []
    if id is not None:
        conditions.append(Community.id == id)
    if name is not None:
        conditions.append(Community.name == name)
    community = session.scalar(base_select_stmt.where(or_(*conditions)))
    return community


def get_community_or_raise(
    *, session: Session, id: Optional[int] = None, name: Optional[str] = None
) -> Community:
    community = get_community(session=session, id=id, name=name)
    if community is None:
        identifier = id if id is not None else name
        raise NotFoundError(f"Community with identifier {identifier} not found.")
    return community


def get_community_user_ids(session: Session, community_id: int) -> list[int]:
    users_ids = session.scalars(
        select(User.id)
        .join(CommunityUser, User.id == CommunityUser.user_id)
        .where(CommunityUser.community_id == community_id)
    ).all()
    return users_ids


def get_first_community_id_of_user(session: Session, user_id: int) -> int:
    if user_id is None:
        raise ValueError("User Id must be provided")
    community_id = session.scalar(
        select(CommunityUser.community_id)
        .where(CommunityUser.user_id == user_id)
        .order_by(CommunityUser.community_id.asc())
        .limit(1)
    )
    return community_id
