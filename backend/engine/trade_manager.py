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
        
        # 1. Load Strategy Details
        self.strategy = db.query(models.Strategy).filter(models.Strategy.id == strategy_id).first()
        self.symbol = self.strategy.symbol 
        
        # 2. Parse Logic Rules (JSON)
        # Handles cases where data might be a string or a dictionary
        raw_logic = self.strategy.logic_configuration
        if isinstance(raw_logic, str):
            try:
                raw_logic = json.loads(raw_logic)
            except:
                raw_logic = {}
            
        self.rules = raw_logic.get("rules", [])
        
        # 3. Load User Credentials
        # We find keys belonging to the USER who owns this strategy
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
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {self.symbol}: {message}"
        self.logs.append(log_entry)
        
        # Keep logs manageable
        if len(self.logs) > 100: self.logs.pop(0)
        
        # Sync with global state
        if self.strategy_id in active_bots:
            active_bots[self.strategy_id]["logs"] = self.logs

    def calculate_indicator_value(self, df, indicator_name, param):
        """
        Dynamic Calculator: Converts "EMA" and "9" into actual numbers.
        """
        try:
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
                return val_param
                
            return 0
        except Exception as e:
            return 0

    async def run(self):
        """
        The Main Execution Loop
        """
        self.log(f"🚀 Started Dynamic Engine. Watching {len(self.rules)} Rules.")
        
        while self.is_active:
            try:
                if self.broker:
                    # --- STEP 1: GET MARKET DATA ---
                    current_price = self.broker.get_market_price(self.symbol)
                    
                    if not current_price:
                        self.log("⚠️ Price fetch failed.")
                        await asyncio.sleep(5)
                        continue

                    # Fetch History
                    df = self.broker.get_historical_data(self.symbol, self.strategy.timeframe, limit=200)
                    
                    if df.empty:
                        self.log("⏳ Waiting for data candles...")
                        await asyncio.sleep(5)
                        continue

                    # --- STEP 2: EVALUATE RULES ---
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
                        elif op == "CROSS_UP": condition_met = val_a > val_b 
                            
                        if condition_met:
                            self.log(f"✅ Condition Met: {log_msg}")
                            should_buy = True 
                        else:
                            # Heartbeat log every 10 seconds
                            if datetime.now().second % 10 == 0:
                                self.log(f"👀 Monitoring: {log_msg}")

                    # --- STEP 3: EXECUTE TRADE ---
                    if should_buy:
                        # 1. Calculate Quantity (~$15 USDT)
                        # This ensures we meet minimum order requirements
                        target_usdt_value = 15.0
                        qty = target_usdt_value / current_price
                        
                        # 2. Smart Rounding
                        if "BTC" in self.symbol: qty = round(qty, 3)
                        elif "ETH" in self.symbol: qty = round(qty, 2)
                        elif "XRP" in self.symbol or "DOGE" in self.symbol: qty = int(qty)
                        else: qty = round(qty, 2)

                        self.log(f"⚡ SENDING BUY: {qty} {self.symbol} (~${target_usdt_value})")
                        
                        # 3. Place Order
                        order = self.broker.place_order(self.symbol, "buy", qty)
                        
                        # 4. CRITICAL FIX: CHECK FOR FAILURE
                        # We check if the response contains 'error' or status='error'
                        if (isinstance(order, dict) and "error" in order) or (isinstance(order, dict) and order.get("status") == "error"):
                            # Reveal the TRUE error message from the exchange
                            reason = order.get('message') or order.get('error') or "Unknown Reason"
                            self.log(f"❌ CRITICAL FAILURE: {reason}")
                        else:
                            # Success!
                            order_id = order.get('id', 'Unknown')
                            status = order.get('status', 'Filled')
                            self.log(f"🎉 ORDER SUCCESS! ID: {order_id} | Status: {status}")
                        
                        # Wait 1 minute to avoid double buying on same signal
                        await asyncio.sleep(60) 

                else:
                    self.log("⚠️ Engine Idle: Connect Broker.")
                    await asyncio.sleep(10)

            except Exception as e:
                self.log(f"🔥 Critical Error: {str(e)}")
                traceback.print_exc()
                await asyncio.sleep(5)

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