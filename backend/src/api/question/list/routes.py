from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.common.schemas import APIResponse
from src.api.common.guards import get_current_user
from src.core.database import get_session
from src.core.exceptions import ServiceError
from src.models.user import User

from src.services.question.list import list_question_service, get_answer_type_service
from src.services.question.common.params import QuestionExpand, QuestionListParams

from src.api.question.common.out import QuestionOut, AnswerTypeOut
from src.api.user.common.out import UserOut
from . import dependencies


router = APIRouter(prefix="")

DESCRIPTION = """Endpoint to list question."""


@router.get(
    "/",
    response_model=APIResponse,
    description=DESCRIPTION,
)
async def list_question(
    params: QuestionListParams = Depends(dependencies.get_question_list_params),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    message_200 = "Questions listed successfully."
    message_500 = "Failed to list questions."

    try:
        questions = list_question_service(
            session=session,
            params=params,
            current_user=current_user,
        )

        validated_items = []

        for question in questions["items"]:
            data = QuestionOut.model_validate(question).model_dump()

            if QuestionExpand.created_by in params.expand:
                data["created_by"] = (
                    UserOut.model_validate(question.created_by_user).model_dump()
                    if getattr(question, "created_by_user", None)
                    else None
                )

            if QuestionExpand.updated_by in params.expand:
                data["updated_by"] = (
                    UserOut.model_validate(question.updated_by_user).model_dump()
                    if getattr(question, "updated_by_user", None)
                    else None
                )

            validated_items.append(data)

        return APIResponse(
            status="success",
            code=200,
            message=message_200,
            data=dict(
                total_count=questions["total_count"],
                count=questions["count"],
                items=validated_items,
            ),
        )

    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)


@router.get("/answer-type", response_model=APIResponse, description=DESCRIPTION)
async def get_session_status(session: Session = Depends(get_session)):
    message_200 = "Answer type fetched successfully."
    message_500 = "Failed to fetch answer type."
    try:
        session_status = get_answer_type_service(session=session)
        data = [
            AnswerTypeOut.model_validate(status).model_dump()
            for status in session_status
        ]
        return APIResponse(status="success", code=200, message=message_200, data=data)
    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)
