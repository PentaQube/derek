from datetime import datetime

from sqlalchemy.orm import Session
from src.core.exceptions import AuthenticationError
from src.core.security import verify_password
from src.models.user import User
from src.services.user.common.loaders import get_user_status_or_raise


def ensure_user_password_is_correct(provided_password: str, user: User) -> None:
    if user.password_hash:
        if not verify_password(provided_password, user.password_hash):
            raise AuthenticationError


def ensure_user_is_active(session: Session, user: User) -> None:
    active_user_status = get_user_status_or_raise(session=session, code="active")
    if user.user_status_id != active_user_status.id:
        raise AuthenticationError("User is inactive. Contact an administrator.")


def ensure_password_updated_at_matches(payload: dict, user: User) -> None:
    password_updated_at_db = user.password_updated_at
    password_updated_at_pl = payload["password_updated_at"] and datetime.fromisoformat(
        payload["password_updated_at"]
    )

    if password_updated_at_db != password_updated_at_pl:
        raise AuthenticationError
