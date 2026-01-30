import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
import models
import pandas_ta as ta
# Import the new Real Broker Interface
from engine.broker_interface import BrokerClient

# Global memory
active_bots = {}

class TradeBot:
    def __init__(self, strategy_id: int, db: Session):
        self.strategy_id = strategy_id
        self.db = db
        self.is_active = True
        self.logs = []
        
        # 1. Load Strategy
        self.strategy = db.query(models.Strategy).filter(models.Strategy.id == strategy_id).first()
        self.symbol = self.strategy.symbol # e.g., "NSE:NIFTY50-INDEX"
        
        # 2. Load User Credentials
        self.cred = db.query(models.BrokerCredential).filter(
            models.BrokerCredential.user_id == self.strategy.user_id,
            models.BrokerCredential.broker_name == "fyres",
            models.BrokerCredential.is_active == True
        ).first()
        
        self.broker = None
        if self.cred:
            # Initialize Real Connection
            self.broker = BrokerClient(self.cred.client_id, self.cred.access_token)
        else:
            self.log("⚠️ No Active Broker Token found! Running in Simulation Mode.")

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {self.symbol}: {message}"
        self.logs.append(log_entry)
        if len(self.logs) > 50: self.logs.pop(0)
        if self.strategy_id in active_bots:
            active_bots[self.strategy_id]["logs"] = self.logs

    async def run(self):
        self.log(f"🚀 Algo Started. Logic: {len(self.strategy.logic_configuration.get('rules', []))} Rules")
        
        while self.is_active:
            current_price = 0
            
            # --- PHASE 1: GET DATA ---
            if self.broker:
                # REAL MODE
                current_price = self.broker.get_market_price(self.symbol)
                
                # Fetch history for indicators
                df = self.broker.get_historical_data(self.symbol, self.strategy.timeframe)
                
                if df.empty:
                    self.log("Waiting for data...")
                    await asyncio.sleep(2)
                    continue
                    
                # Calculate Indicators using pandas_ta
                # Example: Calculating EMA 9 and EMA 21 dynamically
                # (In full version, we parse JSON rules here)
                df['ema_9'] = ta.ema(df['close'], length=9)
                df['ema_21'] = ta.ema(df['close'], length=21)
                
                last_candle = df.iloc[-1]
                ema_9 = last_candle['ema_9']
                ema_21 = last_candle['ema_21']
                
            else:
                # SIMULATION FALLBACK (If no broker connected)
                import random
                current_price = 21450 + random.uniform(-10, 10)
                ema_9 = current_price + random.uniform(-5, 5)
                ema_21 = current_price + random.uniform(-10, 10)

            # --- PHASE 2: EVALUATE LOGIC ---
            # (Simplified for this step - checking Crossover)
            if ema_9 > ema_21:
                self.log(f"✅ BUY SIGNAL: EMA9 ({ema_9:.2f}) > EMA21 ({ema_21:.2f})")
                
                if self.broker:
                    # REAL ORDER
                    res = self.broker.place_order(self.symbol, "BUY")
                    self.log(f"⚡ Order Sent: {res}")
                else:
                    self.log(f"⚡ [SIM] Bought at {current_price:.2f}")
                
                await asyncio.sleep(5) # Wait to avoid duplicate orders

            else:
                # Heartbeat log (Randomly to avoid spam)
                if datetime.now().second % 10 == 0:
                    self.log(f"👀 Price: {current_price} | EMA9: {ema_9:.2f} | EMA21: {ema_21:.2f}")

            # Wait 1 second (High Frequency Loop)
            await asyncio.sleep(1)

    def stop(self):
        self.is_active = False
        self.log("🛑 Bot Stopped")

# ... (Keep the existing start_bot / stop_bot functions as they were) ...
# Just make sure start_bot instantiates the new TradeBot class above.
async def start_bot(strategy_id: int, db: Session):
    if strategy_id in active_bots:
        return {"status": "error", "message": "Bot already running"}
    
    bot = TradeBot(strategy_id, db)
    task = asyncio.create_task(bot.run())
    
    active_bots[strategy_id] = {
        "status": "running",
        "task": task,
        "logs": bot.logs,
        "instance": bot
    }
    
    strat = db.query(models.Strategy).filter(models.Strategy.id == strategy_id).first()
    strat.is_running = True
    db.commit()
    return {"status": "success", "message": "Bot Started"}

async def stop_bot(strategy_id: int, db: Session):
    if strategy_id not in active_bots:
        return {"status": "error", "message": "Bot not active"}
    active_bots[strategy_id]["instance"].stop()
    active_bots[strategy_id]["task"].cancel()
    del active_bots[strategy_id]
    strat = db.query(models.Strategy).filter(models.Strategy.id == strategy_id).first()
    strat.is_running = False
    db.commit()
    return {"status": "success", "message": "Bot Stopped"}