from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.common.schemas import APIResponse
from src.api.common.guards import get_current_user
from src.core.database import get_session
from src.core.exceptions import ServiceError
from src.models.user import User

from src.api.question.common.out import QuestionOut

from src.services.question.update import update_question_service
from src.services.question.common.schemas import QuestionUpdateData

router = APIRouter(prefix="")

DESCRIPTION = """Endpoint to update question."""


@router.patch(
    "/{question_id}",
    response_model=APIResponse,
    description=DESCRIPTION,
)
async def update_question(
    request_body: QuestionUpdateData,
    question_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    return_data: bool | None = None,
):
    message_200 = "Question updated successfully."
    message_500 = "Failed to update question."

    try:

        update_question = update_question_service(
            session=session,
            question_id=question_id,
            data=request_body,
            current_user=current_user,
        )

        return APIResponse(
            status="success",
            code=200,
            message=message_200,
            data=(
                QuestionOut.model_validate(update_question).model_dump()
                if return_data
                else None
            ),
        )

    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)
