from typing import Optional, List
from src.core.types import NotEmptyStr
from pydantic import BaseModel, Field
from src.services.user.common.schemas import UserCreateData


class create_community(BaseModel):
    name: NotEmptyStr = Field(..., json_schema_extra={"example": "New Community"})
    user_ids: Optional[list[int]] = Field(
        default=None,
        json_schema_extra={"example": [13, 12, 1]},
    )
