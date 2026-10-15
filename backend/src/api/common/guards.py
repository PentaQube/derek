from datetime import datetime

from fastapi import Depends, HTTPException, Header, Query
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select, literal
from sqlalchemy.orm import Session

from src.core.database import get_session
from src.core.permissions import require_platform_admin
from src.core.utils import decode_token
from src.core.exceptions import AuthorizationError, AuthenticationError

from src.models.user import User
from src.models.community import CommunityUser
from src.core.session_participant_tokens import decode_session_participant_token

reuseable_oauth = OAuth2PasswordBearer(tokenUrl="/iam/tokens", scheme_name="JWT")


async def get_current_user(
    session: Session = Depends(get_session),
    token: str = Depends(reuseable_oauth),
) -> User:
    message_401 = "Invalid access token provided."
    message_500 = "Failed to get current user."

    try:
        payload = decode_token(token)

        # Get user from database
        user = session.scalar(select(User).where(User.email == payload["sub"].lower()))

        if user is None:
            raise HTTPException(
                status_code=401,
                detail=message_401,
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check password_updated_at
        password_updated_at_db = user.password_updated_at
        password_updated_at_pl = payload[
            "password_updated_at"
        ] and datetime.fromisoformat(payload["password_updated_at"])

        if password_updated_at_db != password_updated_at_pl:
            raise HTTPException(
                status_code=401,
                detail=message_401,
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user
    except JWTError:
        raise HTTPException(
            status_code=401, detail=message_401, headers={"WWW-Authenticate": "Bearer"}
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        session.rollback()

        raise HTTPException(status_code=500, detail=message_500)


async def is_platform_admin(current_user: User = Depends(get_current_user)) -> User:
    require_platform_admin(current_user)
    return current_user


async def is_commmunity_user(
    session: Session = Depends(get_session),
    community_id: int | None = Header(None, alias="Community-Id"),
    current_user: User = Depends(get_current_user),
) -> int | None:

    if community_id is None:
        raise HTTPException(
            status_code=400,
            detail="Community-Id header is required.",
        )

    is_exists = session.scalar(
        select(literal(1))
        .select_from(CommunityUser)
        .where(
            CommunityUser.user_id == current_user.id,
            CommunityUser.community_id == community_id,
        )
        .limit(1)
    )

    if is_exists is None:
        raise AuthorizationError("User does not belong to this community.")
    return community_id


def get_participant(token: str = Query(...)):
    try:
        return decode_session_participant_token(token)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
