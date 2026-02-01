import ccxt
import pandas as pd
import time

class BrokerClient:
    def __init__(self, broker_name, api_key, secret_key):
        # 1. CLEAN THE NAME
        self.broker_name = broker_name.lower().strip()
        
        # 🔴 REAL MONEY MODE 🔴
        self.IS_TESTNET = False 
        
        print(f"🔧 System Check: CCXT Version {ccxt.__version__}")
        print(f"🔧 Target: {'TESTNET' if self.IS_TESTNET else 'MAINNET'}")

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
            
            # --- BUG FIX: DO NOT MANUALLY OVERWRITE URLS ---
            # CCXT defaults to the correct Mainnet URL automatically.
            # We only touch this if we are in Testnet mode.
            
            if self.IS_TESTNET:
                self.exchange.set_sandbox_mode(True)
            
            # --- CONNECTION TEST ---
            print(f"🕵️ Testing connection to {self.broker_name}...")
            
            # Try to fetch balance. If keys are wrong, this throws an error.
            self.exchange.fetch_balance() 
            print("✅ Connection Verified! Keys are valid.")
            
            # Load Markets (Crucial for symbol mapping)
            self.exchange.load_markets()
            
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            # Raise clear error for Frontend
            if "AuthenticationError" in str(e) or "401" in str(e):
                raise ValueError("Invalid API Key or Secret. Please check your credentials.")
            elif "string indices" in str(e):
                raise ValueError(f"CCXT Configuration Error: {e}")
            else:
                raise ValueError(f"Connection Failed: {e}")

    def get_market_price(self, symbol):
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            print(f"Price Error: {e}")
            return None

    def get_historical_data(self, symbol, timeframe, limit=100):
        try:
            candles = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            if not candles: return pd.DataFrame()

            df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"History Error: {e}")
            return pd.DataFrame()

    def place_order(self, symbol, side, qty):
        try:
            print(f"⚡ Executing REAL {side} order for {qty} {symbol}...")
            order = self.exchange.create_order(symbol, 'market', side.lower(), qty)
            return order
        except Exception as e:
            print(f"Order Error: {e}")
            return {"status": "error", "message": str(e)}