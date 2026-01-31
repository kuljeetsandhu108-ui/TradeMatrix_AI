import ccxt
import pandas as pd
import time

class BrokerClient:
    def __init__(self, broker_name, api_key, secret_key):
        # 1. CLEAN THE NAME
        self.broker_name = broker_name.lower().strip()
        
        # --- DEBUGGING BLOCK ---
        print(f"🔧 System CCXT Version: {ccxt.__version__}")
        print(f"🔧 Trying to load: '{self.broker_name}'")
        
        # Check if exchange is in the official list
        if self.broker_name not in ccxt.exchanges:
            print(f"❌ '{self.broker_name}' is NOT in ccxt.exchanges list.")
            # Print similar exchanges to help debug
            similar = [e for e in ccxt.exchanges if 'coin' in e or 'delta' in e]
            print(f"💡 Did you mean one of these? {similar}")
            raise ValueError(f"Exchange '{self.broker_name}' not supported by this CCXT version.")
        # -----------------------

        # 2. INITIALIZE EXCHANGE
        try:
            exchange_class = getattr(ccxt, self.broker_name)
            self.exchange = exchange_class({
                'apiKey': api_key,
                'secret': secret_key,
                'enableRateLimit': True,
                'options': {'defaultType': 'future'} # Default to futures
            })
            
            # 3. TEST CONNECTION (Optional but good)
            # This ensures keys are valid before starting the bot loop
            # self.exchange.fetch_balance() 
            
        except Exception as e:
            print(f"❌ Init Error: {e}")
            raise ValueError(f"Failed to initialize {self.broker_name}: {e}")

    def get_market_price(self, symbol):
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            print(f"Price Fetch Error ({self.broker_name}): {e}")
            return None

    def get_historical_data(self, symbol, timeframe, limit=100):
        try:
            candles = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"History Error ({self.broker_name}): {e}")
            return pd.DataFrame()

    def place_order(self, symbol, side, qty):
        try:
            # Create a Market Order
            order = self.exchange.create_order(symbol, 'market', side.lower(), qty)
            return order
        except Exception as e:
            print(f"Order Error ({self.broker_name}): {e}")
            return {"status": "error", "message": str(e)}