from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from typing import List
from routers.auth import get_current_user # Secure Auth Dependency

router = APIRouter(
    prefix="/api/v1/strategy",
    tags=["strategies"]
)

# 1. CREATE STRATEGY (Now saves Quantity)
@router.post("/create")
def create_strategy(
    strategy: schemas.StrategyCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    print(f"Creating Strategy: {strategy.name} | Qty: {strategy.quantity} | User: {current_user.email}") 
    
    # Pack the Rules AND Quantity into the JSON configuration
    # This allows us to add more settings later (like Stop Loss) without changing the DB table
    logic_config = {
        "rules": [c.dict() for c in strategy.conditions],
        "quantity": strategy.quantity  # <--- CRITICAL UPDATE: SAVING QUANTITY
    }

    new_strategy = models.Strategy(
        name=strategy.name,
        symbol=strategy.symbol,
        timeframe=strategy.timeframe,
        user_id=current_user.id, # Link to the logged-in user
        logic_configuration=logic_config, 
        is_running=False
    )
    
    db.add(new_strategy)
    db.commit()
    db.refresh(new_strategy)
    
    return {"status": "success", "strategy_id": new_strategy.id, "message": "Strategy Created Successfully"}

# 2. LIST STRATEGIES (Now returns Quantity)
@router.get("/list", response_model=List[schemas.StrategyResponse])
def list_strategies(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Only fetch strategies belonging to THIS user
    strategies = db.query(models.Strategy).filter(models.Strategy.user_id == current_user.id).all()
    
    results = []
    for s in strategies:
        # Extract data from the JSON blob
        # Handle cases where logic_configuration might be None or empty
        config = s.logic_configuration if s.logic_configuration else {}
        
        conditions_data = config.get("rules", [])
        saved_quantity = config.get("quantity", 0.001) # Default to 0.001 if missing
        
        results.append(schemas.StrategyResponse(
            id=s.id,
            name=s.name,
            symbol=s.symbol,
            timeframe=s.timeframe,
            user_id=s.user_id,
            conditions=conditions_data,
            quantity=float(saved_quantity), # <--- SEND BACK TO FRONTEND
            is_running=s.is_running
        ))
        
    return results