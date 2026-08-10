from sqlalchemy import delete
from sqlalchemy.orm import Session 
from src.core.database import transactional
from src.core.permissions import require_platform_admin
from src.models.user import User
from src.models.community import Community
from src.models.community import CommunityUser
from src.services.user.common.loaders import validate_user_ids_or_raise
from .common.schemas import CommunityUpdateData
from .common.loaders import get_community_or_raise, get_community_user_ids


def update_community_service(
    *,
    session: Session,
    community_id: int,
    data: CommunityUpdateData,
    current_user: User,
) -> Community:
    require_platform_admin(current_user)

    # Load community
    community = get_community_or_raise(session=session, id=community_id)

    # Validate users only if field was sent
    validated_user_ids: set[int] | None = None
    if data.user_ids is not None:
        validated_user_ids = set(
            validate_user_ids_or_raise(
                session=session,
                user_ids=data.user_ids,
            )
        )

    with transactional(session):

        # 1. Update community fields
        if data.name is not None:
            community.name = data.name

        community.updated_by = current_user.id
        session.flush()

        # 2.
        if validated_user_ids is not None:

            # current ids
            current_ids = set(
                get_community_user_ids(session=session, community_id=community_id)
            )

            #  diff
            ids_to_add = validated_user_ids - current_ids
            ids_to_remove = current_ids - validated_user_ids

            # # Remove users
            if ids_to_remove:
                session.execute(
                    delete(CommunityUser).where(
                        CommunityUser.community_id == community_id,
                        CommunityUser.user_id.in_(ids_to_remove),
                    )
                )

            # Add users
            for user_id in ids_to_add:
                session.add(
                    CommunityUser(
                        community_id=community_id,
                        user_id=user_id,
                    )
                )

        session.flush()

    return community
