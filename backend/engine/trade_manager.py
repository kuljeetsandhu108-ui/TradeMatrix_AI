import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
import models
import pandas_ta as ta
from engine.broker_interface import BrokerClient
import traceback
import ccxt

# Global memory
active_bots = {}

class TradeBot:
    def __init__(self, strategy_id: int, db: Session):
        self.strategy_id = strategy_id
        self.db = db
        self.is_active = True
        self.logs = []
        
        # Load Strategy & Rules
        self.strategy = db.query(models.Strategy).filter(models.Strategy.id == strategy_id).first()
        self.symbol = self.strategy.symbol 
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

    # --- DYNAMIC CALCULATOR ---
    def calculate_indicator_value(self, df, indicator_name, param):
        try:
            param = float(param) # Convert string input to number
            if param.is_integer(): param = int(param)

            if indicator_name == "EMA":
                return ta.ema(df['close'], length=param).iloc[-1]
            elif indicator_name == "SMA":
                return ta.sma(df['close'], length=param).iloc[-1]
            elif indicator_name == "RSI":
                return ta.rsi(df['close'], length=param).iloc[-1]
            elif indicator_name == "CLOSE":
                return df['close'].iloc[-1]
            elif indicator_name in ["VALUE", "Number Value"]:
                return param
            return 0
        except Exception as e:
            return 0

    async def run(self):
        self.log(f"🚀 Started Dynamic Engine. Rules: {len(self.rules)}")
        
        while self.is_active:
            try:
                if self.broker:
                    current_price = self.broker.get_market_price(self.symbol)
                    df = self.broker.get_historical_data(self.symbol, self.strategy.timeframe, limit=200)
                    
                    if df.empty:
                        self.log("⏳ Waiting for data...")
                        await asyncio.sleep(5)
                        continue

                    # CHECK RULES
                    should_buy = False
                    
                    for rule in self.rules:
                        val_a = self.calculate_indicator_value(df, rule['indicatorA'], rule['paramA'])
                        val_b = self.calculate_indicator_value(df, rule['indicatorB'], rule['paramB'])
                        op = rule['operator']
                        
                        # --- DEBUG LOG (This replaces the old "EMA9" log) ---
                        log_msg = f"Rule: {rule['indicatorA']}({rule['paramA']}) {val_a:.2f} {op} {rule['indicatorB']}({rule['paramB']}) {val_b:.2f}"
                        
                        condition_met = False
                        if op in [">", "Greater Than"]: condition_met = val_a > val_b
                        elif op in ["<", "Less Than"]: condition_met = val_a < val_b
                        elif op == "==": condition_met = val_a == val_b
                            
                        if condition_met:
                            self.log(f"✅ Condition Met: {log_msg}")
                            should_buy = True 
                        else:
                            # Heartbeat log
                            if datetime.now().second % 10 == 0:
                                self.log(f"👀 Monitoring: {log_msg}")

                    if should_buy:
                        self.log(f"⚡ EXECUTING BUY: {self.symbol} @ {current_price}")
                        # Execute trade...
                        order = self.broker.place_order(self.symbol, "buy", 0.001) # Hardcoded qty for safety
                        if "error" in order:
                            self.log(f"❌ Order Failed: {order.get('message', order)}")
                        else:
                            self.log("🎉 ORDER SUCCESS!")
                        
                        await asyncio.sleep(60) 

                else:
                    self.log("⚠️ Engine Idle: Connect Broker.")
                    await asyncio.sleep(10)

            except Exception as e:
                self.log(f"🔥 Error: {str(e)}")
                traceback.print_exc()
                await asyncio.sleep(5)

            await asyncio.sleep(2) 

    def stop(self):
        self.is_active = False
        self.log("🛑 Bot Stopped")

# --- CONTROL FUNCTIONS ---
async def start_bot(strategy_id: int, db: Session):
    if strategy_id in active_bots: return {"status": "error", "message": "Running"}
    bot = TradeBot(strategy_id, db)
    task = asyncio.create_task(bot.run())
    active_bots[strategy_id] = {"status": "running", "task": task, "logs": bot.logs, "instance": bot}
    
    # DB Update
    strat = db.query(models.Strategy).filter(models.Strategy.id == strategy_id).first()
    strat.is_running = True
    db.commit()
    return {"status": "success"}

async def stop_bot(strategy_id: int, db: Session):
    if strategy_id not in active_bots: return {"status": "error", "message": "Stopped"}
    active_bots[strategy_id]["instance"].stop()
    active_bots[strategy_id]["task"].cancel()
    del active_bots[strategy_id]
    
    # DB Update
    strat = db.query(models.Strategy).filter(models.Strategy.id == strategy_id).first()
    strat.is_running = False
    db.commit()
    return {"status": "success"}