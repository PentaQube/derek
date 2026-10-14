from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.common.schemas import APIResponse
from src.api.common.helper import expand_if_requested
from src.api.common.guards import (
    is_commmunity_user,
    get_current_user,
)

from src.api.session.common.out import SessionOut, SessionStatusOut, AnswerStatusOut
from src.api.user.common.out import UserOut
from src.api.community.common.out import CommunityOut

from src.core.database import get_session
from src.core.exceptions import ServiceError
from src.models.user import User

from src.services.session.common.params import SessionExpand, SessionListParams
from src.services.session.list import (
    list_session_service,
    get_session_status_service,
    session_status_counts_service,
    get_answer_status_service,
)

from . import dependencies


router = APIRouter(prefix="")

DESCRIPTION = """Endpoint to list session."""


@router.get(
    "/",
    response_model=APIResponse,
    description=DESCRIPTION,
)
async def list_session(
    params: SessionListParams = Depends(dependencies.get_session_list_params),
    current_user: User = Depends(get_current_user),
    community_id: int | None = Depends(is_commmunity_user),
    session: Session = Depends(get_session),
):
    message_200 = "Session listed successfully."
    message_500 = "Failed to Session list."

    try:
        sessions_data = list_session_service(
            session=session,
            params=params,
            current_user=current_user,
            community_id=community_id,
        )

        validated_items = []
        for sesion_data in sessions_data["items"]:
            data = SessionOut.model_validate(sesion_data).model_dump(
                exclude={"questions"}
            )

            expanded_fields = {
                "community": (
                    SessionExpand.community,
                    sesion_data.community,
                    CommunityOut,
                ),
                "session_status": (
                    SessionExpand.session_status,
                    sesion_data.session_status,
                    SessionStatusOut,
                ),
                "created_by": (
                    SessionExpand.created_by,
                    sesion_data.created_by_user,
                    UserOut,
                ),
                "updated_by": (
                    SessionExpand.updated_by,
                    sesion_data.updated_by_user,
                    UserOut,
                ),
            }
            for key, (expand_enum, value, schema) in expanded_fields.items():
                expanded = expand_if_requested(
                    expand_enum, params.expand, value, schema
                )
                if expanded is not None:
                    data[key] = expanded

            if SessionExpand.session_question in params.expand:
                questions = []
                for session_question in sesion_data.session_questions or []:
                    question = session_question.question
                    if not question:
                        continue
                    questions.append(
                        {
                            "id": question.id,
                            "title": question.title,
                            "answer_type": question.answer_type_id,
                            "question_bank": question.question_bank_id,
                            "is_scored": question.is_scored,
                            "time_limit_ms": question.time_limit_ms,
                            "is_triggered": session_question.is_triggered,
                        }
                    )
                data["questions"] = questions

            validated_items.append(data)

        return APIResponse(
            status="success",
            code=200,
            message=message_200,
            data=dict(
                total_count=sessions_data["total_count"],
                count=sessions_data["count"],
                items=validated_items,
            ),
        )
    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)


@router.get("/status", response_model=APIResponse, description=DESCRIPTION)
async def get_session_status(session: Session = Depends(get_session)):
    message_200 = "Session status fetched successfully."
    message_500 = "Failed to fetch Session status."
    try:
        session_status = get_session_status_service(session=session)
        data = [
            SessionStatusOut.model_validate(status).model_dump()
            for status in session_status
        ]
        return APIResponse(status="success", code=200, message=message_200, data=data)
    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)


@router.get(
    "/status-counts",
    response_model=APIResponse,
    description=DESCRIPTION,
)
async def session_status_counts(
    current_user: User = Depends(get_current_user),
    community_id: int | None = Depends(is_commmunity_user),
    session: Session = Depends(get_session),
):
    message_200 = "Fetched Session counts successfully."
    message_500 = "Failed to fetch Session counts "
    try:
        session_counts = session_status_counts_service(
            session=session,
            community_id=community_id,
        )
        return APIResponse(
            status="success", code=200, message=message_200, data=session_counts
        )
    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)


@router.get("/answer-status", response_model=APIResponse, description=DESCRIPTION)
async def get_session_status(session: Session = Depends(get_session)):
    message_200 = "Answer status fetched successfully."
    message_500 = "Failed to fetch Answer status."
    try:
        session_status = get_answer_status_service(session=session)
        data = [
            AnswerStatusOut.model_validate(status).model_dump()
            for status in session_status
        ]
        return APIResponse(status="success", code=200, message=message_200, data=data)
    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)
