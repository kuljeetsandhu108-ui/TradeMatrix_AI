from pydantic import BaseModel
from typing import List, Optional, Any

# --- SHARED MODELS ---

class Condition(BaseModel):
    id: int
    indicatorA: str
    paramA: str
    operator: str
    indicatorB: str
    paramB: str

# --- INPUT MODELS (Data coming FROM Frontend) ---

class StrategyCreate(BaseModel):
    name: str
    symbol: str
    timeframe: str
    conditions: List[Condition]
    # NEW: The Trade Quantity (e.g. 0.001 for BTC, 10 for XRP)
    quantity: float = 0.001 
    user_id: Optional[int] = None # Optional because we get it from the Token now

class BrokerConnectRequest(BaseModel):
    broker_name: str
    client_id: str
    api_key: str
    user_id: int = 1 # Legacy support, will be overwritten by Token ID

class GoogleLoginRequest(BaseModel):
    token: str

# --- OUTPUT MODELS (Data sent TO Frontend) ---

class StrategyResponse(StrategyCreate):
    id: int
    is_running: bool
    # We explicitly include quantity here to ensure it's sent back
    quantity: float