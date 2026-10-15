from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.common.schemas import APIResponse
from src.api.common.guards import get_current_user
from src.core.database import get_session
from src.core.exceptions import ServiceError
from src.models.user import User

from . import dependencies, examples
from src.api.session_question.common.out import SessionQuestionOut
from src.api.session.common.out import SessionOut
from src.api.question.common.out import QuestionOut

from src.services.session_question.list import list_session_question_service

router = APIRouter(prefix="")

DESCRIPTION = "Endpoint to list session questions."


@router.get(
    "/",
    response_model=APIResponse,
    description=DESCRIPTION,
    # responses=examples.list_session_question_examples,
)
async def list_session_question(
    params: dependencies.SessionQuestionListParams = Depends(
        dependencies.get_session_question_list_params
    ),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    message_200 = "Session questions listed successfully."
    message_500 = "Failed to list session questions."

    try:
        results = list_session_question_service(
            session=session,
            params=params,
        )

        validated_items = []
        for item in results["items"]:
            data = SessionQuestionOut.model_validate(item).model_dump()

            if "session" in params.expand:
                data["session"] = SessionOut.model_validate(item.session).model_dump()

            if "question" in params.expand:
                question_data = QuestionOut.model_validate(item.question).model_dump()
                # Inject is_triggered from SessionQuestion
                question_data["is_triggered"] = item.is_triggered
                data["question"] = question_data

            validated_items.append(data)

        return APIResponse(
            status="success",
            code=200,
            message=message_200,
            data=dict(
                total_count=results["total_count"],
                count=results["count"],
                items=validated_items,
            ),
        )
    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)
