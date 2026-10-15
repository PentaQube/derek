from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.common.schemas import APIResponse
from src.api.common.guards import get_current_user
from src.core.database import get_session
from src.core.exceptions import ServiceError
from src.models.user import User
from src.services.session.create import create_session_service
from src.services.session.common.schemas import SessionCreateData

from ..common.out import SessionOut


router = APIRouter(prefix="")

DESCRIPTION = """Endpoint to create session."""


@router.post(
    "/",
    response_model=APIResponse,
    description=DESCRIPTION,
)
async def create_session(
    request_body: SessionCreateData,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    return_data: bool | None = None,
):
    message_200 = "Session created successfully."
    message_500 = "Failed to create the session."

    try:

        result = create_session_service(
            session=session,
            data=request_body,
            current_user=current_user,
        )

        return APIResponse(
            status="success",
            code=200,
            message=message_200,
            data=(
                SessionOut.model_validate(result).model_dump() if return_data else None
            ),
        )

    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)
