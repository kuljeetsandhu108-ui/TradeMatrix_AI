from pydantic import BaseModel
from typing import List, Optional, Any

# This defines one single condition row (e.g. EMA 9 > EMA 21)
class Condition(BaseModel):
    id: int
    indicatorA: str
    paramA: str
    operator: str
    indicatorB: str
    paramB: str

# This defines the full package sent from the Frontend
class StrategyCreate(BaseModel):
    name: str          # "Ayush 1"
    symbol: str        # "NIFTY 50"
    timeframe: str     # "5m"
    conditions: List[Condition] # The list of rules
    user_id: Optional[int] = 1  # We will use User 1 for now (Hardcoded until Login is ready)

# ... (Keep existing classes) ...

# Add this NEW class at the bottom
class StrategyResponse(StrategyCreate):
    id: int
    is_running: bool