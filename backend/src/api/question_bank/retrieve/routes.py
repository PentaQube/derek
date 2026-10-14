from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from websockets import Data
from src.api.common.guards import get_current_user
from src.api.common.schemas import APIResponse
from src.core.database import get_session
from src.core.exceptions import ServiceError
from src.services.question_bank.retrieve import retrieve_question_bank_service
from src.models.user import User
from src.api.question_bank.common.out import QuestionBankOut
from src.api.user.common.out import UserOut
from src.api.community.common.out import CommunityOut

from src.services.question_bank.common.params import (
    QuestionBankRetrieveParams,
    QuestionBankExpand,
)

from . import dependencies

router = APIRouter(prefix="")

DESCRIPTION = """
    Endpoint to retrieve question_bank.
"""


@router.get(
    "/{question_bank_id}",
    response_model=APIResponse,
    description=DESCRIPTION,
    # responses=examples.retrieve_question_bank_examples if hasattr(examples, "retrieve_question_bank_examples") else None,
)
async def retrieve_question_bank(
    question_bank_id: int,
    params: QuestionBankRetrieveParams = Depends(
        dependencies.get_question_bank_retrieve_params
    ),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    message_200 = "Question_bank retrieved successfully."
    message_500 = "Failed to Question_bank retrieve."
    try:
        question_bank = retrieve_question_bank_service(
            session=session,
            question_bank_id=question_bank_id,
            params=params,
            current_user=current_user,
        )
        data = QuestionBankOut.model_validate(question_bank).model_dump()

        expand_fields = {
            "created_by": ("created_by_user", UserOut),
            "updated_by": ("updated_by_user", UserOut),
            "community": ("community_id_QB", CommunityOut),
        }
        for key, (attr, out_schema) in expand_fields.items():
            if getattr(QuestionBankExpand, key) in params.expand:
                data[key] = (
                    out_schema.model_validate(getattr(question_bank, attr)).model_dump()
                    if getattr(question_bank, attr)
                    else None
                )

        return APIResponse(status="success", code=200, message=message_200, data=data)
    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)
