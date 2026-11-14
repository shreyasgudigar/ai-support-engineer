from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from argon2.exceptions import HashingError

from app.auth.security import hash_password, verify_password, create_access_token
from app.db import get_user_by_email, create_user
from app.auth.dependencies import get_current_user

from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm


router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    customer_id: int = Field(gt=0)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest):

    existing_user = get_user_by_email(str(request.email))

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists",
        )

    password_hash = hash_password(request.password)

    try:
        user = create_user(
            email=str(request.email),
            password_hash=password_hash,
            customer_id=request.customer_id,
        )
    except Exception as exc:
        print("REGISTRATION DATABASE ERROR:", repr(exc))
        raise HTTPException(
            status_code=400,
            detail="Account registration failed. Check the server terminal.",
        ) from exc

    return {
        "message": "Account created successfully",
        "user": user,
    }



@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    print("LOGIN STEP 1: Request received", flush=True)

    email = form_data.username

    print("LOGIN STEP 2: Looking up user", flush=True)
    user = get_user_by_email(email)

    print("LOGIN STEP 3: User lookup completed", flush=True)

    if user is None or not user["is_active"]:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    print("LOGIN STEP 4: Verifying password", flush=True)

    if not verify_password(
        form_data.password,
        user["password_hash"],
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    print("LOGIN STEP 5: Password verified", flush=True)

    access_token = create_access_token(
        user_id=user["id"],
        role=user["role"],
    )

    print("LOGIN STEP 6: Token created", flush=True)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "role": user["role"],
            "customer_id": user["customer_id"],
        },
    }


@router.get("/me")
def get_my_account(current_user=Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "role": current_user["role"],
        "customer_id": current_user["customer_id"],
    }