from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.common.schemas import APIResponse
from src.api.common.guards import get_current_user
from src.core.database import get_session
from src.core.exceptions import ServiceError
from src.models.user import User
from src.services.question.create import create_question_service

from ..common.out import QuestionOut

from src.services.question.common.schemas import QuestionData

router = APIRouter(prefix="")

DESCRIPTION = """Endpoint to create question."""


@router.post(
    "/",
    response_model=APIResponse,
    description=DESCRIPTION,
)
async def create_question(
    request_body: QuestionData,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    return_data: bool | None = None,
):
    message_200 = "Question created successfully."
    message_500 = "Failed to Question create."

    try:
        result = create_question_service(
            session=session,
            data=request_body,
            current_user=current_user,
        )

        return APIResponse(
            status="success",
            code=200,
            message=message_200,
            data=(
                QuestionOut.model_validate(result).model_dump() if return_data else None
            ),
        )

    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)
