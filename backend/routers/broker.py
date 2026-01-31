from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from pydantic import BaseModel
import models
from routers.auth import get_current_user

router = APIRouter(
    prefix="/api/v1/broker",
    tags=["broker"]
)

class BrokerConnectRequest(BaseModel):
    broker_name: str
    api_key: str
    secret_key: str

# 1. CONNECT (Save Keys)
@router.post("/connect")
def connect_broker(
    data: BrokerConnectRequest, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Check existing for THIS SPECIFIC USER
    existing = db.query(models.BrokerCredential).filter(
        models.BrokerCredential.user_id == current_user.id,
        models.BrokerCredential.broker_name == data.broker_name
    ).first()

    if existing:
        existing.client_id = data.api_key
        existing.api_key = data.secret_key
        existing.is_active = True
        db.commit()
        return {"status": "success", "message": f"Updated credentials for {data.broker_name}"}
    
    # Create New
    new_cred = models.BrokerCredential(
        user_id=current_user.id,
        broker_name=data.broker_name,
        client_id=data.api_key,
        api_key=data.secret_key,
        is_active=True
    )
    db.add(new_cred)
    db.commit()
    
    return {"status": "success", "message": f"Connected to {data.broker_name}"}

# 2. GET STATUS
@router.get("/status")
def get_broker_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    creds = db.query(models.BrokerCredential).filter(models.BrokerCredential.user_id == current_user.id).all()
    return [
        {"broker": c.broker_name, "active": c.is_active, "key_preview": c.client_id[:4] + "***"}
        for c in creds
    ]

# 3. DELETE KEYS (New Endpoint)
@router.delete("/{broker_name}")
def delete_broker(
    broker_name: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    cred = db.query(models.BrokerCredential).filter(
        models.BrokerCredential.user_id == current_user.id,
        models.BrokerCredential.broker_name == broker_name
    ).first()

    if not cred:
        raise HTTPException(status_code=404, detail="Broker not found")

    db.delete(cred)
    db.commit()
    
    return {"status": "success", "message": f"Deleted {broker_name} keys"}