from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from src.api.common.schemas import APIResponse
from src.api.common.guards import get_current_user
from src.core.database import get_session
from src.core.exceptions import ServiceError
from src.models.user import User
from src.services.session_question.common.schemas import UpdateSessionQuestionData
from src.services.session_question.update import update_session_questions_service
from ..common.out import SessionQuestionOut

router = APIRouter(prefix="")

DESCRIPTION = "Endpoint to update session questions."


@router.put(
    "/{session_id}",
    response_model=APIResponse,
    description="Update session questions",
)
async def update_session_questions(
    session_id: int,
    request_body: UpdateSessionQuestionData,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    return_data: Optional[bool] = None,
):
    message_200 = "Session questions updated successfully."
    message_500 = "Failed to update session questions."

    try:
        result = update_session_questions_service(
            session=session,
            session_id=session_id,
            data=request_body,
        )

        return APIResponse(
            status="success",
            code=200,
            message=message_200,
            data=(
                SessionQuestionOut.model_validate(result).model_dump()
                if return_data
                else None
            ),
        )
    except ServiceError:
        raise

    except Exception:
        raise HTTPException(status_code=500, detail=message_500)
