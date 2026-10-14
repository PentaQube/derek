from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.api.common.guards import get_current_user, is_commmunity_user
from src.api.common.schemas import APIResponse
from src.core.database import get_session
from src.core.exceptions import ServiceError

from src.models.user import User
from src.api.user.common.out import UserOut
from src.services.question_bank.common.params import (
    QuestionBankExpand,
    QuestionBankListParams,
)

from src.services.question_bank.list import list_question_bank_service
from ..common.out import QuestionBankOut
from . import dependencies


router = APIRouter(prefix="")

DESCRIPTION = """
    Endpoint to list question_bank.
"""


@router.get(
    "/",
    response_model=APIResponse,
    description=DESCRIPTION,
    # responses=examples.
)
async def list_question_bank(
    params: QuestionBankListParams = Depends(
        dependencies.get_question_bank_list_params
    ),
    current_user: User = Depends(get_current_user),
    community_id: int = Depends(is_commmunity_user),
    session: Session = Depends(get_session),
):
    message_200 = "Question_bank listed successfully."
    message_500 = "Failed to Question_bank list."
    try:
        question_banks = list_question_bank_service(
            session=session, params=params, community_id=community_id
        )

        validated_items = []
        for row in question_banks["items"]:
            question_bank = row[0]
            questions_count = row[1]
            data = QuestionBankOut.model_validate(question_bank).model_dump()
            data["questions_count"] = int(questions_count or 0)

            if QuestionBankExpand.created_by in params.expand:
                data["created_by"] = (
                    UserOut.model_validate(question_bank.created_by_user).model_dump()
                    if getattr(question_bank, "created_by_user", None)
                    else None
                )

            if QuestionBankExpand.updated_by in params.expand:
                data["updated_by"] = (
                    UserOut.model_validate(question_bank.updated_by_user).model_dump()
                    if getattr(question_bank, "updated_by_user", None)
                    else None
                )

            validated_items.append(data)
        return APIResponse(
            status="success",
            code=200,
            message=message_200,
            data=dict(
                total_count=question_banks["total_count"],
                count=question_banks["count"],
                items=validated_items,
            ),
        )
    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)
