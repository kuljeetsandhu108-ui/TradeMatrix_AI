from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests
import models
import jwt
import datetime
import os

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["auth"]
)

# --- SETTINGS ---
SECRET_KEY = "super_secret_high_end_key"
ALGORITHM = "HS256"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID") 

# Define where to look for the token (needed for the dependency)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- LOGIN REQUEST SCHEMA ---
class GoogleLoginRequest(BaseModel):
    token: str

# --- THE SECURITY DEPENDENCY (Moved Here) ---
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Decodes the JWT Token and finds the User.
    Other routers will use this to protect endpoints.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode Token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    # Get User from DB
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise credentials_exception
        
    return user

# --- GOOGLE LOGIN ENDPOINT ---
@router.post("/google")
def google_login(data: GoogleLoginRequest, db: Session = Depends(get_db)):
    print(f"Received Google Token (First 50 chars): {data.token[:50]}...") 

    try:
        # 1. Verify Google Token
        # Increased clock skew to 60s to fix time sync issues
        id_info = id_token.verify_oauth2_token(data.token, requests.Request(), clock_skew_in_seconds=60)

        email = id_info.get("email")
        name = id_info.get("name")
        picture = id_info.get("picture")
        
        if not email:
            raise HTTPException(status_code=400, detail="Google Token valid but no email found")

        # 2. Check/Create User
        user = db.query(models.User).filter(models.User.email == email).first()

        if not user:
            print(f"🆕 Creating New User: {email}")
            user = models.User(
                email=email,
                full_name=name,
                profile_pic=picture,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # 3. Create Session Token (JWT)
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        access_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        return {
            "access_token": access_token,
            "user": {
                "id": user.id,
                "name": user.full_name,
                "email": user.email,
                "picture": user.profile_pic
            }
        }

    except ValueError as e:
        print(f"❌ Google Token Verification Error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid Google Token: {str(e)}")
    except Exception as e:
        print(f"❌ Internal Auth Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")