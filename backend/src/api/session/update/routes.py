from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.common.schemas import APIResponse
from src.api.common.guards import get_current_user
from src.core.database import get_session
from src.core.exceptions import ServiceError
from src.models.user import User
from src.services.session.update import (
    update_session_service,
)
from src.services.session.common.schemas import SessionUpdateData
from ..common.out import SessionOut

router = APIRouter(prefix="")

DESCRIPTION = """Endpoint to update session."""


@router.patch(
    "/{session_id}",
    response_model=APIResponse,
    description=DESCRIPTION,
)
async def update_session(
    request_body: SessionUpdateData,
    session_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    return_data: bool | None = None,
):
    message_200 = "Session updated successfully."
    message_500 = "Failed to update the session."

    try:

        update_session = update_session_service(
            session=session,
            session_id=session_id,
            data=request_body,
            current_user=current_user,
        )

        return APIResponse(
            status="success",
            code=200,
            message=message_200,
            data=(
                SessionOut.model_validate(update_session).model_dump()
                if return_data
                else None
            ),
        )

    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)
