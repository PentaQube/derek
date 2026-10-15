from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.common.schemas import APIResponse
from src.api.common.guards import get_current_user
from src.core.database import get_session
from src.core.exceptions import ServiceError
from src.models.user import User

from src.services.session_question.retrieve import retrieve_session_question_service
from src.services.session_question.common.params import (
    SessionQuestionRetrieveParams,
    SessionQuestionExpand,
)
from src.api.session_question.common.out import SessionQuestionOut
from . import dependencies, examples
from src.api.user.common.out import UserOut
from src.api.session.common.out import SessionOut
from src.api.question.common.out import QuestionOut

router = APIRouter(prefix="")

DESCRIPTION = "Endpoint to retrieve a session question."


@router.get(
    "/{session_question_id}",
    response_model=APIResponse,
    description=DESCRIPTION,
)
async def retrieve_session_question(
    session_question_id: int,
    params: SessionQuestionRetrieveParams = Depends(
        dependencies.get_session_retrieve_params
    ),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    message_200 = "Session question retrieved successfully."
    message_500 = "Failed to retrieve the session question."

    try:
        session_question_obj = retrieve_session_question_service(
            session=session,
            session_question_id=session_question_id,
            params=params,
        )

        data = SessionQuestionOut.model_validate(session_question_obj).model_dump()
        expand_fields = {
            "session": ("session", SessionOut),
            "question": ("question", QuestionOut),
        }
        for key, (attr, out_schema) in expand_fields.items():
            if getattr(SessionQuestionExpand, key) in params.expand:
                data[key] = (
                    out_schema.model_validate(
                        getattr(session_question_obj, attr)
                    ).model_dump()
                    if getattr(session_question_obj, attr)
                    else None
                )

        return APIResponse(status="success", code=200, message=message_200, data=data)

    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)
