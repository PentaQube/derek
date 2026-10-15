import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.common.schemas import APIResponse
from src.api.session_participiant.common.out import SessionParticipantOut
from src.api.user.common.out import UserOut
from src.core.database import get_session
from src.core.exceptions import ServiceError
from src.core.ws import ws_manager
from src.models.user import User
from src.services.session_participant.common.schemas import SessionParticipantJoinByLink
from src.services.session_participant.create import (
    join_live_session_by_link_with_token_service,
)

router = APIRouter(prefix="")


@router.post(
    "/join/{session_id}",
    response_model=APIResponse,
    description="Public join: join a live (ongoing) session via link (name/email). Returns a participant token for WS.",
)
async def join_live_session(
    request_body: SessionParticipantJoinByLink,
    session_id: int,
    session: Session = Depends(get_session),
    return_data: Optional[bool] = None,
    expand: Optional[str] = None,
):
    message_200 = "Joined the live session successfully."
    message_500 = "Failed to join the live session."

    try:
        participant, created, participant_token = (
            join_live_session_by_link_with_token_service(
                session=session,
                session_id=session_id,
                data=request_body,
            )
        )

        if created:
            user = session.get(User, participant.user_id)
            payload = {
                "type": "participant_joined",
                "session_id": session_id,
                "participant": {
                    "id": participant.id,
                    "user_id": participant.user_id,
                    "name": user.name if user else None,
                    "email": user.email if user else None,
                    "total_score": getattr(participant, "total_score", 0),
                    "total_time_taken_ms": getattr(
                        participant, "total_time_taken_ms", 0
                    ),
                },
            }
            await ws_manager.broadcast_text(str(session_id), json.dumps(payload))

        data: dict | None = {
            "participant_token": participant_token,
            "session_participant_id": participant.id,
        }

        if return_data:
            participant_data = SessionParticipantOut.model_validate(
                participant
            ).model_dump()
            if expand == "user":
                user_obj = session.get(User, participant.user_id)
                participant_data["user"] = (
                    UserOut.model_validate(user_obj).model_dump() if user_obj else None
                )
            data["participant"] = participant_data

        return APIResponse(status="success", code=200, message=message_200, data=data)
    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)
