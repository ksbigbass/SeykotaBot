from dotenv import load_dotenv
import os
from alpaca.trading.client import TradingClient


load_dotenv()
   
API_KEY = os.getenv('ALPACA_API_KEY')
SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
base_url = os.getenv('ALPACA_BASE_URL')

trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)



base_url = "https://paper-api.alpaca.markets"
# base_url = 'https://data.alpaca.markets/v2'

ACCOUNT_URL = "{}/v2/account".format(base_url)
ORDERS_URL = "{}/v2/orders".format(base_url)


HEADERS = {"APCA-API-KEY-ID": API_KEY, "APCA-API-SECRET-KEY": SECRET_KEY}

api = tradeapi.REST(API_KEY, SECRET_KEY, base_url, api_version='v2')

class AlpacaTrader(object):
    def __init__(self):
        # API authentication keys can be taken from the Alpaca dashboard.
        # https://app.alpaca.markets/paper/dashboard/overview
        self.key_id = API_KEY
        self.secret_key = SECRET_KEY
        self.base_url = 'https://paper-api.alpaca.markets'
        self.account = api.get_account()

        # The symbol we will be trading
        self.symbol = 'TSLA'
        self.symbol_lst = scrapeSyms.strong
        self.is_tradeable_lst = []

        # When this variable is not None, we have an order open
        # self.current_order = None

        # The closing price of the last aggregate we saw
        # self.last_price = api.get_latest_trade(self.symbol).price

        # The connection to the Alpaca API
        self.api = tradeapi.REST(
            self.key_id,
            self.secret_key,
            self.base_url
        )
        
        # Get our starting position, in case we already have one open
        try:
            self.position = int(self.api.get_position(self.symbol).qty)
        except:
            # No position exists
            self.position = 0

        try:
            self.balance = float(self.account.last_equity)
        except:
            self.balance = 0.00

    def set_symbol(self,symbol):
        self.symbol = symbol

    def get_symbol(self):
        return print(self.symbol)

    def set_symbol_lst(self,symbol_lst):
        self.symbol_lst = symbol_lst

    def get_symbol_lst(self):
        return print(self.symbol_lst)  

    def get_is_tradable_lst(self):
        return print(self.is_tradeable_lst)         

    def nasdaq(self):
        active_assets = api.list_assets(status='active')
        # Filter the assets down to just those on NASDAQ.
        nasdaq_assets = [a for a in active_assets if a.exchange == 'NASDAQ']
        print(nasdaq_assets)

    def is_tradeable(self):
       
        try:
            for sym in self.symbol_lst:
                try:
                    asset = api.get_asset(sym)
                
                    if asset.tradable == True:
                        self.is_tradeable_lst.append(sym)
                except:
                    pass

        except:
            print('error')
          

    def send_order(self, target_qty):
        if self.position == 0:
            api.submit_order(self.symbol, target_qty, side='buy', type='limit', time_in_force='gtc', limit_price=(int(self.last_price - self.last_price * .10)))
            return print (f'made order {target_qty} of {self.symbol} at {int(self.last_price - self.last_price * .10)}')
         
    def postion_size(self):
        self.last_price = api.get_latest_trade(self.symbol).price
        target_qty = self.balance *.03 // self.last_price
        self.send_order(target_qty)

    def postion_size_lst(self):
        for sym in self.is_tradeable_lst:
            self.symbol = sym
            self.last_price = api.get_latest_trade(self.symbol).price
            target_qty = self.balance *.03 // self.last_price
            self.send_order(target_qty)

    def todays_win_loss(self):
        balance_change = float(self.account.equity) - float(self.account.last_equity)
        print(f'Today\'s portfolio balance change: ${balance_change}')  

    def buying_power(self):
        return print(f'${self.account.buying_power} via margin and ${self.account.cash} is cash.')   


    def quick_order(self,symbol,qty=1):
        api.submit_order(symbol, qty, side='buy', type='market', time_in_force='gtc')


if __name__ == '__main__':
    trader = AlpacaTrader()
    trader.set_symbol('APPS')
    # trader.set_symbol_lst(['OILU', 'LXU', 'CRGY', 'BPT', 'SGML', 'AMR', 'ZETA', 'NRT', 'IPI', 'NRGV', 'AR', 'UAN'])
    # trader.quick_order('NOACW')
    trader.get_positions()
    trader.is_tradeable()
    trader.get_is_tradable_lst()
    trader.postion_size_lst()
    trader.todays_win_loss()
    trader.buying_power()
           
