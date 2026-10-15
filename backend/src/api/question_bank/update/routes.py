from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.common.guards import get_current_user
from src.api.common.schemas import APIResponse
from src.api.question_bank.common.out import QuestionBankOut

from src.core.database import get_session
from src.core.exceptions import ServiceError
from src.services.question_bank.common.schemas import QuestionBankUpdateData
from src.services.question_bank.update import update_question_bank_service
from src.models.user import User


router = APIRouter(prefix="")

DESCRIPTION = """
    Endpoint to update a question bank.
"""


@router.patch(
    "/{question_bank_id}",
    response_model=APIResponse,
    description=DESCRIPTION,
    # responses=examples.
)
async def update_question_bank(
    question_bank_id: int,
    request_body: QuestionBankUpdateData,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    return_data: Optional[bool] = None,
):
    message_200 = "Question bank updated successfully."
    message_500 = "Failed to update question bank."

    try:
        update_QB = update_question_bank_service(
            session=session,
            question_bank_id=question_bank_id,
            data=request_body,
            current_user=current_user,
        )
        return APIResponse(
            status="success",
            code=200,
            message=message_200,
            data=(
                QuestionBankOut.model_validate(update_QB).model_dump()
                if return_data
                else None
            ),
        )
    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)
