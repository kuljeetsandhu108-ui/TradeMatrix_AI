import ccxt
import pandas as pd
import time

class BrokerClient:
    def __init__(self, broker_name, api_key, secret_key):
        # 1. CLEAN THE NAME
        self.broker_name = broker_name.lower().strip()
        
        # --- SETTINGS ---
        # SET THIS TO TRUE FOR DEMO TRADING
        self.IS_TESTNET = True 
        
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
            
            # --- ENABLE SANDBOX (DEMO) MODE ---
            if self.IS_TESTNET:
                if 'test' in self.exchange.urls:
                    self.exchange.urls['api'] = self.exchange.urls['test']
                    print(f"✅ Switched {self.broker_name} to Testnet URLs")
                else:
                    self.exchange.set_sandbox_mode(True)
                    print(f"✅ Enabled Sandbox Mode for {self.broker_name}")
            # ----------------------------------
            
        except Exception as e:
            print(f"❌ Init Error: {e}")
            raise ValueError(f"Failed to initialize {self.broker_name}: {e}")

    def get_market_price(self, symbol):
        try:
            # Fetch Ticker
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
            # For Delta Demo, ensure the symbol format is correct (e.g. BTC/USDT:USDT)
            # CCXT usually handles this, but sometimes testnet symbols differ slightly
            
            print(f"⚡ Sending {side} order for {qty} {symbol} to DEMO server...")
            order = self.exchange.create_order(symbol, 'market', side.lower(), qty)
            return order
        except Exception as e:
            print(f"Order Error ({self.broker_name}): {e}")
            return {"status": "error", "message": str(e)}