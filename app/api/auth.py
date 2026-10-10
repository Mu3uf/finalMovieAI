import os

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from supabase import create_client

from app.services.supabase import supabase
from app.services.auth import get_current_user


router = APIRouter(
    prefix="/api/auth",
    tags=["auth"]
)


# ------------------------------------------------------------
# IMPORTANT: separate client for login / signup
# ------------------------------------------------------------
# The shared `supabase` client is used by the tools to read the
# movies table. If we call sign_in_with_password() on that same
# client, it STORES the user's session and every later query
# (for ALL visitors) starts running as that logged-in user instead
# of the normal server role. RLS then changes what the queries can
# see, and the site stops returning data until the server restarts.
#
# So login/signup use a short-lived client that is thrown away
# after each request. The shared client is never touched.
# ------------------------------------------------------------

def new_auth_client():
    url = getattr(supabase, "supabase_url", None) or os.getenv("SUPABASE_URL")
    key = (
        getattr(supabase, "supabase_key", None)
        or os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
    )

    # supabase_url can be a URL object (not a plain string) in newer
    # versions of the library, and create_client() needs real strings.
    return create_client(str(url), str(key))


# Where the confirmation email link should send the user.
# Set SITE_URL on Render (e.g. https://movieai2.onrender.com).
# Defaults to the old value so nothing changes if it is not set.
SITE_URL = os.getenv("SITE_URL", "http://localhost:8000")


class SignupRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/signup")
def signup(request: SignupRequest):

    try:

        auth_client = new_auth_client()

        result = auth_client.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "email_redirect_to": SITE_URL
            }
        })

        if not result.user:
            raise HTTPException(
                status_code=400,
                detail="Could not create user."
            )

        return {
            "success": True,
            "message": "Account created successfully.",
            "user": {
                "id": result.user.id,
                "email": result.user.email
            }
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post("/login")
def login(request: LoginRequest):

    try:

        auth_client = new_auth_client()

        result = auth_client.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })

        if not result.user or not result.session:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password."
            )

        return {
            "success": True,
            "message": "Login successful.",
            "access_token": result.session.access_token,
            "refresh_token": result.session.refresh_token,
            "user": {
                "id": result.user.id,
                "email": result.user.email
            }
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )


@router.get("/me")
def get_me(
    user=Depends(get_current_user)
):

    return {
        "success": True,
        "user": {
            "id": user.id,
            "email": user.email
        }
    }