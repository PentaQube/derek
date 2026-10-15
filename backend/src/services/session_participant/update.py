from sqlalchemy.orm import Session

from src.core.database import transactional
from src.core.permissions import require_platform_admin
from src.core.exceptions import NotFoundError
from src.models.user import User
from src.models.session import SessionParticipant
from .common.schemas import SessionParticipantUpdate


def update_session_participant_service(
    *,
    session: Session,
    participant_id: int,
    data: SessionParticipantUpdate,
    current_user: User,
) -> SessionParticipant:
    require_platform_admin(current_user)

    participant = session.get(SessionParticipant, participant_id)

    if not participant:
        raise NotFoundError(
            f"Session participant with ID {participant_id} not found."
        )

    with transactional(session):
        if data.total_score is not None:
            participant.total_score = data.total_score

        if data.total_time_taken_ms is not None:
            participant.total_time_taken_ms = data.total_time_taken_ms

        return participant
