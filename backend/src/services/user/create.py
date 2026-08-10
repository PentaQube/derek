from sqlalchemy import select
from sqlalchemy.orm import Session
from src.core.database import transactional
from src.core.permissions import require_platform_admin
from src.core.exceptions import NotFoundError
from src.models.user import User, UserStatus
from src.models.community import CommunityUser
from jose import jwt
from .common.preconditions import ensure_create_data_is_valid
from src.services.community.common.preconditions import ensure_community_exists
from .common.schemas import UserCreateData
from datetime import datetime, timezone,timedelta
from src.core.config import settings

def create_user_service(
    *, session: Session, data: UserCreateData, current_user: User
) -> User:
    # Auth check
    require_platform_admin(current_user)

    # Preconditions
    ensure_create_data_is_valid(session=session, data=data)

    with transactional(session):
       
        new_user = User(
            name=data.name,
            email=data.email,
            is_platform_admin=data.is_platform_admin,
            user_status_id=data.user_status_id,
            created_by=current_user.id,
            updated_by=current_user.id,
        )
        session.add(new_user)
        session.flush()

        # Communnity checks 
        if data.community_ids:
            valid_community_ids = []

            for community_id in data.community_ids:
                try:
                    ensure_community_exists(session=session,id=community_id)
                    valid_community_ids.append(community_id)
                except NotFoundError:
                    continue
            
            for community_id in valid_community_ids:
                session.add(
                    CommunityUser(
                        user_id=new_user.id,
                        community_id=community_id,
                    )
                )
        payload = {
        "sub": str(new_user.id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
    }
        token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
        return token,new_user
