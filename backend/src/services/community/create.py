from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.database import transactional
from src.core.permissions import require_platform_admin
from src.models.community import Community, CommunityUser
from src.models.user import User, UserStatus
from src.services.user.common.loaders import validate_user_ids_or_raise


def create_community_service(
    *, session: Session, data: dict, current_user: User
) -> Community:
    require_platform_admin(current_user)

    user_ids = data.get("user_ids") or []

    validated_user_ids = (
        validate_user_ids_or_raise(session=session, user_ids=user_ids)
        if user_ids
        else []
    )

    with transactional(session):
        new_community = Community(
            name=data["name"],
            created_by=current_user.id,
            updated_by=current_user.id,
        )
        session.add(new_community)
        session.flush()

        for user_id in validated_user_ids:
            session.add(
                CommunityUser(
                    community_id=new_community.id,
                    user_id=user_id,
                )
            )

        return new_community