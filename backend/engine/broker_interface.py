from fyers_apiv3 import fyersModel
import pandas as pd
import datetime

class BrokerClient:
    def __init__(self, client_id, access_token):
        self.client_id = client_id
        self.access_token = access_token
        
        # Initialize Fyres SDK
        self.fyers = fyersModel.FyersModel(
            client_id=self.client_id, 
            token=self.access_token,
            is_async=False, 
            log_path=""
        )

    def get_market_price(self, symbol):
        """
        Fetches the current market price (LTP).
        Symbol format for Fyres: "NSE:NIFTY50-INDEX" or "NSE:SBIN-EQ"
        """
        data = {
            "symbols": symbol
        }
        try:
            response = self.fyers.quotes(data=data)
            if 'd' in response and len(response['d']) > 0:
                return response['d'][0]['v']['lp'] # Last Traded Price
            return None
        except Exception as e:
            print(f"Error fetching price: {e}")
            return None

    def get_historical_data(self, symbol, timeframe, duration_days=5):
        """
        Fetches candle data to calculate indicators (EMA, RSI).
        """
        # Map timeframe "5m" to Fyres format
        tf_map = {"1m": "1", "5m": "5", "15m": "15", "1H": "60"}
        
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=duration_days)
        
        data = {
            "symbol": symbol,
            "resolution": tf_map.get(timeframe, "5"),
            "date_format": "1",
            "range_from": start_date.strftime("%Y-%m-%d"),
            "range_to": today.strftime("%Y-%m-%d"),
            "cont_flag": "1"
        }

        try:
            response = self.fyers.history(data=data)
            if 'candles' in response:
                df = pd.DataFrame(response['candles'])
                df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                return df
            return pd.DataFrame()
        except Exception as e:
            print(f"History Error: {e}")
            return pd.DataFrame()

    def place_order(self, symbol, side, qty=1):
        """
        Executes a real trade.
        side: 1 (Buy), -1 (Sell)
        """
        order_data = {
            "symbol": symbol,
            "qty": qty,
            "type": 2, # Market Order
            "side": 1 if side == "BUY" else -1,
            "productType": "INTRADAY",
            "limitPrice": 0,
            "stopPrice": 0,
            "validity": "DAY",
            "disclosedQty": 0,
            "offlineOrder": False,
        }

        try:
            response = self.fyers.place_order(data=order_data)
            return response
        except Exception as e:
            print(f"Order Placement Error: {e}")
            return {"status": "error", "message": str(e)}