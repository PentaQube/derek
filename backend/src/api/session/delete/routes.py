from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.common.schemas import APIResponse
from src.api.common.guards import get_current_user
from src.core.database import get_session
from src.core.exceptions import ServiceError
from src.models.user import User
from src.services.session.delete import delete_session_service


router = APIRouter(prefix="")

DESCRIPTION = """Endpoint to delete session."""


@router.delete(
    "/{session_id}",
    response_model=APIResponse,
    description=DESCRIPTION,
)
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    message_200 = "Session deleted successfully."
    message_500 = "Failed to delete the session."

    try:

        delete_session_service(
            session=session,
            session_id=session_id,
        )

        return APIResponse(status="success", code=200, message=message_200)

    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)
