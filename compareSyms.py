import pandas as pd
import scrapeSyms
import datetime as dt
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

API_KEY = os.getenv('ALPACA_API_KEY')
SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')

# Initialize trading client
trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
data_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

def get_current_price(symbol):
    """Get the current market price for a symbol"""
    try:
        request_params = StockLatestTradeRequest(symbol_or_symbols=symbol)
        latest_trade = data_client.get_stock_latest_trade(request_params)
        return float(latest_trade[symbol].price)
    except Exception as e:
        print(f"Could not get price for {symbol}: {e}")
        return None


def create_sell_list(symbols, quantities):
    """Sell positions that are no longer in the strong list"""
    sold_count = 0
    
    for i, stock in enumerate(symbols):
        if stock not in scrapeSyms.strong:
            try:
                qty = quantities[i]
                
                # Get current price for better limit order
                current_price = get_current_price(stock)
                
                if current_price and current_price > 1.0:
                    # Set limit price 5% below current price
                    limit_price = round(current_price * 0.95, 2)
                else:
                    # Fallback to $1 if price unavailable or too low
                    limit_price = 1.0
                
                # Create sell limit order
                order_data = LimitOrderRequest(
                    symbol=stock,
                    qty=qty,
                    side=OrderSide.SELL,
                    time_in_force=TimeInForce.GTC,
                    limit_price=limit_price
                )
                
                order = trading_client.submit_order(order_data)
                print(f"✓ Placed sell order for {qty} shares of {stock} at ${limit_price}")
                sold_count += 1
                
            except Exception as e:
                print(f"✗ Error selling {stock}: {e}")
    
    if sold_count == 0:
        print("No positions to sell - all holdings are still strong!")
    else:
        print(f"\nTotal sell orders placed: {sold_count}")


def check_strong_overlap(position_symbols):
    """Check which current positions are still in the strong list"""
    strong_overlap = []
    weak_positions = []
    
    for stock in position_symbols:
        if stock in scrapeSyms.strong:
            strong_overlap.append(stock)
        else:
            weak_positions.append(stock)
    
    print(f"\n{'='*50}")
    print(f"Portfolio Analysis")
    print(f"{'='*50}")
    print(f"Total positions: {len(position_symbols)}")
    print(f"Still strong: {len(strong_overlap)} → {strong_overlap}")
    print(f"No longer strong: {len(weak_positions)} → {weak_positions}")
    print(f"{'='*50}\n")
    
    return strong_overlap, weak_positions


def get_positions():
    """Get current positions and sell any that aren't strong anymore"""
    try:
        positions = trading_client.get_all_positions()
        
        if not positions:
            print("No open positions found.")
            return
        
        symbols = [position.symbol for position in positions]
        quantities = [abs(float(position.qty)) for position in positions]
        
        # Show analysis
        strong_overlap, weak_positions = check_strong_overlap(symbols)
        
        # Sell weak positions
        if weak_positions:
            print("Selling positions that are no longer strong...\n")
            create_sell_list(symbols, quantities)
        else:
            print("All positions are still in the strong list. No action needed.")
            
    except Exception as e:
        print(f"Error getting positions: {e}")


def show_strong_stocks():
    """Display current strong stocks from Seykota"""
    print(f"\n{'='*50}")
    print(f"Current Strong Stocks (Top 15)")
    print(f"{'='*50}")
    for i, stock in enumerate(scrapeSyms.strong, 1):
        print(f"{i:2d}. {stock}")
    print(f"{'='*50}\n")


if __name__ == '__main__':
    print("TrendTracker Position Manager")
    print(f"Date: {dt.date.today()}\n")
    
    # Show current strong stocks
    show_strong_stocks()
    
    # Analyze and manage positions
    get_positions()