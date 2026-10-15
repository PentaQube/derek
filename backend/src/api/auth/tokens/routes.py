from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.orm import Session
from src.api.common.schemas import APIResponse
from src.core.config import settings
from src.core.database import get_session
from src.core.exceptions import ServiceError
from src.services.auth.tokens import authenticate_service, refresh_service

from . import examples, out

router = APIRouter(prefix="/tokens")


AUTHENTICATE_DESCRIPTION = """
    Endpoint to authenticate a user.
    The endpoint returns an access token and a refresh token.
"""
REFRESH_DESCRIPTION = """
    Endpoint to re-authenticate a user.
    The endpoint returns a new access token.
"""


@router.post(
    "",
    response_model=APIResponse,
    description=AUTHENTICATE_DESCRIPTION,
    responses=examples.authenticate_examples,
)
# @limiter.limit("10/minute", key_func=ip_username_key)
async def authenticate(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    message_200 = "User authenticated successfully."
    message_500 = "Failed to authenticate user."

    # # Store username in request.state
    # # for use by custom key_func ip_username_key
    # request.state.username = form_data.username.lower()

    try:
        access_token, refresh_token = authenticate_service(
            session=session,
            email=form_data.username.lower(),
            provided_password=form_data.password,
        )

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True if settings.env != "dev" else False,
            samesite="strict" if settings.env != "dev" else None,
            max_age=settings.refresh_token_expire_seconds,
        )

        return APIResponse(
            status="success",
            code=200,
            message=message_200,
            data=out.AccessTokenOut(access_token=access_token),
        )
    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)


@router.post(
    "/refresh",
    response_model=APIResponse,
    description=REFRESH_DESCRIPTION,
    responses=examples.refresh_examples,
)
async def refresh(request: Request, session: Session = Depends(get_session)):
    message_200 = "New access token provisioned successfully."
    message_401 = "Invalid or missing refresh token."
    message_500 = "Failed to provision a new access token."

    try:
        # ✅ Extract refresh_token from cookie
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise HTTPException(
                status_code=401,
                detail=message_401,
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = refresh_service(session=session, refresh_token=refresh_token)

        return APIResponse(
            status="success",
            code=200,
            message=message_200,
            data=out.AccessTokenOut(access_token=access_token),
        )
    except JWTError:
        raise HTTPException(
            status_code=401, detail=message_401, headers={"WWW-Authenticate": "Bearer"}
        )
    except ServiceError:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail=message_500)
