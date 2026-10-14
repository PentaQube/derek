from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional, List

from src.api.common.schemas import APIResponse
from src.api.common.guards import get_current_user
from src.core.database import get_session
from src.core.exceptions import ServiceError
from src.models.user import User
from src.services.session_question.delete import (
    delete_session_questions_service,
)
from src.services.session_question.common.schemas import DeleteSessionQuestionData

router = APIRouter(prefix="")

DESCRIPTION = "Endpoint to delete session_question."


@router.delete(
    "/{session_id}",
    response_model=APIResponse,
    description=DESCRIPTION,
)
async def delete_selected_session_questions(
    session_id: int,
    request_body: Optional[DeleteSessionQuestionData] = Body(None),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    message_200 = "SessionQuestion deleted successfully."
    message_500 = "Failed to session_question delete."

    try:
        deleted_count = delete_session_questions_service(
            session=session,
            session_id=session_id,
            data=request_body,
        )

        return APIResponse(
            status="success",
            code=200,
            message=message_200,
            data={"deleted_count": deleted_count},
        )

    except ServiceError:
        raise

    except Exception:
        raise HTTPException(status_code=500, detail=message_500)
