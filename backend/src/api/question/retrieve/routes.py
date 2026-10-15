from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.common.schemas import APIResponse
from src.api.common.guards import get_current_user
from src.core.database import get_session
from src.core.exceptions import ServiceError
from src.models.user import User
from src.services.question.retrieve import retrieve_question_service
from src.services.question.common.params import QuestionExpand, QuestionRetrieveParams
from src.api.question.common.out import QuestionOut, AnswerTypeOut
from src.api.question_bank.common.out import QuestionBankOut
from src.api.user.common.out import UserOut
from . import dependencies, examples


router = APIRouter(prefix="")

DESCRIPTION = """Endpoint to retrieve question."""


@router.get(
    "/{question_id}",
    response_model=APIResponse,
    description=DESCRIPTION,
)
async def retrieve_question(
    question_id: int,
    params: QuestionRetrieveParams = Depends(dependencies.get_question_retrieve_params),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    message_200 = "Question retrieved successfully."
    message_500 = "Failed to retrieve question."

    try:

        question = retrieve_question_service(
            session=session,
            question_id=question_id,
            params=params,
            current_user=current_user,
        )

        data = QuestionOut.model_validate(question).model_dump()

        expand_fields = {
            "created_by": ("created_by_user", UserOut),
            "updated_by": ("updated_by_user", UserOut),
            "question_bank": ("question_bank", QuestionBankOut),
            "answer_type": ("answer_type", AnswerTypeOut),
        }
        for key, (attr, out_schema) in expand_fields.items():
            if getattr(QuestionExpand, key) in params.expand:
                data[key] = (
                    out_schema.model_validate(getattr(question, attr)).model_dump()
                    if getattr(question, attr)
                    else None
                )

        return APIResponse(status="success", code=200, message=message_200, data=data)

    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)
