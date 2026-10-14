from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.api.common.guards import is_platform_admin
from src.api.common.schemas import APIResponse
from src.core.database import get_session
from src.core.exceptions import ServiceError

from src.models.community import Community
from src.models.user import User

from src.api.community.common.out import CommunityOut

from src.services.community.common.params import CommunityExpand, CommunityListParams
from src.services.community.list import list_community_service
from . import dependencies


router = APIRouter(prefix="")

DESCRIPTION = """
    Endpoint to list community.
"""


@router.get(
    "/",
    response_model=APIResponse,
    description=DESCRIPTION,
    # responses=(examples.list_community_examples),
)
async def list_community(
    params: CommunityListParams = Depends(dependencies.get_community_list_params),
    current_user: User = Depends(is_platform_admin),
    session: Session = Depends(get_session),
):
    message_200 = "Community listed successfully."
    message_500 = "Community list failed."

    try:
        communities = list_community_service(
            session=session, params=params, current_user=current_user
        )

        validated_items = []
        for community in communities["items"]:
            data = CommunityOut.model_validate(community).model_dump()

            if CommunityExpand.created_by in params.expand:
                data["created_by"] = (
                    CommunityOut.model_validate(community.created_by_user).model_dump()
                    if getattr(community, "created_by_user", None)
                    else None
                )

            if CommunityExpand.updated_by in params.expand:
                data["updated_by"] = (
                    CommunityOut.model_validate(community.updated_by_user).model_dump()
                    if getattr(community, "updated_by_user", None)
                    else None
                )

            validated_items.append(data)

        return APIResponse(
            status="success",
            code=200,
            message=message_200,
            data=dict(
                total_count=communities["total_count"],
                count=communities["count"],
                items=validated_items,
            ),
        )
    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)
