import ccxt
import pandas as pd
import time

class BrokerClient:
    def __init__(self, broker_name, api_key, secret_key):
        # 1. CLEAN THE NAME (Remove spaces, lowercase)
        self.broker_name = broker_name.lower().strip()
        
        # 2. CHECK SUPPORT
        if not hasattr(ccxt, self.broker_name):
            # Debugging: Print similar exchanges if exact match fails
            print(f"❌ Error: '{self.broker_name}' not found in CCXT.")
            raise ValueError(f"Exchange '{self.broker_name}' not supported. Check spelling.")

        # 3. INITIALIZE EXCHANGE
        try:
            exchange_class = getattr(ccxt, self.broker_name)
            self.exchange = exchange_class({
                'apiKey': api_key,
                'secret': secret_key,
                'enableRateLimit': True,
                'options': {'defaultType': 'future'} # Default to futures if available
            })
            # Some exchanges require loading markets first
            # self.exchange.load_markets() 
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
            # CoinDCX/Delta specific adjustments could go here
            order = self.exchange.create_order(symbol, 'market', side.lower(), qty)
            return order
        except Exception as e:
            print(f"Order Error ({self.broker_name}): {e}")
            return {"status": "error", "message": str(e)}