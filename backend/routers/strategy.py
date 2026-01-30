from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from typing import List
from routers.auth import get_current_user
router = APIRouter(
    prefix="/api/v1/strategy",
    tags=["strategies"]
)

# 1. CREATE STRATEGY (Protected)
@router.post("/create")
def create_strategy(
    strategy: schemas.StrategyCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # <--- REQUIRES LOGIN
):
    print(f"Creating Strategy for User: {current_user.email}") # Debug
    
    new_strategy = models.Strategy(
        name=strategy.name,
        symbol=strategy.symbol,
        timeframe=strategy.timeframe,
        user_id=current_user.id, # <--- USE REAL ID
        logic_configuration={"rules": [c.dict() for c in strategy.conditions]},
        is_running=False
    )
    
    db.add(new_strategy)
    db.commit()
    db.refresh(new_strategy)
    
    return {"status": "success", "strategy_id": new_strategy.id}

# 2. LIST STRATEGIES (Protected)
@router.get("/list", response_model=List[schemas.StrategyResponse])
def list_strategies(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # <--- REQUIRES LOGIN
):
    # Only fetch strategies belonging to THIS user
    strategies = db.query(models.Strategy).filter(models.Strategy.user_id == current_user.id).all()
    
    results = []
    for s in strategies:
        conditions_data = s.logic_configuration.get("rules", [])
        results.append(schemas.StrategyResponse(
            id=s.id,
            name=s.name,
            symbol=s.symbol,
            timeframe=s.timeframe,
            user_id=s.user_id,
            conditions=conditions_data,
            is_running=s.is_running
        ))
        
    return results