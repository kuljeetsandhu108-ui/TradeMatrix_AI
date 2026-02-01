import ccxt
import pandas as pd
import time

class BrokerClient:
    def __init__(self, broker_name, api_key, secret_key):
        self.broker_name = broker_name.lower().strip()
        
        # 🔴 CRITICAL SETTING: REAL MONEY MODE 🔴
        # Must be FALSE for Live Trading
        self.IS_TESTNET = False 
        
        print(f"🔧 System Check: CCXT Version {ccxt.__version__}")
        print(f"🔧 Target: {'TESTNET (DEMO)' if self.IS_TESTNET else 'MAINNET (REAL MONEY)'}")

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
            
            # FORCE REAL URLS (Just to be absolutely safe)
            if not self.IS_TESTNET:
                # Ensure we are pointing to the live server
                if self.broker_name == 'delta':
                    self.exchange.urls['api'] = 'https://api.delta.exchange'
            
            if self.IS_TESTNET:
                self.exchange.set_sandbox_mode(True)
            
            # --- CONNECTION TEST ---
            # We try to fetch the balance immediately. 
            # If this fails, we KNOW the keys/IP are wrong.
            print(f"🕵️ Testing connection to {self.broker_name}...")
            self.exchange.fetch_balance() 
            print("✅ Connection Verified! Keys are valid.")
            
            # Load Markets for symbol mapping
            self.exchange.load_markets()
            
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            # We raise the error so the frontend knows immediately
            raise ValueError(f"Invalid API Keys or IP blocked by Delta: {e}")

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