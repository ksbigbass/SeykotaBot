from dotenv import load_dotenv
import os
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest
import scrapeSyms

load_dotenv()
   
API_KEY = os.getenv('ALPACA_API_KEY')
SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')

# Initialize clients
trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
data_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)


class AlpacaTrader(object):
    def __init__(self):
        self.key_id = API_KEY
        self.secret_key = SECRET_KEY
        self.trading_client = trading_client
        self.data_client = data_client
        
        # Get account info
        self.account = self.trading_client.get_account()

        # The symbol we will be trading
        self.symbol = 'TSLA'
        self.symbol_lst = scrapeSyms.strong
        self.is_tradeable_lst = []

        # Get our starting position, in case we already have one open
        try:
            position = self.trading_client.get_open_position(self.symbol)
            self.position = int(float(position.qty))
        except:
            # No position exists
            self.position = 0

        try:
            self.balance = float(self.account.last_equity)
        except:
            self.balance = 0.00

    def set_symbol(self, symbol):
        self.symbol = symbol

    def get_symbol(self):
        return print(self.symbol)

    def set_symbol_lst(self, symbol_lst):
        self.symbol_lst = symbol_lst

    def get_symbol_lst(self):
        return print(self.symbol_lst)  

    def get_is_tradable_lst(self):
        return print(self.is_tradeable_lst)

    def get_positions(self):
        """Get all current positions"""
        try:
            positions = self.trading_client.get_all_positions()
            for pos in positions:
                print(f"{pos.symbol}: {pos.qty} shares @ ${pos.avg_entry_price}")
        except Exception as e:
            print(f"Error getting positions: {e}")

    def nasdaq(self):
        """Get NASDAQ assets"""
        try:
            assets = self.trading_client.get_all_assets()
            nasdaq_assets = [a for a in assets if a.exchange == 'NASDAQ']
            print(nasdaq_assets)
        except Exception as e:
            print(f"Error getting NASDAQ assets: {e}")

    def is_tradeable(self):
        """Check which symbols are tradeable"""
        try:
            for sym in self.symbol_lst:
                try:
                    # Parse the symbol if it contains company name
                    clean_sym = sym.split(',')[0].strip() if ',' in sym else sym.strip()
                    
                    asset = self.trading_client.get_asset(clean_sym)
                    
                    if asset.tradable:
                        self.is_tradeable_lst.append(clean_sym)
                except Exception as e:
                    print(f"Skipping {sym}: {e}")
                    pass
        except Exception as e:
            print(f'Error checking tradeable: {e}')

    def get_last_price(self, symbol):
        """Get the latest price for a symbol"""
        try:
            request_params = StockLatestTradeRequest(symbol_or_symbols=symbol)
            latest_trade = self.data_client.get_stock_latest_trade(request_params)
            return float(latest_trade[symbol].price)
        except Exception as e:
            print(f"Could not get price for {symbol}: {e}")
            return None

    def send_order(self, target_qty):
        """Send a limit buy order"""
        if self.position == 0 and target_qty > 0:
            try:
                self.last_price = self.get_last_price(self.symbol)
                
                if self.last_price is None:
                    print(f"Cannot place order for {self.symbol} - no price data")
                    return
                
                # Calculate limit price (10% below current price)
                limit_price = round(self.last_price * 0.90, 2)
                
                # Create limit order request
                order_data = LimitOrderRequest(
                    symbol=self.symbol,
                    qty=target_qty,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.GTC,
                    limit_price=limit_price
                )
                
                order = self.trading_client.submit_order(order_data)
                print(f'✓ Made order: {target_qty} shares of {self.symbol} at ${limit_price}')
                
            except Exception as e:
                print(f'✗ Error placing order for {self.symbol}: {e}')
         
    def postion_size(self):
        """Calculate position size and place order"""
        try:
            self.last_price = self.get_last_price(self.symbol)
            
            if self.last_price is None:
                return
            
            # Use 3% of balance per position
            target_qty = int(self.balance * 0.03 // self.last_price)
            
            if target_qty > 0:
                self.send_order(target_qty)
            else:
                print(f"Position size too small for {self.symbol}")
                
        except Exception as e:
            print(f"Error calculating position size: {e}")

    def postion_size_lst(self):
        """Place orders for all tradeable stocks in list"""
        for sym in self.is_tradeable_lst:
            self.symbol = sym
            self.postion_size()

    def todays_win_loss(self):
        """Display today's P/L"""
        balance_change = float(self.account.equity) - float(self.account.last_equity)
        print(f'Today\'s portfolio balance change: ${balance_change:.2f}')  

    def buying_power(self):
        """Display buying power"""
        return print(f'${self.account.buying_power} via margin and ${self.account.cash} is cash.')   

    def quick_order(self, symbol, qty=1):
        """Place a quick market order"""
        try:
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.GTC
            )
            
            order = self.trading_client.submit_order(order_data)
            print(f"✓ Market order placed: {qty} shares of {symbol}")
            
        except Exception as e:
            print(f"✗ Error placing market order: {e}")


if __name__ == '__main__':
    trader = AlpacaTrader()
    trader.set_symbol('APPS')
    # trader.set_symbol_lst(['OILU', 'LXU', 'CRGY', 'BPT', 'SGML', 'AMR', 'ZETA', 'NRT', 'IPI', 'NRGV', 'AR', 'UAN'])
    # trader.quick_order('NOACW')
    trader.get_positions()
    trader.is_tradeable()
    trader.get_is_tradable_lst()
    # trader.postion_size_lst()
    trader.todays_win_loss()
    trader.buying_power()