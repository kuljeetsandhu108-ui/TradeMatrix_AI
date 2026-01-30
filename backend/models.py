from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    profile_pic = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    broker_accounts = relationship("BrokerCredential", back_populates="owner")
    strategies = relationship("Strategy", back_populates="owner")

class BrokerCredential(Base):
    __tablename__ = "broker_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    broker_name = Column(String) # "fyres", "angel"
    
    api_key = Column(String, nullable=True)
    client_id = Column(String, nullable=True)
    access_token = Column(String, nullable=True)
    
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="broker_accounts")

# --- THIS WAS MISSING ---
class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Nullable for now
    name = Column(String)
    
    # Stores the logic like: {"rules": [{"indicatorA": "EMA" ...}]}
    logic_configuration = Column(JSON) 
    
    symbol = Column(String)
    timeframe = Column(String)
    is_running = Column(Boolean, default=False)
    
    owner = relationship("User", back_populates="strategies")