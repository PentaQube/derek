from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from src.core.database import transactional
from src.core.exceptions import AuthorizationError
from src.core.permissions import require_platform_admin
from src.models.community import Community, CommunityUser
from src.models.question_bank import QuestionBank
from src.models.user import User
from src.models.session import Session as AppSession

from .common.preconditions import ensure_community_exists


def delete_community_service(
    *, session: Session, community_id: int, current_user: User
) -> None:
    require_platform_admin(current_user)

    ensure_community_exists(session=session, id=community_id)

    has_users = session.scalar(
        select(CommunityUser.community_id).where(
            CommunityUser.community_id == community_id
        ).limit(1)
    ) is not None

    has_sessions = session.scalar(
        select(AppSession.id).where(AppSession.community_id == community_id).limit(1)
    ) is not None

    has_question_bank = session.scalar(
        select(QuestionBank.id).where(QuestionBank.community_id == community_id).limit(1)
    ) is not None

    if has_users or has_sessions or has_question_bank:
        raise AuthorizationError("This community cannot be deleted since it is in use.")

    with transactional(session):
        session.execute(delete(Community).where(Community.id == community_id))