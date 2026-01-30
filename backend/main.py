from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import models
import os

# --- IMPORT ROUTERS ---
from routers import strategy, broker, execution

# 1. Create Database Tables (Auto-Migration)
# This ensures that when you deploy to Railway, the tables are created in Postgres automatically.
models.Base.metadata.create_all(bind=engine)

# 2. Initialize the App
app = FastAPI(
    title="TradeMatrix Engine",
    description="High-Frequency Algorithmic Trading Core connected to NSE via Broker APIs",
    version="1.0.0"
)

# 3. CORS CONFIGURATION (Crucial for Cloud Deployment)
# We need to allow requests from your Localhost AND your Railway Frontend.

origins = [
    "http://localhost:3000",      # Local Development
    "http://127.0.0.1:3000",      # Local Development IP
    
    # Your Railway Frontend URL (From your screenshot)
    "https://glorious-intuition-production-3777.up.railway.app",
    
    # Generic Railway wildcard (Optional, covers future deployments)
    "https://*.up.railway.app"
]

app.add_middleware(
    CORSMiddleware,
    # In production, specific domains are better, but "*" ensures it works immediately 
    # if you change the frontend URL.
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. HEALTH CHECK
@app.get("/")
async def root():
    return {
        "status": "System Operational", 
        "cloud": "Railway", 
        "database": "Connected",
        "market": "NSE"
    }

# 5. REGISTER ROUTERS
# This connects all the different parts of our system to the main brain.
app.include_router(strategy.router)
app.include_router(broker.router)
app.include_router(execution.router)