import asyncio
import random
from datetime import datetime
from sqlalchemy.orm import Session
import models

# Global dictionary to keep track of running bots
# Format: { strategy_id: {"status": "running", "task": asyncio_Task, "logs": []} }
active_bots = {}

class TradeBot:
    def __init__(self, strategy_id: int, db: Session):
        self.strategy_id = strategy_id
        self.db = db
        self.is_active = True
        self.logs = []
        
        # Load Strategy Details
        self.strategy = db.query(models.Strategy).filter(models.Strategy.id == strategy_id).first()
        self.symbol = self.strategy.symbol
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {self.symbol}: {message}"
        self.logs.append(log_entry)
        
        # Keep only last 50 logs to save memory
        if len(self.logs) > 50:
            self.logs.pop(0)
            
        # Update global state so API can read it
        if self.strategy_id in active_bots:
            active_bots[self.strategy_id]["logs"] = self.logs

    async def run(self):
        """
        The Main Infinite Loop.
        In a real scenario, this connects to WebSocket.
        Here, we simulate market data.
        """
        self.log(f"🚀 Algorithm Started on {self.symbol}")
        self.log(f"⚙️ Loaded Logic: {len(self.strategy.logic_configuration.get('rules', []))} Conditions")
        
        price = 21450.00 # Starting mock price for NIFTY
        
        while self.is_active:
            # 1. Simulate Price Movement
            change = random.uniform(-10, 10)
            price += change
            
            # 2. Calculate Fake Indicators (Simulation)
            ema_9 = price + random.uniform(-5, 5)
            ema_21 = price + random.uniform(-10, 10)
            
            # 3. Check Logic (Simplified for Demo)
            # In real life, we would use pandas_ta here on real data
            if ema_9 > ema_21 and change > 5:
                self.log(f"✅ SIGNAL DETECTED: EMA(9) {ema_9:.2f} > EMA(21) {ema_21:.2f}")
                self.log(f"⚡ EXECUTING BUY ORDER: {self.symbol} @ {price:.2f}")
                # Here we would call broker_api.place_order()
                await asyncio.sleep(2) # Prevent spamming
                
            elif ema_9 < ema_21 and change < -5:
                self.log(f"🔻 SIGNAL DETECTED: EMA(9) < EMA(21)")
                self.log(f"⚡ EXECUTING SELL ORDER: {self.symbol} @ {price:.2f}")
                await asyncio.sleep(2)
            
            else:
                # Just a heartbeat log every 5 seconds
                if random.random() > 0.8:
                    self.log(f"👀 Monitoring... Price: {price:.2f} | No Signal")

            # Wait 1 second before next tick
            await asyncio.sleep(1)

    def stop(self):
        self.is_active = False
        self.log("🛑 Algorithm Stopped by User")

# --- MANAGER FUNCTIONS ---

async def start_bot(strategy_id: int, db: Session):
    if strategy_id in active_bots:
        return {"status": "error", "message": "Bot already running"}
    
    # Create the bot instance
    bot = TradeBot(strategy_id, db)
    
    # Create an async task to run it in background
    task = asyncio.create_task(bot.run())
    
    # Save to global memory
    active_bots[strategy_id] = {
        "status": "running",
        "task": task,
        "logs": bot.logs,
        "instance": bot
    }
    
    # Update DB status
    strat = db.query(models.Strategy).filter(models.Strategy.id == strategy_id).first()
    strat.is_running = True
    db.commit()
    
    return {"status": "success", "message": "Bot Started"}

async def stop_bot(strategy_id: int, db: Session):
    if strategy_id not in active_bots:
        return {"status": "error", "message": "Bot not active"}
    
    # Stop the loop
    active_bots[strategy_id]["instance"].stop()
    
    # Cancel the async task
    active_bots[strategy_id]["task"].cancel()
    
    # Remove from memory
    del active_bots[strategy_id]
    
    # Update DB status
    strat = db.query(models.Strategy).filter(models.Strategy.id == strategy_id).first()
    strat.is_running = False
    db.commit()
    
    return {"status": "success", "message": "Bot Stopped"}