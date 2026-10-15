from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.common.schemas import APIResponse
from src.api.common.guards import get_current_user
from src.core.database import get_session
from src.core.exceptions import ServiceError
from src.models.user import User
from src.services.question.delete import delete_question_service


router = APIRouter(prefix="")

DESCRIPTION = """Endpoint to delete question."""


@router.delete(
    "/{question_id}",
    response_model=APIResponse,
    description=DESCRIPTION,
)
async def delete_question(
    question_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    message_200 = "Question deleted successfully."
    message_500 = "Failed to delete question."

    try:

        delete_question_service(
            session=session,
            question_id=question_id,
            current_user=current_user,
        )

        return APIResponse(status="success", code=200, message=message_200)

    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)
