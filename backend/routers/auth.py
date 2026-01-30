from fastapi import APIRouter, Depends, HTTPException
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

# SETTINGS
SECRET_KEY = "super_secret_high_end_key"
ALGORITHM = "HS256"
# You can optionally enforce the Client ID check on backend too
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID") 

class GoogleLoginRequest(BaseModel):
    token: str

@router.post("/google")
def google_login(data: GoogleLoginRequest, db: Session = Depends(get_db)):
    print(f"Received Google Token (First 50 chars): {data.token[:50]}...") # Debug Log

    try:
        # 1. Verify the Token with Google
        id_info = id_token.verify_oauth2_token(data.token, requests.Request(), clock_skew_in_seconds=60)


        # 2. Extract Info
        email = id_info.get("email")
        name = id_info.get("name")
        picture = id_info.get("picture")
        
        print(f"✅ Google Verified: {email}") # Debug Log

        if not email:
            raise HTTPException(status_code=400, detail="Google Token valid but no email found")

        # 3. Check/Create User in Database
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
        else:
            print(f"👋 Welcome back User ID: {user.id}")
        
        # 4. Create Session Token (JWT)
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
        # This prints the EXACT reason Google rejected it to your Terminal
        print(f"❌ Google Token Verification Error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid Google Token: {str(e)}")
    except Exception as e:
        print(f"❌ Internal Auth Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")