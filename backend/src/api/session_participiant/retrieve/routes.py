from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.common.guards import get_current_user, get_participant
from src.api.common.schemas import APIResponse
from src.api.session_participiant.common.out import SessionParticipantOut
from src.core.database import get_session
from src.core.exceptions import AuthenticationError, ServiceError
from src.models.user import User
from src.services.session_participant.retrieve import (
    retrieve_session_participant_service,
    get_participiant_last_question,
)

router = APIRouter(prefix="")


DESCRIPTION = """
    Endpoint to retrieve a session participant.
"""


@router.get("/{participant_id}", response_model=APIResponse, description=DESCRIPTION)
async def retrieve_session_participiant(
    participant_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    message_200 = "Session participant retrieved successfully."
    message_500 = "Failed to retrieve session participant."

    try:
        participiant = retrieve_session_participant_service(
            session=session,
            participant_id=participant_id,
            current_user=current_user,
        )

        data = SessionParticipantOut.model_validate(participiant).model_dump()

        return APIResponse(
            status="success",
            code=200,
            message=message_200,
            data=data,
        )

    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)


@router.get(
    "/session_progress/{session_id}",
    response_model=APIResponse,
    description=DESCRIPTION,
)
async def get_last_queation(
    session_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_participant),
):
    message_200 = "Last question retrieved successfully."
    message_500 = "Failed to retrieve last question."

    try:
        participiant_id = current_user.spid
        if participiant_id is None:
            raise HTTPException(status_code=404, detail="Coundn't find participiant ")

        question = get_participiant_last_question(
            session=session,
            session_id=session_id,
            participant_id=participiant_id,
        )

        return APIResponse(
            status="success",
            code=200,
            message=message_200,
            data=question,
        )

    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)
