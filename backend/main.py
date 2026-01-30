from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import models

# --- IMPORT ROUTERS ---
from routers import strategy, broker, execution

# 1. Initialize Database Tables
# This creates the tables in your Railway PostgreSQL automatically
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TradeMatrix Engine",
    description="High-Frequency Algo Trading Backend",
    version="1.0.0"
)

# 2. CORS CONFIGURATION (Crucial Fix)
# We set allow_origins to ["*"] to allow connections from ANY frontend domain.
# This fixes the "Deployment Failed" error caused by domain mismatches on Railway.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "status": "System Operational", 
        "market": "NSE", 
        "mode": "Live-Cloud"
    }

# 3. REGISTER ROUTERS
# This connects all your logic modules to the main app
app.include_router(strategy.router)
app.include_router(broker.router)
app.include_router(execution.router)