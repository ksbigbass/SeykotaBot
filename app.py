from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
from datetime import datetime
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
import scrapeSyms
import compareSyms 
from AlpacaTrader import Trader  

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv('ALPACA_API_KEY')
SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')

app = Flask(__name__, static_folder='.')
CORS(app)

# Initialize Alpaca API with new SDK
trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
data_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

@app.route('/')
def index():
    """Serve the dashboard"""
    return send_from_directory('.', 'index.html')

@app.route('/api/account', methods=['GET'])
def get_account():
    """Get account information"""
    try:
        account = trading_client.get_account()
        
        data = {
            'balance': float(account.equity),
            'lastBalance': float(account.last_equity),
            'buyingPower': float(account.buying_power),
            'cash': float(account.cash),
            'portfolioValue': float(account.portfolio_value),
            'todayPnL': float(account.equity) - float(account.last_equity),
            'status': account.status.value,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/positions', methods=['GET'])
def get_positions():
    """Get all current positions"""
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

@app.route('/api/stocks/strong', methods=['GET'])
def get_strong_stocks():
    """Get strong stocks from integrated scraper and comparison"""
    try:
        # Integrate: Scrape, compare, and initialize trader
        symbols = scrapeSyms.strongDf
        strong_stocks, weak_stocks = scrapeSyms(symbols)
        trader = Trader()
        trader.set_stocks(strong_stocks, weak_stocks)
        
        stocks = []
        for idx, symbol in enumerate(strong_stocks, 1):
            # Parse symbol and name
            if ',' in symbol:
                sym_part = symbol.split(',')[0].strip()
                name_part = symbol.split(',')[1].strip() if len(symbol.split(',')) > 1 else 'Unknown'
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
    """Get weak stocks from integrated scraper and comparison"""
    try:
        # Integrate: Scrape, compare, and initialize trader
        symbols = scrapeSyms.weakDf
        strong_stocks, weak_stocks = scrapeSyms(symbols)
        trader = Trader()
        trader.set_stocks(strong_stocks, weak_stocks)
        
        stocks = []
        for idx, symbol in enumerate(weak_stocks, 1):
            # Parse symbol and name
            if ',' in symbol:
                sym_part = symbol.split(',')[0].strip()
                name_part = symbol.split(',')[1].strip() if len(symbol.split(',')) > 1 else 'Unknown'
            else:
                sym_part = symbol.strip()
                name_part = 'Unknown'
            
            stocks.append({
                'symbol': sym_part,
                'name': name_part,
                'rank': idx + 15,  # Weak stocks start at rank 16
                'category': 'weak'
            })
        
        return jsonify({
            'stocks': stocks,
            'count': len(stocks),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scan', methods=['POST'])
def scan_and_trade():
    """Scan for strong stocks and place orders"""
    try:
        from AlpacaTrader import AlpacaTrader
        
        trader = AlpacaTrader()
        trader.is_tradeable()
        
        # Get tradeable stocks
        tradeable = trader.is_tradeable_lst
        
        # Place orders for tradeable strong stocks
        results = []
        for symbol in tradeable[:10]:  # Limit to top 10 to avoid over-trading
            try:
                trader.set_symbol(symbol)
                trader.postion_size()
                results.append({
                    'symbol': symbol,
                    'status': 'order_placed',
                    'success': True
                })
            except Exception as e:
                results.append({
                    'symbol': symbol,
                    'status': 'error',
                    'error': str(e),
                    'success': False
                })
        
        return jsonify({
            'results': results,
            'total': len(results),
            'successful': len([r for r in results if r['success']]),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("Starting TrendTracker API...")
    print(f"Dashboard: http://localhost:5000")
    print(f"API Docs: http://localhost:5000/api/health")
    app.run(debug=True, host='0.0.0.0', port=5000)