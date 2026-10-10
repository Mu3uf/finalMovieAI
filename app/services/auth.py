from fastapi import Header, HTTPException
from app.services.supabase import supabase


def get_current_user(
    authorization: str = Header(default=None)
):
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is required."
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header."
        )

    access_token = authorization.replace(
        "Bearer ",
        "",
        1
    ).strip()

    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Access token is missing."
        )

    try:

        response = supabase.auth.get_user(access_token)

        if not response or not response.user:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired access token."
            )

        return response.user

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token."
        )