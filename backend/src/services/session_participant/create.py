from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from src.core.database import transactional
from src.core.permissions import require_platform_admin

from src.core.exceptions import AuthorizationError, AlreadyExistsError

from src.models.user import User
from src.models.session import SessionParticipant

from src.services.user.common.loaders import get_user_status_or_raise

from src.services.session.common.loaders import (
    get_session_or_raise,
    get_session_status_or_raise,
)
from src.services.session_participant.common.loaders import (
    get_participant_by_session_user,
)

from src.core.session_participant_tokens import create_session_participant_token

from .common.schemas import SessionParticipantCreate, SessionParticipantJoinByLink
from .common.preconditions import ensure_create_data_is_valid


def _get_user_by_email(*, session: Session, normalized_email: str) -> User | None:
    stmt = select(User).where(func.lower(User.email) == normalized_email)
    return session.scalar(stmt)


# & either get user or create user
def _get_or_create_user_for_join(*, session: Session, name: str, email: str) -> User:
    normalized_email = email.strip().lower()
    normalized_name = name.strip()
    existing = _get_user_by_email(session=session, normalized_email=normalized_email)
    if existing is not None:
        return existing
    inactive_status = get_user_status_or_raise(session=session, code="inactive")

    try:
        with transactional(session):
            user = User(
                name=normalized_name,
                email=normalized_email,
                user_status_id=inactive_status.id,
            )
            session.add(user)
            session.flush()
            return user
    except IntegrityError:
        # Handle race: another request inserted the same email
        existing = _get_user_by_email(
            session=session, normalized_email=normalized_email
        )
        if existing is not None:
            return existing
        raise


def add_session_participiants_service(
    *, session: Session, data: SessionParticipantCreate, current_user: User
) -> SessionParticipant:
    require_platform_admin(current_user)
    ensure_create_data_is_valid(session=session, data=data)

    with transactional(session):
        new_participiant = SessionParticipant(
            user_id=data.user_id, session_id=data.session_id
        )
        session.add(new_participiant)

        return new_participiant


# & neat :)
def join_live_session_by_link_service(
    *, session: Session, session_id: int, data: SessionParticipantJoinByLink
) -> tuple[SessionParticipant, bool]:
    session_data = get_session_or_raise(session=session, id=session_id)
    ongoing_status = get_session_status_or_raise(session=session, code="ongoing")

    if session_data.session_status_id != ongoing_status.id:
        raise AuthorizationError("Session is not live (ongoing) yet")

    user = _get_or_create_user_for_join(
        session=session, name=data.name, email=data.email
    )

    # & Check if already exist -->  # TODO may be not needed need to check
    existing = get_participant_by_session_user(
        session=session,
        session_id=session_id,
        user_id=user.id,
    )

    if existing:
        raise AlreadyExistsError("User has already joined this session.")

    with transactional(session):
        participant = SessionParticipant(session_id=session_id, user_id=user.id)
        session.add(participant)
        session.flush()
        return participant, True


def join_live_session_by_link_with_token_service(
    *, session: Session, session_id: int, data: SessionParticipantJoinByLink
) -> tuple[SessionParticipant, bool, str]:
    session_data = get_session_or_raise(session=session, id=session_id)
    ongoing_status = get_session_status_or_raise(session=session, code="ongoing")

    if session_data.session_status_id != ongoing_status.id:
        raise AuthorizationError("Session is not live (ongoing) yet")

    user = _get_or_create_user_for_join(
        session=session, name=data.name, email=data.email
    )

    existing = get_participant_by_session_user(
        session=session,
        session_id=session_id,
        user_id=user.id,
    )

    if existing is not None:
        token = create_session_participant_token(
            session_id=session_id,
            user_id=user.id,
            session_participant_id=existing.id,
        )
        return existing, False, token

    with transactional(session):
        participant = SessionParticipant(session_id=session_id, user_id=user.id)
        session.add(participant)
        session.flush()
        token = create_session_participant_token(
            session_id=session_id,
            user_id=user.id,
            session_participant_id=participant.id,
        )
        return participant, True, token
