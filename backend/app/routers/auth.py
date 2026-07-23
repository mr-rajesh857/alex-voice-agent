from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import httpx

from app.core.config import settings
from app.db.session import get_db
from app.db.models import User
from app.schemas.auth import UserCreate, UserLogin, UserResponse, Token
from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token
from app.mcp_client.client import set_google_oauth_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    user_id_str = decode_access_token(token)
    if user_id_str is None:
        raise credentials_exception
    
    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise credentials_exception
        
    stmt = select(User).where(User.id == user_uuid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
        
    return user


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == user_in.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    
    new_user = User(
        name=user_in.name,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password)
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    access_token = create_access_token(subject=str(new_user.id))
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user)
    )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == credentials.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(subject=str(user.id))
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.get("/google/callback")
async def google_oauth_callback(
    code: str = Query(..., description="Authorization code from Google"),
    db: AsyncSession = Depends(get_db)
):
    """
    Exchanges authorization code for Google Access Token and tests Gmail Profile.
    """
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
    }

    async with httpx.AsyncClient() as client:
        # 1. Exchange code for tokens
        token_resp = await client.post(token_url, data=data)
        if token_resp.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Google OAuth token exchange failed: {token_resp.text}"
            )
        
        token_json = token_resp.json()
        google_access_token = token_json.get("access_token")

        # Save token globally for real Google API tool execution
        if google_access_token:
            set_google_oauth_token(google_access_token, token_json.get("refresh_token"))

        # 2. Test Gmail API profile using the access token
        gmail_resp = await client.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/profile",
            headers={"Authorization": f"Bearer {google_access_token}"}
        )

        gmail_data = gmail_resp.json() if gmail_resp.status_code == 200 else {"error": gmail_resp.text}

        return {
            "status": "success",
            "message": "Google OAuth authentication successful!",
            "google_access_token": google_access_token,
            "token_type": token_json.get("token_type"),
            "expires_in": token_json.get("expires_in"),
            "scopes_granted": token_json.get("scope"),
            "gmail_profile_test": gmail_data
        }
