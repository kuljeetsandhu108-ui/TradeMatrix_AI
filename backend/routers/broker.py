from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from pydantic import BaseModel
import models
from routers.auth import get_current_user # <--- IMPORT AUTH DEPENDENCY

router = APIRouter(
    prefix="/api/v1/broker",
    tags=["broker"]
)

class BrokerConnectRequest(BaseModel):
    broker_name: str  # "delta", "coindcx"
    api_key: str
    secret_key: str
    # user_id is removed from here because we get it from the Token now

@router.post("/connect")
def connect_broker(
    data: BrokerConnectRequest, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # <--- GET REAL USER
):
    # 1. Check existing for THIS SPECIFIC USER
    existing = db.query(models.BrokerCredential).filter(
        models.BrokerCredential.user_id == current_user.id, # <--- USE REAL ID
        models.BrokerCredential.broker_name == data.broker_name
    ).first()

    if existing:
        existing.client_id = data.api_key
        existing.api_key = data.secret_key
        existing.is_active = True
        db.commit()
        return {"status": "success", "message": f"Updated credentials for {data.broker_name}"}
    
    # 2. Create New
    new_cred = models.BrokerCredential(
        user_id=current_user.id, # <--- USE REAL ID
        broker_name=data.broker_name,
        client_id=data.api_key,
        api_key=data.secret_key,
        is_active=True
    )
    db.add(new_cred)
    db.commit()
    
    return {"status": "success", "message": f"Connected to {data.broker_name}"}

@router.get("/status")
def get_broker_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # <--- GET REAL USER
):
    creds = db.query(models.BrokerCredential).filter(models.BrokerCredential.user_id == current_user.id).all()
    return [
        {"broker": c.broker_name, "active": c.is_active, "key_preview": c.client_id[:4] + "***"}
        for c in creds
    ]