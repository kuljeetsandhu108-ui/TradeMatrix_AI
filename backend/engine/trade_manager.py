import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
import models
import pandas_ta as ta
from engine.broker_interface import BrokerClient
import traceback
import ccxt # Import CCXT to check version and availability

# Global memory to track running bots
active_bots = {}

class TradeBot:
    def __init__(self, strategy_id: int, db: Session):
        self.strategy_id = strategy_id
        self.db = db
        self.is_active = True
        self.logs = []
        
        # 1. Load Strategy Data
        self.strategy = db.query(models.Strategy).filter(models.Strategy.id == strategy_id).first()
        self.symbol = self.strategy.symbol # e.g., "BTC/USDT"
        
        # 2. Load User's API Keys
        # We look for ANY active broker connection for this user
        self.cred = db.query(models.BrokerCredential).filter(
            models.BrokerCredential.user_id == self.strategy.user_id,
            models.BrokerCredential.is_active == True
        ).first()
        
        self.broker = None
        
        # --- DEBUGGING LOGS (Visible in Frontend Terminal) ---
        # This will help us diagnose the Railway Environment
        self.log(f"🔍 System Check: CCXT Version {ccxt.__version__}")
        
        if self.cred:
            broker_name_clean = self.cred.broker_name.lower().strip()
            
            # Check if this broker actually exists in the library
            if broker_name_clean in ccxt.exchanges:
                self.log(f"✅ Crypto Driver: {broker_name_clean} is AVAILABLE.")
            else:
                self.log(f"❌ Crypto Driver: {broker_name_clean} is MISSING from this version.")
                # Find similar names to help debug
                similar = [e for e in ccxt.exchanges if 'coin' in e or 'delta' in e][:5]
                self.log(f"ℹ️ Did you mean: {similar}?")

            try:
                # Initialize CCXT Connection via BrokerClient wrapper
                self.broker = BrokerClient(
                    broker_name=self.cred.broker_name,
                    api_key=self.cred.client_id, # Stored as client_id
                    secret_key=self.cred.api_key # Stored as api_key
                )
                self.log(f"✅ Connected to {self.cred.broker_name} API successfully")
            except Exception as e:
                self.log(f"❌ Broker Connection Failed: {str(e)}")
        else:
            self.log("⚠️ No Active Broker Keys found. Please configure Broker Config.")

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {self.symbol}: {message}"
        self.logs.append(log_entry)
        # Keep logs manageable
        if len(self.logs) > 100: self.logs.pop(0)
        # Sync with global state
        if self.strategy_id in active_bots:
            active_bots[self.strategy_id]["logs"] = self.logs

    async def run(self):
        self.log(f"🚀 Starting Engine for {self.symbol} ({self.strategy.timeframe})")
        
        while self.is_active:
            try:
                # --- STEP 1: FETCH DATA ---
                current_price = 0
                
                if self.broker:
                    # Get Live Price
                    current_price = self.broker.get_market_price(self.symbol)
                    
                    if not current_price:
                        self.log("⚠️ Failed to fetch price. Retrying...")
                        await asyncio.sleep(5)
                        continue

                    # Get History for Indicators (EMA/RSI)
                    df = self.broker.get_historical_data(self.symbol, self.strategy.timeframe)
                    
                    if df.empty:
                        self.log("⏳ Waiting for historical candles...")
                        await asyncio.sleep(5)
                        continue
                        
                    # --- STEP 2: CALCULATE INDICATORS ---
                    # (Hardcoded Logic Example: EMA Crossover)
                    
                    df['ema_9'] = ta.ema(df['close'], length=9)
                    df['ema_21'] = ta.ema(df['close'], length=21)
                    
                    last_candle = df.iloc[-1]
                    prev_candle = df.iloc[-2]
                    
                    ema_9 = last_candle['ema_9']
                    ema_21 = last_candle['ema_21']
                    prev_ema_9 = prev_candle['ema_9']
                    prev_ema_21 = prev_candle['ema_21']

                    # --- STEP 3: EXECUTE STRATEGY ---
                    
                    # BUY CONDITION: EMA 9 Crosses Above EMA 21
                    if prev_ema_9 <= prev_ema_21 and ema_9 > ema_21:
                        self.log(f"🟢 BUY SIGNAL: EMA9 ({ema_9:.2f}) > EMA21 ({ema_21:.2f})")
                        
                        # EXECUTE TRADE
                        qty = 0.001 if "BTC" in self.symbol else 0.01 
                        
                        order = self.broker.place_order(self.symbol, "buy", qty)
                        if "error" in order:
                            self.log(f"❌ Order Failed: {order['message']}")
                        else:
                            self.log(f"⚡ BUY ORDER EXECUTED! ID: {order.get('id', 'Unknown')}")
                            await asyncio.sleep(10) # Wait to avoid double fire

                    # SELL CONDITION: EMA 9 Crosses Below EMA 21
                    elif prev_ema_9 >= prev_ema_21 and ema_9 < ema_21:
                        self.log(f"🔴 SELL SIGNAL: EMA9 ({ema_9:.2f}) < EMA21 ({ema_21:.2f})")
                        
                        # EXECUTE TRADE
                        qty = 0.001 if "BTC" in self.symbol else 0.01 
                        
                        order = self.broker.place_order(self.symbol, "sell", qty)
                        if "error" in order:
                            self.log(f"❌ Order Failed: {order['message']}")
                        else:
                            self.log(f"⚡ SELL ORDER EXECUTED! ID: {order.get('id', 'Unknown')}")
                            await asyncio.sleep(10)

                    else:
                        # Heartbeat log every 10 seconds
                        if datetime.now().second % 10 == 0:
                            self.log(f"👀 Watching: {current_price} | EMA9: {ema_9:.2f}")

                else:
                    self.log("⚠️ Engine Idle: Connect Broker to trade.")
                    await asyncio.sleep(5)

            except Exception as e:
                self.log(f"🔥 Critical Loop Error: {str(e)}")
                traceback.print_exc()
                await asyncio.sleep(5)

            # High Frequency Loop Speed (e.g., Check every 3 seconds)
            await asyncio.sleep(3)

    def stop(self):
        self.is_active = False
        self.log("🛑 Bot Stopped")

# --- API CONTROL FUNCTIONS ---

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
    
    # Update Status in DB
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
    
    # Update Status in DB
    strat = db.query(models.Strategy).filter(models.Strategy.id == strategy_id).first()
    strat.is_running = False
    db.commit()
    return {"status": "success", "message": "Bot Stopped"}