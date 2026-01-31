import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
import models
import pandas_ta as ta
from engine.broker_interface import BrokerClient
import traceback
import ccxt
import json

# Global memory
active_bots = {}

class TradeBot:
    def __init__(self, strategy_id: int, db: Session):
        self.strategy_id = strategy_id
        self.db = db
        self.is_active = True
        self.logs = []
        
        # Load Strategy
        self.strategy = db.query(models.Strategy).filter(models.Strategy.id == strategy_id).first()
        self.symbol = self.strategy.symbol 
        
        # Load Rules (JSON)
        # format: [{'indicatorA': 'EMA', 'paramA': '1', 'operator': '>', 'indicatorB': 'EMA', 'paramB': '2'}]
        self.rules = self.strategy.logic_configuration.get("rules", [])
        
        # Load Creds
        self.cred = db.query(models.BrokerCredential).filter(
            models.BrokerCredential.user_id == self.strategy.user_id,
            models.BrokerCredential.is_active == True
        ).first()
        
        self.broker = None
        
        # Init Broker
        if self.cred:
            try:
                self.broker = BrokerClient(
                    broker_name=self.cred.broker_name,
                    api_key=self.cred.client_id,
                    secret_key=self.cred.api_key
                )
                self.log(f"✅ Broker Ready: {self.cred.broker_name}")
            except Exception as e:
                self.log(f"❌ Connection Error: {str(e)}")
        else:
            self.log("⚠️ No Active Broker Keys found.")

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {self.symbol}: {message}"
        self.logs.append(log_entry)
        if len(self.logs) > 100: self.logs.pop(0)
        if self.strategy_id in active_bots:
            active_bots[self.strategy_id]["logs"] = self.logs

    # --- DYNAMIC INDICATOR CALCULATOR ---
    def calculate_indicator_value(self, df, indicator_name, param):
        """
        Dynamically calculates the value based on user input.
        e.g., Name="EMA", Param="1" -> Calculates EMA(1)
        """
        try:
            param = int(float(param)) # Convert "1" to 1
            
            if indicator_name == "EMA":
                # Calculate EMA column
                series = ta.ema(df['close'], length=param)
                return series.iloc[-1] # Return latest value
            
            elif indicator_name == "SMA":
                series = ta.sma(df['close'], length=param)
                return series.iloc[-1]
            
            elif indicator_name == "RSI":
                series = ta.rsi(df['close'], length=param)
                return series.iloc[-1]
            
            elif indicator_name == "CLOSE":
                return df['close'].iloc[-1]
                
            elif indicator_name == "VALUE" or indicator_name == "Number Value":
                return param # Just return the raw number (e.g. 50)
                
            return 0
        except Exception as e:
            self.log(f"Calc Error ({indicator_name} {param}): {e}")
            return 0

    async def run(self):
        self.log(f"🚀 Starting Dynamic Engine. Loaded {len(self.rules)} Rules.")
        
        while self.is_active:
            try:
                if self.broker:
                    # 1. Fetch Price
                    current_price = self.broker.get_market_price(self.symbol)
                    
                    # 2. Fetch History (Enough for indicators)
                    df = self.broker.get_historical_data(self.symbol, self.strategy.timeframe, limit=200)
                    
                    if df.empty:
                        self.log("⏳ Waiting for data...")
                        await asyncio.sleep(5)
                        continue

                    # 3. CHECK DYNAMIC RULES
                    should_buy = False
                    should_sell = False
                    
                    # We iterate through the User's Rules
                    for rule in self.rules:
                        # Parse Left Side
                        val_a = self.calculate_indicator_value(df, rule['indicatorA'], rule['paramA'])
                        # Parse Right Side
                        val_b = self.calculate_indicator_value(df, rule['indicatorB'], rule['paramB'])
                        
                        op = rule['operator']
                        
                        # Logging for Debugging (This will show EMA 1 vs EMA 2 now!)
                        log_msg = f"🔍 Rule: {rule['indicatorA']}({rule['paramA']}) {val_a:.2f} {op} {rule['indicatorB']}({rule['paramB']}) {val_b:.2f}"
                        
                        # Evaluate Logic
                        condition_met = False
                        if op == ">" or op == "Greater Than":
                            condition_met = val_a > val_b
                        elif op == "<" or op == "Less Than":
                            condition_met = val_a < val_b
                        elif op == "==":
                            condition_met = val_a == val_b
                            
                        if condition_met:
                            self.log(f"✅ Condition Met: {log_msg}")
                            # For simplicity: Assume simple rules trigger Buy
                            # In V2, we can add a 'Action' dropdown to the builder
                            should_buy = True 
                        else:
                            # Heartbeat log (1 in 10 chance)
                            if datetime.now().second % 10 == 0:
                                self.log(f"👀 Monitoring: {log_msg}")

                    # 4. EXECUTE
                    if should_buy:
                        # Basic Safety: Don't spam orders every second
                        self.log(f"⚡ EXECUTING BUY: {self.symbol} @ {current_price}")
                        qty = 0.001 if "BTC" in self.symbol else 0.01 
                        order = self.broker.place_order(self.symbol, "buy", qty)
                        
                        if "error" in order:
                            self.log(f"❌ Order Failed: {order['message']}")
                        else:
                            self.log("🎉 ORDER SUCCESS!")
                        
                        await asyncio.sleep(60) # Wait 1 min before next trade

                else:
                    self.log("⚠️ Engine Idle: Connect Broker.")
                    await asyncio.sleep(10)

            except Exception as e:
                self.log(f"🔥 Error: {str(e)}")
                traceback.print_exc()
                await asyncio.sleep(5)

            await asyncio.sleep(2) # Tick speed

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