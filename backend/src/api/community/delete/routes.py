from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.api.common.guards import is_platform_admin
from src.api.common.schemas import APIResponse
from src.core.database import get_session
from src.core.exceptions import ServiceError
from src.models.user import User
from src.services.community.delete import delete_community_service


router = APIRouter(prefix="")

DESCRIPTION = """
    Endpoint to delete community.
"""


@router.delete(
    "/{community_id}",
    response_model=APIResponse,
    description=DESCRIPTION,
    # responses=examples.delete_community_examples,
)
async def delete_community(
    community_id: int,
    current_user: User = Depends(is_platform_admin),
    session: Session = Depends(get_session),
):
    try:
        delete_community_service(
            session=session, community_id=community_id, current_user=current_user
        )
        return APIResponse(
            status="success", code=200, message="Community deleted successfully."
        )
    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Community delete failed")
