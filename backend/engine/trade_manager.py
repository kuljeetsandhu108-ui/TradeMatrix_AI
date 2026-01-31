import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
import models
import pandas_ta as ta
from engine.broker_interface import BrokerClient
import traceback
import ccxt
import json

# Global dictionary to track running bots in memory
active_bots = {}

class TradeBot:
    def __init__(self, strategy_id: int, db: Session):
        self.strategy_id = strategy_id
        self.db = db
        self.is_active = True
        self.logs = []
        
        # 1. Load Strategy Details from Database
        self.strategy = db.query(models.Strategy).filter(models.Strategy.id == strategy_id).first()
        self.symbol = self.strategy.symbol 
        
        # 2. Parse the Logic Rules (JSON)
        # Example: [{'indicatorA': 'EMA', 'paramA': '1', 'operator': '>', 'indicatorB': 'EMA', 'paramB': '2'}]
        raw_logic = self.strategy.logic_configuration
        if isinstance(raw_logic, str):
            # Handle case where it might be stored as a string
            raw_logic = json.loads(raw_logic)
            
        self.rules = raw_logic.get("rules", [])
        
        # 3. Load User Credentials (Security Check)
        # We find the keys belonging to the USER who owns this strategy
        self.cred = db.query(models.BrokerCredential).filter(
            models.BrokerCredential.user_id == self.strategy.user_id,
            models.BrokerCredential.is_active == True
        ).first()
        
        self.broker = None
        
        # 4. Initialize Broker Connection
        if self.cred:
            try:
                self.broker = BrokerClient(
                    broker_name=self.cred.broker_name,
                    api_key=self.cred.client_id,
                    secret_key=self.cred.api_key
                )
                self.log(f"✅ Broker Ready: {self.cred.broker_name.upper()}")
            except Exception as e:
                self.log(f"❌ Connection Error: {str(e)}")
        else:
            self.log("⚠️ No Active Broker Keys found. Please configure Broker Config.")

    def log(self, message):
        """
        Adds a timestamped log to the in-memory list.
        The frontend polls this list to show the black terminal.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {self.symbol}: {message}"
        self.logs.append(log_entry)
        
        # Keep logs manageable (Last 100 lines)
        if len(self.logs) > 100: self.logs.pop(0)
        
        # Sync with global state so API can read it
        if self.strategy_id in active_bots:
            active_bots[self.strategy_id]["logs"] = self.logs

    def calculate_indicator_value(self, df, indicator_name, param):
        """
        The Brain: Converts "EMA" and "9" into an actual number based on market data.
        """
        try:
            # Convert param to number (handle decimals if needed)
            val_param = float(param)
            int_param = int(val_param)

            if indicator_name == "EMA":
                return ta.ema(df['close'], length=int_param).iloc[-1]
            
            elif indicator_name == "SMA":
                return ta.sma(df['close'], length=int_param).iloc[-1]
            
            elif indicator_name == "RSI":
                return ta.rsi(df['close'], length=int_param).iloc[-1]
            
            elif indicator_name == "CLOSE":
                return df['close'].iloc[-1]
            
            elif indicator_name == "OPEN":
                return df['open'].iloc[-1]
            
            elif indicator_name in ["VALUE", "Number Value"]:
                return val_param # Just return the raw number (e.g. 50 for RSI 50)
                
            return 0
        except Exception as e:
            # self.log(f"Calc Error ({indicator_name}): {e}") 
            return 0

    # ... (imports and init remain the same) ...

    async def run(self):
        self.log(f"🚀 Started Dynamic Engine. Watching {len(self.rules)} Rules.")
        
        while self.is_active:
            try:
                if self.broker:
                    # 1. GET DATA
                    current_price = self.broker.get_market_price(self.symbol)
                    
                    if not current_price:
                        self.log("⚠️ Price fetch failed.")
                        await asyncio.sleep(5)
                        continue

                    # 2. GET HISTORY
                    df = self.broker.get_historical_data(self.symbol, self.strategy.timeframe, limit=200)
                    if df.empty:
                        self.log("⏳ Waiting for candles...")
                        await asyncio.sleep(5)
                        continue

                    # 3. EVALUATE RULES
                    should_buy = False
                    
                    for rule in self.rules:
                        val_a = self.calculate_indicator_value(df, rule['indicatorA'], rule['paramA'])
                        val_b = self.calculate_indicator_value(df, rule['indicatorB'], rule['paramB'])
                        op = rule['operator']
                        
                        log_msg = f"Rule: {rule['indicatorA']}({rule['paramA']}) {val_a:.2f} {op} {rule['indicatorB']}({rule['paramB']}) {val_b:.2f}"
                        
                        condition_met = False
                        if op in [">", "Greater Than"]: condition_met = val_a > val_b
                        elif op in ["<", "Less Than"]: condition_met = val_a < val_b
                        elif op == "==": condition_met = val_a == val_b
                            
                        if condition_met:
                            self.log(f"✅ Condition Met: {log_msg}")
                            should_buy = True 
                        else:
                            if datetime.now().second % 10 == 0:
                                self.log(f"👀 Monitoring: {log_msg}")

                    # 4. EXECUTE TRADE (With Size Calculation)
                    # 4. EXECUTE TRADE
                    if should_buy:
                        # --- CALCULATE QUANTITY (~$15 USDT) ---
                        target_usdt_value = 15.0
                        qty = target_usdt_value / current_price
                        
                        # Rounding logic specific to coins
                        if "BTC" in self.symbol: qty = round(qty, 3)
                        elif "ETH" in self.symbol: qty = round(qty, 2)
                        elif "XRP" in self.symbol or "DOGE" in self.symbol: qty = int(qty)
                        else: qty = round(qty, 2)

                        self.log(f"⚡ SENDING BUY: {qty} {self.symbol} (~${target_usdt_value})")
                        
                        # Send Order
                        order = self.broker.place_order(self.symbol, "buy", qty)
                        
                        # --- CRITICAL FIX: CHECK FOR STATUS ERROR ---
                        # We check if 'error' key exists OR if 'status' is 'error'
                        if (isinstance(order, dict) and "error" in order) or (isinstance(order, dict) and order.get("status") == "error"):
                            reason = order.get('message') or order.get('error') or "Unknown Reason"
                            self.log(f"❌ CRITICAL FAILURE: {reason}")
                        else:
                            order_id = order.get('id', 'Unknown')
                            status = order.get('status', 'Filled')
                            self.log(f"🎉 ORDER SUCCESS! ID: {order_id} | Status: {status}")
                        
                        await asyncio.sleep(60) # Wait 1 min to avoid double buying
                        
                            self.log(f"🎉 ORDER SENT! ID: {order_id} | Status: {status}")
                        
                        await asyncio.sleep(60) 

                else:
                    self.log("⚠️ Engine Idle: Connect Broker.")
                    await asyncio.sleep(10)

            except Exception as e:
                self.log(f"🔥 Error: {str(e)}")
                traceback.print_exc()
                await asyncio.sleep(5)

            await asyncio.sleep(3)

    def stop(self):
        self.is_active = False
        self.log("🛑 Bot Stopped")

# --- API CONTROL FUNCTIONS (Called by Router) ---

async def start_bot(strategy_id: int, db: Session):
    if strategy_id in active_bots:
        return {"status": "error", "message": "Bot already running"}
    
    # Initialize the Bot Class
    bot = TradeBot(strategy_id, db)
    
    # Run it in the background
    task = asyncio.create_task(bot.run())
    
    # Store reference
    active_bots[strategy_id] = {
        "status": "running",
        "task": task,
        "logs": bot.logs,
        "instance": bot
    }
    
    # Update Database Status
    strat = db.query(models.Strategy).filter(models.Strategy.id == strategy_id).first()
    strat.is_running = True
    db.commit()
    
    return {"status": "success", "message": "Bot Started"}

async def stop_bot(strategy_id: int, db: Session):
    if strategy_id not in active_bots:
        return {"status": "error", "message": "Bot not active"}
    
    # Stop Logic
    active_bots[strategy_id]["instance"].stop()
    active_bots[strategy_id]["task"].cancel()
    del active_bots[strategy_id]
    
    # Update Database Status
    strat = db.query(models.Strategy).filter(models.Strategy.id == strategy_id).first()
    strat.is_running = False
    db.commit()
    
    return {"status": "success", "message": "Bot Stopped"}