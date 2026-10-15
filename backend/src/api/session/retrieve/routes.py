from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.common.schemas import APIResponse
from src.api.common.guards import get_current_user
from src.core.database import get_session
from src.core.exceptions import ServiceError
from src.models.user import User

from src.services.session.retrieve import retrieve_session_service
from src.services.session.common.params import SessionRetrieveParams, SessionExpand
from src.api.session.common.out import SessionOut
from . import dependencies, examples
from src.api.user.common.out import UserOut
from src.api.community.common.out import CommunityOut

from src.services.session_participant.list import list_session_participants_service
from src.services.session_participant.common.params import (
    SessionParticipantsListParams,
    SessionParticipantsFilterParams,
    SessionParticipantsPaginationParams,
    SessionParticipantsOrderParams,
    SessionParticipantsExpand,
)
from src.api.session_participiant.common.out import SessionParticipantOut

router = APIRouter(prefix="")

DESCRIPTION = """Endpoint to retrieve session."""


@router.get(
    "/{session_id}",
    response_model=APIResponse,
    description=DESCRIPTION,
)
async def retrieve_session(
    session_id: int,
    params: SessionRetrieveParams = Depends(dependencies.get_session_retrieve_params),
    session: Session = Depends(get_session),
    # ! do not add current user ->  Public
):
    message_200 = "Session retrieved successfully."
    message_500 = "Failed to retrieve the session."

    try:

        session_list = retrieve_session_service(
            session=session,
            session_id=session_id,
            params=params,
        )

        data = SessionOut.model_validate(session_list).model_dump(exclude={"questions"})
        expand_fields = {
            "created_by": ("created_by_user", UserOut),
            "updated_by": ("updated_by_user", UserOut),
            "community": ("community", CommunityOut),
            # "session_question": ("session_question", QuestionBankOut),
        }
        for key, (attr, out_schema) in expand_fields.items():
            if getattr(SessionExpand, key) in params.expand:
                data[key] = (
                    out_schema.model_validate(getattr(session_list, attr)).model_dump()
                    if getattr(session_list, attr)
                    else None
                )

        if SessionExpand.session_question in params.expand:
            questions = []
            for session_question in session_list.session_questions or []:
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
                    }
                )
            data["questions"] = questions

        return APIResponse(status="success", code=200, message=message_200, data=data)

    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)


@router.get(
    "/{session_id}/participants",
    response_model=APIResponse,
    description="List joined participants for a session.",
)
async def list_session_participants(
    session_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    message_200 = "Session participants listed successfully."
    message_500 = "Failed to list session participants."

    try:
        params = SessionParticipantsListParams(
            filter=SessionParticipantsFilterParams(session_id=session_id, user_id=None),
            pagination=SessionParticipantsPaginationParams(limit=None, offset=None),
            order=SessionParticipantsOrderParams(order_by=None),
            expand={SessionParticipantsExpand.user},
        )

        result = list_session_participants_service(
            session=session,
            params=params,
            current_user=current_user,
        )

        items = []
        for participant in result["items"]:
            data = SessionParticipantOut.model_validate(participant).model_dump()
            data["user"] = (
                UserOut.model_validate(participant.user).model_dump()
                if participant.user
                else None
            )
            items.append(data)

        return APIResponse(
            status="success",
            code=200,
            message=message_200,
            data={
                "total_count": result["total_count"],
                "count": result["count"],
                "items": items,
            },
        )
    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)
