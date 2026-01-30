from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import models
from routers import strategy, broker # <--- IMPORT BROKER
from routers import strategy, broker, execution

# --- IMPORT THE ROUTER ---
from routers import strategy 

# Create Database Tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TradeMatrix Engine",
    version="1.0.0"
)

# CORS Setup - Allowing Frontend Access
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "System Operational"}

# --- REGISTER THE ROUTER HERE ---
# This line fixes the 404 error
app.include_router(strategy.router)
app.include_router(broker.router) # <--- ADD THIS LINE
app.include_router(execution.router)