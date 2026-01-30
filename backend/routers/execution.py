from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from engine.trade_manager import start_bot, stop_bot, active_bots
import models

router = APIRouter(
    prefix="/api/v1/execution",
    tags=["execution"]
)

@router.post("/start/{strategy_id}")
async def start_strategy(strategy_id: int, db: Session = Depends(get_db)):
    return await start_bot(strategy_id, db)

@router.post("/stop/{strategy_id}")
async def stop_strategy(strategy_id: int, db: Session = Depends(get_db)):
    return await stop_bot(strategy_id, db)

@router.get("/logs/{strategy_id}")
def get_logs(strategy_id: int):
    if strategy_id in active_bots:
        return {"status": "running", "logs": active_bots[strategy_id]["logs"]}
    else:
        return {"status": "stopped", "logs": []}