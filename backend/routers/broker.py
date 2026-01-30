from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
from pydantic import BaseModel
import models
import requests # Used for the real token exchange
import datetime

router = APIRouter(
    prefix="/api/v1/broker",
    tags=["broker"]
)

# --- SCHEMAS ---
class BrokerConnectRequest(BaseModel):
    broker_name: str  # "fyres" or "angel"
    client_id: str    # App ID
    api_key: str      # Secret Key (We store this to generate tokens later)
    user_id: int = 1  # Default to 1 for now

# --- ENDPOINTS ---

# 1. SAVE STATIC KEYS (Step 1: Setup)
@router.post("/connect")
def connect_broker(data: BrokerConnectRequest, db: Session = Depends(get_db)):
    """
    Saves the App ID and App Secret. 
    Does NOT generate the Access Token yet (that happens in the morning login).
    """
    # Check if user already has this broker entry
    existing = db.query(models.BrokerCredential).filter(
        models.BrokerCredential.user_id == data.user_id,
        models.BrokerCredential.broker_name == data.broker_name
    ).first()

    if existing:
        # Update existing keys
        existing.client_id = data.client_id
        existing.api_key = data.api_key # Storing Secret Key here
        existing.is_active = False # Reset active status until they login
        db.commit()
        return {"status": "success", "message": f"Updated credentials for {data.broker_name}"}
    
    # Create new entry
    new_cred = models.BrokerCredential(
        user_id=data.user_id,
        broker_name=data.broker_name,
        client_id=data.client_id,
        api_key=data.api_key,
        is_active=False # Not active yet
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
            "id": c.client_id,
            "last_login": c.updated_at if hasattr(c, 'updated_at') else "N/A"
        }
        for c in creds
    ]


# 3. GENERATE LOGIN URL (Step 2: Morning Ritual)
@router.get("/fyres/login-url")
def get_fyres_login_url(user_id: int = 1, db: Session = Depends(get_db)):
    """
    Constructs the official Fyres Login URL.
    The redirect_uri points back to OUR server, not the frontend.
    """
    cred = db.query(models.BrokerCredential).filter(
        models.BrokerCredential.user_id == user_id,
        models.BrokerCredential.broker_name == "fyres"
    ).first()
    
    if not cred or not cred.client_id:
        raise HTTPException(status_code=400, detail="Please save App ID & Secret first in Broker Config")

    # The Callback URL where Fyres will send the Auth Code
    # This must be whitelisted in your Fyres App Dashboard
    redirect_uri = "http://localhost:8000/api/v1/broker/fyres/callback"
    
    # Generate the OAuth Link
    # state=user_id allows us to know WHICH user is logging in when the callback returns
    url = f"https://api.fyres.in/auth?type=code&client_id={cred.client_id}&redirect_uri={redirect_uri}&response_type=code&state={user_id}"
    
    return {"login_url": url}


# 4. THE CALLBACK (Step 3: Server-Side Token Generation)
@router.get("/fyres/callback")
def fyres_callback(auth_code: str = None, code: str = None, state: str = None, db: Session = Depends(get_db)):
    """
    This is hit by Fyres Servers after the user enters OTP.
    It runs on YOUR SERVER IP, resolving the 'IP Mismatch' issue.
    """
    # Fyres might send 'code' or 'auth_code'
    final_code = code or auth_code
    
    if not final_code:
        return {"error": "No Auth Code received from Broker"}
    
    if not state:
        return {"error": "State (User ID) missing"}

    user_id = int(state)

    # Fetch User's Keys from DB
    cred = db.query(models.BrokerCredential).filter(
        models.BrokerCredential.user_id == user_id,
        models.BrokerCredential.broker_name == "fyres"
    ).first()

    if not cred:
        return {"error": "Broker credentials not found for this user"}

    # --- THE SERVER-SIDE TOKEN GENERATION ---
    # Here the server talks to Fyres to exchange the Code for the Token.
    
    try:
        # REAL WORLD IMPLEMENTATION (Uncomment when you have Real App ID):
        """
        import hashlib
        app_id = cred.client_id
        secret_key = cred.api_key
        
        # Fyres requires AppIdHash = SHA256(appId + ":" + secretKey)
        app_id_hash = hashlib.sha256(f"{app_id}:{secret_key}".encode()).hexdigest()

        payload = {
            "grant_type": "authorization_code",
            "appIdHash": app_id_hash,
            "code": final_code,
        }

        response = requests.post("https://api.fyres.in/api/v2/validate-authcode", json=payload)
        data = response.json()
        
        if response.status_code == 200 and "access_token" in data:
            access_token = data["access_token"]
        else:
            return {"error": "Failed to generate token from Fyres", "details": data}
        """

        # --- SIMULATION (For Local Testing without breaking Fyres) ---
        # We simulate that the server successfully exchanged the token
        access_token = f"ey_SERVER_GENERATED_TOKEN_{final_code[:10]}_VALID_FOR_TODAY"
        print(f"✅ Generated Access Token for User {user_id} on Server IP")

        # Save to Database
        cred.access_token = access_token
        cred.is_active = True
        # cred.updated_at = datetime.datetime.now() # If you have this column
        db.commit()

        # Redirect user back to the WebApp Dashboard
        return RedirectResponse(url="http://localhost:3000/dashboard?status=connected")

    except Exception as e:
        print(f"Error in callback: {e}")
        return {"error": "Internal Server Error during Token Generation"}