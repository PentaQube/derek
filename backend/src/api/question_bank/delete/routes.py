from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.api.common.guards import get_current_user
from src.api.common.schemas import APIResponse
from src.core.database import get_session
from src.core.exceptions import ServiceError
from src.models.user import User

from src.services.question_bank.delete import delete_question_bank_service


router = APIRouter(prefix="")

DESCRIPTION = """
    Endpoint to delete question_bank.
"""


@router.delete(
    "/{question_bank_id}",
    response_model=APIResponse,
    description=DESCRIPTION,
    # responses=examples
)
async def delete_question_bank(
    question_bank_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    message_200 = "Question_bank deleted successfully."
    message_500 = "Failed to Question_bank delete."
    try:
        delete_question_bank_service(
            session=session,
            question_bank_id=question_bank_id,
            current_user=current_user,
        )

        return APIResponse(status="success", code=200, message=message_200)
    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)
