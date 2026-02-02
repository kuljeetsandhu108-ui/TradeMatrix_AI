import ccxt
import pandas as pd
import time

class BrokerClient:
    def __init__(self, broker_name, api_key, secret_key):
        self.broker_name = broker_name.lower().strip()
        
        # 🔴 ENSURE THIS IS FALSE FOR REAL MONEY 🔴
        self.IS_TESTNET = False 
        
        # --- DEBUGGING PRINTS (Check your Logs!) ---
        masked_key = f"{api_key[:4]}...{api_key[-4:]}" if api_key and len(api_key) > 8 else "INVALID KEY"
        print(f"🔧 [DEBUG] Initializing {self.broker_name}")
        print(f"🔧 [DEBUG] Using Key: {masked_key}")
        print(f"🔧 [DEBUG] Mode: {'TESTNET' if self.IS_TESTNET else 'MAINNET'}")

        if self.broker_name not in ccxt.exchanges:
            raise ValueError(f"Exchange '{self.broker_name}' not supported.")

        try:
            exchange_class = getattr(ccxt, self.broker_name)
            
            config = {
                'apiKey': api_key,
                'secret': secret_key,
                'enableRateLimit': True,
                'options': {'defaultType': 'future'} 
            }
            
            self.exchange = exchange_class(config)
            
            # --- FORCE URL CHECK ---
            if self.IS_TESTNET:
                self.exchange.set_sandbox_mode(True)
            
            # PRINT THE EXACT URL WE ARE HITTING
            current_url = self.exchange.urls['api']
            print(f"🔗 [DEBUG] Connecting to URL: {current_url}")
            
            # --- CONNECTION TEST ---
            print(f"🕵️ Testing balance fetch...")
            self.exchange.fetch_balance() 
            print("✅ Connection Verified!")
            
            self.exchange.load_markets()
            
        except Exception as e:
            print(f"❌ Connection Error details: {e}")
            # Detect specific Delta error
            if "invalid_api_key" in str(e):
                raise ValueError(f"❌ REJECTED: The Key {masked_key} does not exist on {current_url}. \nCheck: 1. Are you on Demo vs Real? 2. Did you copy Secret into Key field?")
            raise ValueError(f"Connection Failed: {e}")

    def get_market_price(self, symbol):
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except:
            return None

    def get_historical_data(self, symbol, timeframe, limit=100):
        try:
            candles = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            if not candles: return pd.DataFrame()
            df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except:
            return pd.DataFrame()

    def place_order(self, symbol, side, qty):
        try:
            print(f"⚡ Executing {side} order for {qty} {symbol}...")
            order = self.exchange.create_order(symbol, 'market', side.lower(), qty)
            return order
        except Exception as e:
            return {"status": "error", "message": str(e)}