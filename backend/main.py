from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, SessionLocal
import models
import requests # <--- Crucial for IP check

# --- IMPORT ROUTERS ---
from routers import strategy, broker, execution, auth

# 1. Initialize Database Tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TradeMatrix Engine",
    description="High-Frequency Algo Trading Backend",
    version="1.0.0"
)

# 2. CORS CONFIGURATION
# Allow all origins to prevent connection errors on Railway
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. AUTO-CREATE TEST USER
# This prevents "Internal Server Error" when running on a fresh cloud database
def create_default_user():
    db = SessionLocal()
    try:
        # Check if User 1 exists
        user = db.query(models.User).filter(models.User.id == 1).first()
        if not user:
            print("⚠️ User 1 not found. Creating Default Admin User...")
            default_user = models.User(
                email="admin@tradematrix.com",
                full_name="Admin Trader",
                is_active=True
            )
            db.add(default_user)
            db.commit()
            print("✅ Default User Created.")
    except Exception as e:
        print(f"Error creating default user: {e}")
    finally:
        db.close()

# Run this on startup
create_default_user()

# 4. BASIC ROUTES
@app.get("/")
async def root():
    return {
        "status": "System Operational", 
        "market": "Crypto/NSE", 
        "mode": "Live-Cloud"
    }

# --- NEW: SERVER IP CHECKER ---
# Use this to find the IP to whitelist on Delta Exchange
@app.get("/server-ip")
def get_server_ip():
    try:
        # Ask external service for our public IP
        ip = requests.get("https://api.ipify.org").text
        return {"ip": ip, "message": "Copy this IP and paste it into Delta Exchange Whitelist"}
    except Exception as e:
        return {"error": str(e)}

# 5. REGISTER ROUTERS
app.include_router(strategy.router)
app.include_router(broker.router)
app.include_router(execution.router)
app.include_router(auth.router)