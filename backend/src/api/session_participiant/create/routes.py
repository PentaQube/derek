from fastapi import APIRouter, Depends, HTTPException
from src.api.common.schemas import APIResponse

from src.services.session_participant.common.schemas import (
    SessionParticipantCreate,
)
from src.models.user import User
from src.api.common.guards import is_platform_admin
from src.core.database import get_session
from typing import Optional
from sqlalchemy.orm import Session
from src.services.session_participant.create import (
    add_session_participiants_service,
)
from src.api.session_participiant.common.out import SessionParticipantOut
from src.core.exceptions import ServiceError

router = APIRouter(prefix="")
DESCRIPTION = """
    Endpoint to create a useSession participiant.
"""


@router.post("/", response_model=APIResponse, description=DESCRIPTION)
async def add_session_parcipiant(
    request_body: SessionParticipantCreate,
    current_user: User = Depends(is_platform_admin),
    session: Session = Depends(get_session),
    return_data: Optional[bool] = None,
):
    message_200 = "Joined the session successfully."
    message_500 = "Failed to join the session."

    try:
        participiant = add_session_participiants_service(
            session=session,
            data=request_body,
            current_user=current_user,
        )

        return APIResponse(
            status="success",
            code=200,
            message=message_200,
            data=(
                SessionParticipantOut.model_validate(participiant).model_dump()
                if return_data
                else None
            ),
        )
    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)
