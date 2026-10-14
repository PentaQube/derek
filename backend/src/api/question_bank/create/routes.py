from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.api.common.guards import get_current_user
from src.api.common.schemas import APIResponse
from src.core.database import get_session
from src.core.exceptions import ServiceError

from src.models.user import User

from src.services.question_bank.create import create_question_bank_service
from src.services.question_bank.common.schemas import QuestionBankData
from src.api.question_bank.common.out import QuestionBankOut

router = APIRouter(prefix="")

DESCRIPTION = """
    Endpoint to create question_bank.
"""


@router.post(
    "/",
    response_model=APIResponse,
    description=DESCRIPTION,
    # responses=examples.,
)
async def create_question_bank(
    request_body: QuestionBankData,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    return_data: Optional[bool] = None,
):
    message_200 = "Question_bank created successfully."
    message_500 = "Failed to Question_bank create."

    try:
        new_community = create_question_bank_service(
            session=session,
            data=request_body,
            current_user=current_user,
        )

        return APIResponse(
            status="success",
            code=200,
            message=message_200,
            data=(
                QuestionBankOut.model_validate(new_community).model_dump()
                if return_data
                else None
            ),
        )

    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)
