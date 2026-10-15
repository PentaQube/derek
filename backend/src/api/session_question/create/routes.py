from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..common.out import SessionQuestionOut
from src.api.common.schemas import APIResponse
from src.api.common.guards import get_current_user
from src.core.database import get_session
from src.core.exceptions import ServiceError
from src.models.user import User
from src.services.session_question.create import create_session_service
from src.services.session_question.common.schemas import CreateSessionQuestionData

router = APIRouter(prefix="")

DESCRIPTION = "Endpoint to create a session question."


@router.post(
    "/",
    response_model=APIResponse,
    description=DESCRIPTION,
)
async def create_session_question(
    request_body: CreateSessionQuestionData,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    return_data: bool | None = None,
):
    message_200 = "Session question created successfully."
    message_500 = "Failed to create the session question."

    try:

        data = create_session_service(data=request_body, session=session)
        return APIResponse(
            status="success",
            code=200,
            message=message_200,
            data=(
                SessionQuestionOut.model_validate(data).model_dump()
                if return_data
                else None
            ),
        )
    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)
