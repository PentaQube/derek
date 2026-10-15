import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.common.guards import get_current_user
from src.api.common.schemas import APIResponse
from src.core.database import get_session
from src.core.exceptions import ServiceError, NotFoundError
from src.core.ws import ws_manager
from src.models.user import User
from src.services.session.start_question import start_question_service

router = APIRouter(prefix="")


@router.post(
    "/{session_id}/start-question/{question_id}",
    response_model=APIResponse,
    description="Admin trigger to start/broadcast a question to the session WebSocket group.",
)
async def start_question(
    session_id: int,
    question_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    message_200 = "Question started successfully."
    message_500 = "Failed to start question."

    try:
        payload = start_question_service(
            session=session,
            session_id=session_id,
            question_id=question_id,
            current_user=current_user,
        )

        if payload.get("error") == "session_question_not_found":
            raise NotFoundError("Question not found in this session.")

        await ws_manager.broadcast_text(str(session_id), json.dumps(payload))
        session.commit()

        return APIResponse(
            status="success", code=200, message=message_200, data=payload
        )
    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)
