from fastapi import FastAPI, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
from supabase import create_client, Client
import os

# Load environment variables
load_dotenv()

# Create FastAPI application
app = FastAPI()

# Bearer authentication for Swagger
security = HTTPBearer(auto_error=False)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Create Supabase client
supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# --------------------------------------------------
# REQUEST MODEL
# --------------------------------------------------

class AuthRequest(BaseModel):
    email: str
    password: str


# --------------------------------------------------
# BASIC ROUTES
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "FlyRank A4 Auth API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# --------------------------------------------------
# STAGE 1 — SIGNUP
# --------------------------------------------------

@app.post("/auth/signup", status_code=201)
def signup(data: AuthRequest):

    if not data.email or not data.password:
        raise HTTPException(
            status_code=400,
            detail="Email and password are required"
        )

    try:
        response = supabase.auth.sign_up({
            "email": data.email,
            "password": data.password
        })

        return {
            "message": "User registered successfully",
            "user": response.user
        }

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Signup failed"
        )


# --------------------------------------------------
# STAGE 1 — LOGIN
# --------------------------------------------------

@app.post("/auth/login")
def login(data: AuthRequest):

    if not data.email or not data.password:
        raise HTTPException(
            status_code=400,
            detail="Email and password are required"
        )

    try:
        response = supabase.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password
        })

        return {
            "message": "Login successful",
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token
        }

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid login credentials"
        )


# --------------------------------------------------
# STAGE 2 — PUBLIC ROUTE
# --------------------------------------------------

@app.get("/public/info")
def public_info():

    return {
        "message": "Welcome stranger! This info is public."
    }


# --------------------------------------------------
# STAGE 4 — REUSABLE AUTH DEPENDENCY
# --------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(security)
):
    """
    Reusable authentication dependency.

    Extracts the Bearer token and asks Supabase
    to verify it.
    """

    # No token supplied
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Access token required"
        )

    token = credentials.credentials

    try:
        response = supabase.auth.get_user(token)

        if not response.user:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )

        return response.user

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )


# --------------------------------------------------
# STAGE 4 — PROTECTED PROFILE
# --------------------------------------------------

@app.get("/protected/profile")
def protected_profile(current_user=Security(get_current_user)):

    return {
        "id": current_user.id,
        "email": current_user.email,
        "created_at": current_user.created_at
    }


# --------------------------------------------------
# STAGE 4 — SECOND PROTECTED ROUTE
# --------------------------------------------------

@app.get("/protected/dashboard")
def protected_dashboard(current_user=Security(get_current_user)):

    return {
        "message": "Welcome to your protected dashboard",
        "user_id": current_user.id,
        "email": current_user.email
    }


# --------------------------------------------------
# STAGE 4 — LOGOUT
# --------------------------------------------------

@app.post("/auth/logout", status_code=204)
def logout(current_user=Security(get_current_user)):

    try:
        supabase.auth.sign_out()

        return None

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Logout failed"
        )