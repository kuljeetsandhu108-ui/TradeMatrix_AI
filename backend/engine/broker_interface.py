import ccxt
import pandas as pd
import time

class BrokerClient:
    def __init__(self, broker_name, api_key, secret_key):
        # 1. CLEAN THE NAME
        self.broker_name = broker_name.lower().strip()
        
        # --- SETTINGS ---
        # 🔴 REAL MONEY MODE ENABLED 🔴
        self.IS_TESTNET = False 
        
        print(f"🔧 System Check: CCXT Version {ccxt.__version__}")
        print(f"🔧 Mode: {'TESTNET/DEMO' if self.IS_TESTNET else 'REAL MONEY'}")

        # 2. CHECK SUPPORT
        if self.broker_name not in ccxt.exchanges:
            print(f"❌ Error: '{self.broker_name}' not found in CCXT.")
            raise ValueError(f"Exchange '{self.broker_name}' not supported.")

        # 3. INITIALIZE EXCHANGE
        try:
            exchange_class = getattr(ccxt, self.broker_name)
            
            config = {
                'apiKey': api_key,
                'secret': secret_key,
                'enableRateLimit': True,
                'options': {'defaultType': 'future'} 
            }
            
            self.exchange = exchange_class(config)
            
            # --- ENABLE TESTNET (IF TRUE) ---
            if self.IS_TESTNET:
                if 'test' in self.exchange.urls:
                    self.exchange.urls['api'] = self.exchange.urls['test']
                else:
                    self.exchange.set_sandbox_mode(True)
            
            # --- LOAD MARKETS (Crucial for Symbol Mapping) ---
            print(f"Loading markets for {self.broker_name}...")
            self.exchange.load_markets()
            print("✅ Markets Loaded.")
            
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
            # CCXT handles the mapping from 'BTC/USDT' to the exchange specific ID
            candles = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            if not candles:
                print(f"❌ Zero candles returned for {symbol}")
                return pd.DataFrame()

            df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"History Error ({self.broker_name}): {e}")
            return pd.DataFrame()

    def place_order(self, symbol, side, qty):
        try:
            print(f"⚡ Sending REAL {side} order for {qty} {symbol}...")
            order = self.exchange.create_order(symbol, 'market', side.lower(), qty)
            return order
        except Exception as e:
            print(f"Order Error ({self.broker_name}): {e}")
            return {"status": "error", "message": str(e)}