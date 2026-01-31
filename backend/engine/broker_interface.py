import ccxt
import pandas as pd
import time

class BrokerClient:
    def __init__(self, broker_name, api_key, secret_key):
        self.broker_name = broker_name.lower()
        
        # Initialize the specific exchange class dynamically
        # ccxt.delta(), ccxt.coindcx(), ccxt.binance()
        if hasattr(ccxt, self.broker_name):
            exchange_class = getattr(ccxt, self.broker_name)
            self.exchange = exchange_class({
                'apiKey': api_key,
                'secret': secret_key,
                'enableRateLimit': True,
                'options': {'defaultType': 'future'} # Default to Futures for Delta
            })
        else:
            raise ValueError(f"Exchange {broker_name} not supported")

    def get_market_price(self, symbol):
        """
        Fetches LTP for Crypto.
        Symbol format: "BTC/USDT"
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            print(f"Price Fetch Error: {e}")
            return None

    def get_historical_data(self, symbol, timeframe, limit=100):
        """
        Fetches OHLCV data.
        Timeframe: '1m', '5m', '1h', '1d'
        """
        try:
            # CCXT unifies this call for all exchanges
            candles = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            # Convert to DataFrame
            df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"History Error: {e}")
            return pd.DataFrame()

    def place_order(self, symbol, side, qty):
        """
        Executes a Crypto Order.
        Side: 'buy' or 'sell'
        """
        try:
            # Create a Market Order
            order = self.exchange.create_order(symbol, 'market', side.lower(), qty)
            return order
        except Exception as e:
            print(f"Order Error: {e}")
            return {"status": "error", "message": str(e)}