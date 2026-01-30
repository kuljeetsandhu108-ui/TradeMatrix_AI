from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
from pydantic import BaseModel
import models
import requests
import os
import hashlib
import datetime

router = APIRouter(
    prefix="/api/v1/broker",
    tags=["broker"]
)

# --- HELPER: DYNAMIC URL DETECTION ---
def get_callback_url():
    """
    Detects if we are on Railway or Localhost to set the correct Redirect URI.
    """
    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
    
    if railway_domain:
        # PRODUCTION (Railway)
        return f"https://{railway_domain}/api/v1/broker/fyres/callback"
    else:
        # DEVELOPMENT (Localhost)
        return "http://localhost:8000/api/v1/broker/fyres/callback"

# --- SCHEMAS ---
class BrokerConnectRequest(BaseModel):
    broker_name: str  # "fyres"
    client_id: str    # App ID
    api_key: str      # Secret Key (Stored to generate tokens later)
    user_id: int = 1  

# --- ENDPOINTS ---

# 1. SAVE STATIC KEYS (Step 1: Setup)
@router.post("/connect")
def connect_broker(data: BrokerConnectRequest, db: Session = Depends(get_db)):
    # Check if user already has this broker entry
    existing = db.query(models.BrokerCredential).filter(
        models.BrokerCredential.user_id == data.user_id,
        models.BrokerCredential.broker_name == data.broker_name
    ).first()

    if existing:
        existing.client_id = data.client_id
        existing.api_key = data.api_key # Storing Secret Key
        existing.is_active = False      # Reset active status until Login
        db.commit()
        return {"status": "success", "message": f"Updated credentials for {data.broker_name}"}
    
    new_cred = models.BrokerCredential(
        user_id=data.user_id,
        broker_name=data.broker_name,
        client_id=data.client_id,
        api_key=data.api_key,
        is_active=False
    )
    db.add(new_cred)
    db.commit()
    
    return {"status": "success", "message": f"Saved keys for {data.broker_name}. Please perform Morning Login."}


# 2. CHECK STATUS
@router.get("/status")
def get_broker_status(user_id: int = 1, db: Session = Depends(get_db)):
    creds = db.query(models.BrokerCredential).filter(models.BrokerCredential.user_id == user_id).all()
    return [
        {
            "broker": c.broker_name, 
            "active": c.is_active, 
            "id": c.client_id
        }
        for c in creds
    ]


# 3. GENERATE LOGIN URL (Step 2: User clicks 'Login with Fyres')
@router.get("/fyres/login-url")
def get_fyres_login_url(user_id: int = 1, db: Session = Depends(get_db)):
    cred = db.query(models.BrokerCredential).filter(
        models.BrokerCredential.user_id == user_id,
        models.BrokerCredential.broker_name == "fyres"
    ).first()
    
    if not cred or not cred.client_id:
        raise HTTPException(status_code=400, detail="Please save App ID & Secret first")

    # This URL points back to YOUR Server (Railway)
    redirect_uri = get_callback_url()
    
    # We pass user_id as 'state' to identify who is logging in
    url = f"https://api.fyres.in/auth?type=code&client_id={cred.client_id}&redirect_uri={redirect_uri}&response_type=code&state={user_id}"
    
    return {"login_url": url}


# 4. THE CALLBACK (Step 3: SERVER-SIDE TOKEN GENERATION)
# This is the most important part. It runs on the Railway Server IP.
@router.get("/fyres/callback")
def fyres_callback(auth_code: str = None, code: str = None, state: str = None, db: Session = Depends(get_db)):
    
    # Fyres sends the auth code here
    final_code = code or auth_code
    
    if not final_code:
        return {"error": "No Auth Code received from Broker"}
    
    if not state:
        return {"error": "State (User ID) missing"}

    user_id = int(state)

    # 1. Get User Keys from Database
    cred = db.query(models.BrokerCredential).filter(
        models.BrokerCredential.user_id == user_id,
        models.BrokerCredential.broker_name == "fyres"
    ).first()

    if not cred:
        return {"error": "Broker credentials not found for this user"}

    try:
        # 2. Prepare the Hash for Fyres API
        # Requirement: SHA256(appId + ":" + appSecret)
        app_id = cred.client_id
        secret_key = cred.api_key 
        
        app_id_hash = hashlib.sha256(f"{app_id}:{secret_key}".encode()).hexdigest()

        payload = {
            "grant_type": "authorization_code",
            "appIdHash": app_id_hash,
            "code": final_code,
        }

        # 3. SERVER TALKS TO FYRES (This request comes from Railway IP)
        print("⚡ Exchanging Auth Code for Token on Server IP...")
        response = requests.post("https://api.fyres.in/api/v2/validate-authcode", json=payload)
        data = response.json()
        
        # 4. Check if Success
        if response.status_code == 200 and "access_token" in data:
            access_token = data["access_token"]
            print("✅ Token Generated Successfully on Server!")
            
            # 5. Save Token to Database
            cred.access_token = access_token
            cred.is_active = True
            db.commit()

            # 6. Redirect User to Dashboard
            # Determine Frontend URL dynamically
            frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
            # If FRONTEND_URL is not set in env, we try to guess based on referer or default
            
            return RedirectResponse(url=f"{frontend_url}/dashboard?status=connected")
        
        else:
            print(f"❌ Fyres Error: {data}")
            return {"error": "Failed to generate token", "details": data}

    except Exception as e:
        print(f"❌ Internal Server Error: {e}")
        return {"error": f"Internal Server Error: {str(e)}"}