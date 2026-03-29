"""
app.py – Flask REST API for the backtesting platform with MT5 integration.

Endpoints
---------
GET /api/status
    Returns MT5 connection status and account info

GET /api/symbols
    Returns list of available trading symbols from MT5

POST /api/backtest
    Accepts JSON with:
      - strategy_code  : Python strategy code
      - symbol         : Trading symbol (e.g., "EURUSD")
      - timeframe      : Timeframe (M1, H1, D1, etc.)
      - start_date     : Start date (YYYY-MM-DD)
      - end_date       : End date (YYYY-MM-DD)
      - initial_capital: Starting capital in USD
      - position_size  : Lot size (e.g., 0.01)

GET /
    Serves the frontend HTML file.
"""

import os
import sys
import traceback
from datetime import datetime
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from config import login_credentials, BACKTEST_CONFIG

# ==================== FLASK SETUP ====================
app = Flask(__name__, template_folder='frontend', static_folder='frontend')
CORS(app)

# ==================== MT5 INITIALIZATION ====================
mt5_initialized = False

def initialize_mt5():
    """Initialize connection to MetaTrader5"""
    global mt5_initialized
    
    try:
        # Initialize MT5
        if not mt5.initialize(
            login=int(login_credentials['username']),
            password=login_credentials['password'],
            server=login_credentials['server']
        ):
            error = mt5.last_error()
            print(f"❌ MT5 initialization failed: {error}")
            return False
        
        mt5_initialized = True
        account_info = mt5.account_info()
        print(f"✅ MT5 Connected!")
        print(f"   Account: {account_info.login}")
        print(f"   Server: {account_info.server}")
        print(f"   Balance: ${account_info.balance:.2f}")
        return True
        
    except Exception as e:
        print(f"❌ MT5 Error: {e}")
        traceback.print_exc()
        return False

# ==================== ROUTES ====================

# Serve Frontend
@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')

@app.route('/frontend/<path:filename>')
def serve_frontend(filename):
    """Serve frontend static files (CSS, JS)"""
    return send_from_directory('frontend', filename)

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve CSS and JS from root or frontend folder"""
    if os.path.exists(os.path.join('frontend', filename)):
        return send_from_directory('frontend', filename)
    return jsonify({'error': 'File not found'}), 404

# API: Status Check
@app.route('/api/status', methods=['GET'])
def get_status():
    """Check MT5 connection status"""
    try:
        if not mt5_initialized:
            return jsonify({
                'status': 'disconnected',
                'message': 'MT5 not initialized',
                'account_balance': 0
            }), 500
        
        account_info = mt5.account_info()
        if not account_info:
            return jsonify({
                'status': 'disconnected',
                'message': 'Cannot retrieve account info',
                'account_balance': 0
            }), 500
        
        return jsonify({
            'status': 'connected',
            'account_number': account_info.login,
            'account_balance': account_info.balance,
            'server': account_info.server,
            'currency': account_info.currency
        }), 200
        
    except Exception as e:
        print(f"Error in /api/status: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'account_balance': 0
        }), 500

# API: Get Available Symbols
@app.route('/api/symbols', methods=['GET'])
def get_symbols():
    """Get list of available trading symbols from MT5"""
    try:
        if not mt5_initialized:
            return jsonify({
                'symbols': [],
                'message': 'MT5 not initialized'
            }), 500
        
        # Get all symbols from MT5
        symbols = mt5.symbols_get()
        
        if not symbols:
            return jsonify({
                'symbols': [],
                'message': 'No symbols available'
            }), 200
        
        # Extract symbol names
        symbol_names = [s.name for s in symbols]
        symbol_names.sort()
        
        print(f"✅ Loaded {len(symbol_names)} symbols from MT5")
        
        return jsonify({
            'symbols': symbol_names,
            'count': len(symbol_names)
        }), 200
        
    except Exception as e:
        print(f"Error in /api/symbols: {e}")
        traceback.print_exc()
        return jsonify({
            'symbols': [],
            'error': str(e)
        }), 500

# API: Run Backtest
@app.route('/api/backtest', methods=['POST'])
def run_backtest():
    """Execute a backtest with user-provided strategy"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Extract parameters
        strategy_code = data.get('strategy_code', '')
        symbol = data.get('symbol', '')
        timeframe = data.get('timeframe', 'H1')
        start_date = data.get('start_date', '')
        end_date = data.get('end_date', '')
        initial_capital = float(data.get('initial_capital', 1000))
        position_size = float(data.get('position_size', 0.01))
        
        # Validate inputs
        if not strategy_code:
            return jsonify({'error': 'Strategy code is required'}), 400
        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400
        if not start_date or not end_date:
            return jsonify({'error': 'Start and end dates are required'}), 400
        
        # Validate MT5 connection
        if not mt5_initialized:
            return jsonify({'error': 'MT5 not connected'}), 500
        
        print(f"\n{'='*60}")
        print(f"Running backtest: {symbol} {timeframe}")
        print(f"Period: {start_date} to {end_date}")
        print(f"Initial Capital: ${initial_capital:.2f}")
        print(f"Position Size: {position_size} lots")
        print(f"{'='*60}\n")
        
        # Convert timeframe to MT5 constant
        timeframe_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
            'W1': mt5.TIMEFRAME_W1,
            'MN': mt5.TIMEFRAME_MN1,
        }
        
        mt5_timeframe = timeframe_map.get(timeframe, mt5.TIMEFRAME_H1)
        
        # Parse dates
        from_date = datetime.strptime(start_date, '%Y-%m-%d')
        to_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Get OHLC data from MT5
        print(f"📊 Fetching data from MT5...")
        rates = mt5.copy_rates_range(symbol, mt5_timeframe, from_date, to_date)
        
        if rates is None or len(rates) == 0:
            return jsonify({
                'error': f'No data found for {symbol} from {start_date} to {end_date}. Check symbol name and availability.'
            }), 400
        
        # Convert to DataFrame
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df = df[['time', 'open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume']]
        df.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Spread', 'RealVolume']
        
        print(f"✅ Fetched {len(df)} candles")
        print(f"   First: {df.iloc[0]['Time']}")
        print(f"   Last: {df.iloc[-1]['Time']}")
        print(f"   Price range: {df['Low'].min():.5f} - {df['High'].max():.5f}\n")
        
        # Execute strategy
        print(f"🔄 Executing strategy...")
        
        # Create namespace for strategy execution
        namespace = {
            'pd': pd,
            'np': np,
            'df': df,
            'ohlc_data': df[['Open', 'High', 'Low', 'Close', 'Volume']]
        }
        
        # Execute strategy code
        try:
            exec(strategy_code, namespace)
        except Exception as e:
            return jsonify({
                'error': f'Strategy execution error: {str(e)}'
            }), 400
        
        # Get signals from strategy
        if 'generate_signals' not in namespace:
            return jsonify({
                'error': 'Strategy must define generate_signals() function'
            }), 400
        
        generate_signals = namespace['generate_signals']
        signals = generate_signals(df[['Open', 'High', 'Low', 'Close', 'Volume']])
        
        # Run backtest simulation with CORRECT P&L calculation
        print(f"📈 Simulating trades...\n")
        
        capital = initial_capital
        position = 0  # 0 = no position, 1 = long, -1 = short
        entry_price = 0
        trades = []
        equity_curve = [capital]
        
        for i in range(1, len(df)):
            signal = signals[i] if i < len(signals) else 0
            current_price = df.iloc[i]['Close']
            
            # Entry logic
            if signal == 1 and position == 0:  # BUY signal
                entry_price = current_price
                position = 1
                print(f"📈 BUY @ {entry_price:.5f} (Bar {i})")
            
            elif signal == -1 and position == 0:  # SELL signal
                entry_price = current_price
                position = -1
                print(f"📉 SELL @ {entry_price:.5f} (Bar {i})")
            
            # Exit logic
            elif position != 0 and signal == 0:  # CLOSE signal
                exit_price = current_price
                
                # Calculate P&L CORRECTLY
                if position == 1:  # Long position
                    pnl_per_unit = exit_price - entry_price
                    pnl = pnl_per_unit * position_size * 100000  # Standard forex lot = 100,000 units
                    pnl_pct = ((exit_price - entry_price) / entry_price) * 100
                else:  # Short position
                    pnl_per_unit = entry_price - exit_price
                    pnl = pnl_per_unit * position_size * 100000
                    pnl_pct = ((entry_price - exit_price) / entry_price) * 100
                
                capital += pnl
                trades.append({
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'position_type': 'LONG' if position == 1 else 'SHORT'
                })
                
                print(f"❌ CLOSE @ {exit_price:.5f} | P&L: ${pnl:.2f} ({pnl_pct:+.2f}%)")
                position = 0
            
            equity_curve.append(capital)
        
        # Close any open position at end of backtest
        if position != 0:
            exit_price = df.iloc[-1]['Close']
            if position == 1:  # Long position
                pnl_per_unit = exit_price - entry_price
                pnl = pnl_per_unit * position_size * 100000
            else:  # Short position
                pnl_per_unit = entry_price - exit_price
                pnl = pnl_per_unit * position_size * 100000
            
            capital += pnl
            print(f"❌ CLOSE (Final) @ {exit_price:.5f} | P&L: ${pnl:.2f}")
        
        # Calculate statistics
        final_value = capital
        net_pnl = final_value - initial_capital
        total_return = (net_pnl / initial_capital) * 100 if initial_capital > 0 else 0
        
        total_trades = len(trades)
        wins = len([t for t in trades if t['pnl'] > 0])
        losses = len([t for t in trades if t['pnl'] < 0])
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate Max Drawdown
        max_drawdown = 0
        peak = initial_capital
        for eq in equity_curve:
            if eq > peak:
                peak = eq
            drawdown = ((peak - eq) / peak) * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Calculate Sharpe Ratio (annualized)
        returns = []
        for i in range(1, len(equity_curve)):
            if equity_curve[i-1] != 0:
                ret = (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1]
                returns.append(ret)
        
        if len(returns) > 0 and np.std(returns) > 0:
            sharpe_ratio = np.sqrt(252) * (np.mean(returns) / np.std(returns))
        else:
            sharpe_ratio = 0
        
        print(f"\n{'='*60}")
        print(f"RESULTS SUMMARY")
        print(f"{'='*60}")
        print(f"Total Trades: {total_trades}")
        print(f"Wins: {wins} | Losses: {losses}")
        print(f"Win Rate: {win_rate:.1f}%")
        print(f"Net P&L: ${net_pnl:.2f}")
        print(f"Total Return: {total_return:.2f}%")
        print(f"Max Drawdown: {max_drawdown:.2f}%")
        print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
        print(f"{'='*60}\n")
        
        return jsonify({
            'starting_capital': initial_capital,
            'final_value': final_value,
            'net_pnl': net_pnl,
            'total_return': total_return,
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'trades': trades
        }), 200
        
    except Exception as e:
        print(f"❌ Backtest error: {e}")
        traceback.print_exc()
        return jsonify({
            'error': f'Backtest failed: {str(e)}'
        }), 500

# ==================== ERROR HANDLERS ====================
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ==================== MAIN ====================
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 BACKTESTING TRADING PLATFORM - STARTING UP")
    print("="*60)
    
    # Initialize MT5
    if not initialize_mt5():
        print("⚠️  WARNING: MT5 not connected!")
        print("   The API will return errors until MT5 is connected.")
    
    print("\n📡 Starting Flask server...")
    print(f"   URL: http://localhost:5000")
    print(f"   Press Ctrl+C to stop\n")
    
    # Start Flask
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        use_reloader=False
    )