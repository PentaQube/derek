from datetime import datetime, timezone,timedelta
from sqlalchemy.orm import Session
from src.core.database import transactional
from src.core.exceptions import AuthenticationError
from src.core.security import verify_password, get_hashed_password
from src.models.user import User
from jose import jwt
from src.core.config import settings
from src.services.user.common.loaders import get_user_or_raise
from pydantic import EmailStr


def change_password_service(
    *,
    session: Session,
    user: User,
    current_password: str,
    new_password: str,
) -> User:
    if not user.password_hash or not verify_password(
        current_password, user.password_hash
    ):
        raise AuthenticationError("Current password is incorrect.")

    if current_password == new_password:
        raise AuthenticationError(
            "New password must be different from current password."
        )

    with transactional(session):
        user.password_hash = get_hashed_password(new_password)
        user.password_updated_at = datetime.now(timezone.utc)
        user.updated_by = user.id
        return user


def forgot_password_service(
    *,
    session: Session,
    email: EmailStr,
):
    user = get_user_or_raise(session=session, email=email)

    if user.email is None:
        raise AuthenticationError("Invalid email.")

        #  Create token
    payload = {
        "sub": str(user.id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
    }

    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token, user.email, user.name or "User"


def reset_password_sevice(
    *,
    session: Session,
    token: str,
    new_password: str,
):
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    user_id = payload.get("sub")
    user = get_user_or_raise(session=session, id=int(user_id))
    user.password_hash = get_hashed_password(new_password)
    session.commit()
