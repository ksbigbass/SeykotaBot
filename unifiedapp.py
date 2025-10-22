"""
TrendTracker Flask API - Complete Integration
Combines scrapeSyms, compareSyms, and AlpacaTrader functionality
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
from datetime import datetime
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest
import scrapeSyms
from AlpacaTrader import AlpacaTrader

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv('ALPACA_API_KEY')
SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')

app = Flask(__name__, static_folder='.')
CORS(app)

# Initialize Alpaca clients
trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
data_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

# Helper function from compareSyms.py
def get_current_price(symbol):
    """Get the current market price for a symbol"""
    try:
        request_params = StockLatestTradeRequest(symbol_or_symbols=symbol)
        latest_trade = data_client.get_stock_latest_trade(request_params)
        return float(latest_trade[symbol].price)
    except Exception as e:
        print(f"Could not get price for {symbol}: {e}")
        return None

@app.route('/')
def index():
    """Serve the React dashboard"""
    return send_from_directory('.', 'dashboard.html')

@app.route('/api/account', methods=['GET'])
def get_account():
    """Get account information (includes todays_win_loss and buying_power)"""
    try:
        account = trading_client.get_account()
        
        # Calculate today's P/L (todays_win_loss from AlpacaTrader)
        balance_change = float(account.equity) - float(account.last_equity)
        
        data = {
            'balance': float(account.equity),
            'lastBalance': float(account.last_equity),
            'buyingPower': float(account.buying_power),
            'cash': float(account.cash),
            'portfolioValue': float(account.portfolio_value),
            'todayPnL': balance_change,
            'status': account.status.value,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/positions', methods=['GET'])
def get_positions():
    """Get all current positions (get_positions from AlpacaTrader)"""
    try:
        positions = trading_client.get_all_positions()
        
        position_data = []
        for pos in positions:
            position_data.append({
                'symbol': pos.symbol,
                'qty': int(float(pos.qty)),
                'avgPrice': float(pos.avg_entry_price),
                'currentPrice': float(pos.current_price),
                'marketValue': float(pos.market_value),
                'pnl': float(pos.unrealized_pl),
                'pnlPercent': float(pos.unrealized_plpc) * 100,
                'side': pos.side.value
            })
        
        return jsonify({
            'positions': position_data,
            'count': len(position_data),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/positions/analysis', methods=['GET'])
def analyze_positions():
    """Analyze positions vs strong stocks (from compareSyms.py)"""
    try:
        positions = trading_client.get_all_positions()
        
        if not positions:
            return jsonify({
                'strongOverlap': [],
                'weakPositions': [],
                'totalPositions': 0,
                'stillStrong': 0,
                'noLongerStrong': 0
            })
        
        symbols = [position.symbol for position in positions]
        
        # Check overlap with strong stocks
        strong_overlap = [s for s in symbols if s in scrapeSyms.strong]
        weak_positions = [s for s in symbols if s not in scrapeSyms.strong]
        
        return jsonify({
            'strongOverlap': strong_overlap,
            'weakPositions': weak_positions,
            'totalPositions': len(symbols),
            'stillStrong': len(strong_overlap),
            'noLongerStrong': len(weak_positions),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/positions/sell-weak', methods=['POST'])
def sell_weak_positions():
    """Sell positions that are no longer strong (from compareSyms.py)"""
    try:
        positions = trading_client.get_all_positions()
        
        if not positions:
            return jsonify({
                'message': 'No positions to sell',
                'results': []
            })
        
        symbols = [position.symbol for position in positions]
        quantities = [abs(float(position.qty)) for position in positions]
        
        results = []
        sold_count = 0
        
        for i, stock in enumerate(symbols):
            if stock not in scrapeSyms.strong:
                try:
                    qty = quantities[i]
                    current_price = get_current_price(stock)
                    
                    if current_price and current_price > 1.0:
                        limit_price = round(current_price * 0.95, 2)
                    else:
                        limit_price = 1.0
                    
                    order_data = LimitOrderRequest(
                        symbol=stock,
                        qty=qty,
                        side=OrderSide.SELL,
                        time_in_force=TimeInForce.GTC,
                        limit_price=limit_price
                    )
                    
                    order = trading_client.submit_order(order_data)
                    results.append({
                        'symbol': stock,
                        'qty': qty,
                        'limitPrice': limit_price,
                        'status': 'success',
                        'orderId': order.id
                    })
                    sold_count += 1
                    
                except Exception as e:
                    results.append({
                        'symbol': stock,
                        'status': 'error',
                        'error': str(e)
                    })
        
        return jsonify({
            'results': results,
            'soldCount': sold_count,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stocks/strong', methods=['GET'])
def get_strong_stocks():
    """Get strong stocks from scrapeSyms.py"""
    try:
        stocks = []
        for idx, symbol in enumerate(scrapeSyms.strong, 1):
            # Parse symbol and name if comma-separated
            if ',' in symbol:
                parts = symbol.split(',', 1)
                sym_part = parts[0].strip()
                name_part = parts[1].strip() if len(parts) > 1 else 'Unknown'
            else:
                sym_part = symbol.strip()
                name_part = 'Unknown'
            
            stocks.append({
                'symbol': sym_part,
                'name': name_part,
                'rank': idx,
                'category': 'strong'
            })
        
        return jsonify({
            'stocks': stocks,
            'count': len(stocks),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stocks/weak', methods=['GET'])
def get_weak_stocks():
    """Get weak stocks from scrapeSyms.py"""
    try:
        stocks = []
        for idx, symbol in enumerate(scrapeSyms.weak, 1):
            # Parse symbol and name if comma-separated
            if ',' in symbol:
                parts = symbol.split(',', 1)
                sym_part = parts[0].strip()
                name_part = parts[1].strip() if len(parts) > 1 else 'Unknown'
            else:
                sym_part = symbol.strip()
                name_part = 'Unknown'
            
            stocks.append({
                'symbol': sym_part,
                'name': name_part,
                'rank': idx + 15,
                'category': 'weak'
            })
        
        return jsonify({
            'stocks': stocks,
            'count': len(stocks),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tradeable', methods=['GET'])
def get_tradeable_stocks():
    """Get tradeable stocks from strong list (is_tradeable from AlpacaTrader)"""
    try:
        trader = AlpacaTrader()
        trader.is_tradeable()
        
        return jsonify({
            'tradeable': trader.is_tradeable_lst,
            'count': len(trader.is_tradeable_lst),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scan-and-trade', methods=['POST'])
def scan_and_trade():
    """
    Scan for tradeable strong stocks and place orders
    (is_tradeable + postion_size_lst from AlpacaTrader)
    """
    try:
        trader = AlpacaTrader()
        trader.is_tradeable()
        
        results = []
        for symbol in trader.is_tradeable_lst[:10]:  # Limit to top 10
            try:
                trader.set_symbol(symbol)
                
                # Get price
                last_price = trader.get_last_price(symbol)
                if last_price is None:
                    results.append({
                        'symbol': symbol,
                        'status': 'error',
                        'error': 'Could not get price data'
                    })
                    continue
                
                # Calculate position size
                target_qty = int(trader.balance * 0.03 // last_price)
                
                if target_qty > 0:
                    trader.send_order(target_qty)
                    results.append({
                        'symbol': symbol,
                        'qty': target_qty,
                        'status': 'success'
                    })
                else:
                    results.append({
                        'symbol': symbol,
                        'status': 'skipped',
                        'reason': 'Position size too small'
                    })
                    
            except Exception as e:
                results.append({
                    'symbol': symbol,
                    'status': 'error',
                    'error': str(e)
                })
        
        return jsonify({
            'results': results,
            'total': len(results),
            'successful': len([r for r in results if r['status'] == 'success']),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard-data', methods=['GET'])
def get_dashboard_data():
    """
    Get all data needed for dashboard in one call
    Combines: account, positions, strong stocks, weak stocks, analysis
    """
    try:
        # Get account info
        account = trading_client.get_account()
        balance_change = float(account.equity) - float(account.last_equity)
        
        # Get positions
        positions = trading_client.get_all_positions()
        position_data = []
        position_symbols = []
        
        for pos in positions:
            position_symbols.append(pos.symbol)
            position_data.append({
                'symbol': pos.symbol,
                'qty': int(float(pos.qty)),
                'avgPrice': float(pos.avg_entry_price),
                'currentPrice': float(pos.current_price),
                'marketValue': float(pos.market_value),
                'pnl': float(pos.unrealized_pl),
                'pnlPercent': float(pos.unrealized_plpc) * 100,
                'side': pos.side.value,
                'status': 'strong' if pos.symbol in scrapeSyms.strong else 'weak'
            })
        
        # Analyze strong overlap
        strong_overlap = [s for s in position_symbols if s in scrapeSyms.strong]
        weak_positions = [s for s in position_symbols if s not in scrapeSyms.strong]
        
        # Parse strong stocks
        strong_stocks = []
        for idx, symbol in enumerate(scrapeSyms.strong, 1):
            if ',' in symbol:
                parts = symbol.split(',', 1)
                sym_part = parts[0].strip()
                name_part = parts[1].strip() if len(parts) > 1 else 'Unknown'
            else:
                sym_part = symbol.strip()
                name_part = 'Unknown'
            
            strong_stocks.append({
                'symbol': sym_part,
                'name': name_part,
                'rank': idx
            })
        
        # Parse weak stocks
        weak_stocks = []
        for idx, symbol in enumerate(scrapeSyms.weak, 1):
            if ',' in symbol:
                parts = symbol.split(',', 1)
                sym_part = parts[0].strip()
                name_part = parts[1].strip() if len(parts) > 1 else 'Unknown'
            else:
                sym_part = symbol.strip()
                name_part = 'Unknown'
            
            weak_stocks.append({
                'symbol': sym_part,
                'name': name_part,
                'rank': idx + 15
            })
        
        return jsonify({
            'account': {
                'balance': float(account.equity),
                'lastBalance': float(account.last_equity),
                'buyingPower': float(account.buying_power),
                'cash': float(account.cash),
                'todayPnL': balance_change
            },
            'positions': position_data,
            'analysis': {
                'totalPositions': len(position_symbols),
                'stillStrong': len(strong_overlap),
                'noLongerStrong': len(weak_positions),
                'strongOverlap': strong_overlap,
                'weakPositions': weak_positions
            },
            'strongStocks': strong_stocks,
            'weakStocks': weak_stocks,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 TrendTracker API Server Starting...")
    print("="*60)
    print(f"📊 Dashboard: http://localhost:5000")
    print(f"🔧 API Health: http://localhost:5000/api/health")
    print(f"📈 Full Data: http://localhost:5000/api/dashboard-data")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)