from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from pydantic import BaseModel
import models

router = APIRouter(
    prefix="/api/v1/broker",
    tags=["broker"]
)

class BrokerConnectRequest(BaseModel):
    broker_name: str  # "delta", "coindcx"
    api_key: str
    secret_key: str   # Using 'secret_key' instead of 'client_id' for clarity
    user_id: int

@router.post("/connect")
def connect_broker(data: BrokerConnectRequest, db: Session = Depends(get_db)):
    # 1. Check existing
    existing = db.query(models.BrokerCredential).filter(
        models.BrokerCredential.user_id == data.user_id,
        models.BrokerCredential.broker_name == data.broker_name
    ).first()

    if existing:
        existing.client_id = data.api_key     # Storing API Key in client_id column
        existing.api_key = data.secret_key    # Storing Secret in api_key column
        existing.is_active = True             # Crypto is ALWAYS active (No OTP)
        db.commit()
        return {"status": "success", "message": f"Connected to {data.broker_name}"}
    
    # 2. Create New
    new_cred = models.BrokerCredential(
        user_id=data.user_id,
        broker_name=data.broker_name,
        client_id=data.api_key,
        api_key=data.secret_key,
        is_active=True
    )
    db.add(new_cred)
    db.commit()
    
    return {"status": "success", "message": f"Connected to {data.broker_name}"}

@router.get("/status")
def get_broker_status(user_id: int = 1, db: Session = Depends(get_db)):
    creds = db.query(models.BrokerCredential).filter(models.BrokerCredential.user_id == user_id).all()
    return [
        {"broker": c.broker_name, "active": c.is_active, "key_preview": c.client_id[:4] + "***"}
        for c in creds
    ]