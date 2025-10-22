"""
TrendTracker Flask API
Connects the Alpaca trading bot to the web dashboard
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
from datetime import datetime
import alpaca_trade_api as tradeapi

# IMPORTANT: Move these to environment variables!
API_KEY = os.getenv('ALPACA_API_KEY', 'YOUR_KEY_HERE')
SECRET_KEY = os.getenv('ALPACA_SECRET_KEY', 'YOUR_SECRET_HERE')
BASE_URL = 'https://paper-api.alpaca.markets'

app = Flask(__name__, static_folder='.')
CORS(app)

# Initialize Alpaca API
api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL, api_version='v2')

@app.route('/')
def index():
    """Serve the dashboard"""
    return send_from_directory('.', 'index.html')

@app.route('/api/account', methods=['GET'])
def get_account():
    """Get account information"""
    try:
        account = api.get_account()
        
        data = {
            'balance': float(account.equity),
            'lastBalance': float(account.last_equity),
            'buyingPower': float(account.buying_power),
            'cash': float(account.cash),
            'portfolioValue': float(account.portfolio_value),
            'todayPnL': float(account.equity) - float(account.last_equity),
            'status': account.status,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/positions', methods=['GET'])
def get_positions():
    """Get all current positions"""
    try:
        positions = api.list_positions()
        
        position_data = []
        for pos in positions:
            position_data.append({
                'symbol': pos.symbol,
                'qty': int(pos.qty),
                'avgPrice': float(pos.avg_entry_price),
                'currentPrice': float(pos.current_price),
                'marketValue': float(pos.market_value),
                'pnl': float(pos.unrealized_pl),
                'pnlPercent': float(pos.unrealized_plpc) * 100,
                'side': pos.side
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
    """Get strong stocks from Seykota scraper"""
    try:
        import scrapeSyms
        
        stocks = []
        for idx, symbol in enumerate(scrapeSyms.strong, 1):
            stocks.append({
                'symbol': symbol,
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
    """Get weak stocks from Seykota scraper"""
    try:
        import scrapeSyms
        
        stocks = []
        for idx, symbol in enumerate(scrapeSyms.weak, 1):
            stocks.append({
                'symbol': symbol,
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