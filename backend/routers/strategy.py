from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

# Define the URL prefix here
router = APIRouter(
    prefix="/api/v1/strategy",
    tags=["strategies"]
)

# The full URL becomes: /api/v1/strategy/create
@router.post("/create")
def create_strategy(strategy: schemas.StrategyCreate, db: Session = Depends(get_db)):
    print(f"Received Strategy: {strategy.name}") # Debug print
    
    try:
        # 1. Create the database object
        new_strategy = models.Strategy(
            name=strategy.name,
            symbol=strategy.symbol,
            timeframe=strategy.timeframe,
            user_id=strategy.user_id,
            # Convert the list of conditions to a JSON-compatible format
            logic_configuration={"rules": [c.dict() for c in strategy.conditions]},
            is_running=False
        )
        
        # 2. Add to the Vault (Database)
        db.add(new_strategy)
        db.commit()
        db.refresh(new_strategy)
        
        return {"status": "success", "strategy_id": new_strategy.id, "message": "Strategy Deployed"}
        
    except Exception as e:
        print(f"Error saving strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from typing import List

# ... (Keep existing imports and the create_strategy function) ...

# Add this NEW endpoint below create_strategy
# Change the response_model to use StrategyResponse
@router.get("/list", response_model=List[schemas.StrategyResponse]) 
def list_strategies(user_id: int = 1, db: Session = Depends(get_db)):
    strategies = db.query(models.Strategy).filter(models.Strategy.user_id == user_id).all()
    
    results = []
    for s in strategies:
        conditions_data = s.logic_configuration.get("rules", [])
        
        # We now use StrategyResponse which includes ID and is_running
        results.append(schemas.StrategyResponse(
            id=s.id,                  # <--- PASSING ID HERE
            name=s.name,
            symbol=s.symbol,
            timeframe=s.timeframe,
            user_id=s.user_id,
            conditions=conditions_data,
            is_running=s.is_running   # <--- PASSING STATUS HERE
        ))
        
    return results