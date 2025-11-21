#!/usr/bin/env python3
"""
PROFESSIONAL CRYPTO BACKTESTING SYSTEM v3.0
Modular strategies, leverage support, and proper risk management
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import subprocess
import sys
import os
import importlib.util
from datetime import datetime, timedelta
import time
import traceback

# Auto-install required packages
def install_packages():
    """Install required packages automatically"""
    packages = [
        'backtrader',
        'pandas',
        'numpy',
        'ccxt',
        'requests',
        'matplotlib',
        'python-dateutil'
    ]
    
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--quiet"])

# Install packages before importing
print("🔧 Checking dependencies...")
install_packages()

import backtrader as bt
import pandas as pd
import numpy as np
import ccxt
import requests
import warnings
warnings.filterwarnings('ignore')

# ===================== BASE STRATEGY CLASS =====================

class BaseStrategy(bt.Strategy):
    """Base strategy with risk management and leverage support"""
    
    params = (
        ('printlog', False),
        ('risk_per_trade', 2.0),  # Risk 2% of account per trade
        ('leverage', 1),  # Leverage multiplier (1-125x)
        ('stop_loss_pct', 2.0),  # Stop loss percentage
        ('take_profit_pct', 6.0),  # Take profit percentage
        ('use_risk_management', True),  # Enable/disable risk management
    )
    
    def __init__(self):
        self.order = None
        self.stop_order = None
        self.profit_order = None
        self.trades_list = []
        self.trade_count = 0
        self.win_count = 0
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.dataopen = self.datas[0].open
        
        # Track entry price
        self.entry_price = None
        self.position_size = None
        
    def log(self, txt, dt=None):
        """Logging function"""
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
    
    def calculate_position_size(self):
        """Calculate position size based on risk management"""
        account_value = self.broker.getvalue()
        
        if self.params.use_risk_management:
            # Calculate position size based on risk percentage
            risk_amount = account_value * (self.params.risk_per_trade / 100)
            
            # With leverage
            effective_capital = risk_amount * self.params.leverage
            
            # Position size in units
            position_size = effective_capital / self.dataclose[0]
        else:
            # Use all available capital with leverage
            available_cash = self.broker.getcash()
            effective_capital = available_cash * self.params.leverage * 0.95  # Use 95% to avoid margin issues
            position_size = effective_capital / self.dataclose[0]
        
        return position_size
    
    def buy_signal(self):
        """Override this method in child strategies"""
        return False
    
    def sell_signal(self):
        """Override this method in child strategies"""
        return False
    
    def next(self):
        # Skip if we have pending orders
        if self.order:
            return
        
        # Check if we are in the market
        if not self.position:
            # Check for buy signal
            if self.buy_signal():
                # Calculate position size with risk management
                size = self.calculate_position_size()
                
                if size > 0:
                    self.log(f'BUY CREATE, Size: {size:.4f} @ {self.dataclose[0]:.2f} (Leverage: {self.params.leverage}x)')
                    self.order = self.buy(size=size)
                    self.entry_price = self.dataclose[0]
                    self.position_size = size
        else:
            # Check for sell signal or stop/take profit
            current_pnl_pct = ((self.dataclose[0] - self.entry_price) / self.entry_price) * 100
            
            # Check stop loss
            if self.params.use_risk_management and current_pnl_pct <= -self.params.stop_loss_pct:
                self.log(f'STOP LOSS TRIGGERED @ {self.dataclose[0]:.2f} (Loss: {current_pnl_pct:.2f}%)')
                self.order = self.close()
            
            # Check take profit
            elif self.params.use_risk_management and current_pnl_pct >= self.params.take_profit_pct:
                self.log(f'TAKE PROFIT TRIGGERED @ {self.dataclose[0]:.2f} (Profit: {current_pnl_pct:.2f}%)')
                self.order = self.close()
            
            # Check strategy sell signal
            elif self.sell_signal():
                self.log(f'SELL SIGNAL @ {self.dataclose[0]:.2f} (P/L: {current_pnl_pct:.2f}%)')
                self.order = self.close()
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}, Size: {order.executed.size:.4f}')
            else:
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}')
            
            self.bar_executed = len(self)
            
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        
        self.order = None
    
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        
        self.trade_count += 1
        if trade.pnl > 0:
            self.win_count += 1
        
        self.log(f'TRADE CLOSED, GROSS P/L: {trade.pnl:.2f}, NET P/L: {trade.pnlcomm:.2f}')
        
        self.trades_list.append({
            'profit': trade.pnl,
            'pnlcomm': trade.pnlcomm,
        })
        
        # Reset entry price
        self.entry_price = None
        self.position_size = None

# ===================== DATA HANDLING =====================

class PandasData_Fixed(bt.feeds.PandasData):
    """Fixed PandasData feed"""
    params = (
        ('datetime', None),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('openinterest', None),
    )

class DataFetcher:
    """Fetches 1 year of historical data automatically"""
    
    def __init__(self):
        self.exchanges = {}
        self._init_exchanges()
        
    def _init_exchanges(self):
        """Initialize exchange connections"""
        try:
            self.exchanges['binance'] = ccxt.binance({
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            })
            print("✅ Binance connection established")
        except Exception as e:
            print(f"⚠️ Binance connection failed: {e}")
            
    def fetch_one_year_data(self, symbol, timeframe, progress_callback=None):
        """Fetch exactly 1 year of data"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        # Try real exchange data first
        if 'binance' in self.exchanges:
            try:
                if progress_callback:
                    progress_callback("Connecting to Binance...")
                    
                exchange = self.exchanges['binance']
                
                if '/' not in symbol:
                    symbol = symbol + '/USDT'
                
                since_ms = int(start_date.timestamp() * 1000)
                until_ms = int(end_date.timestamp() * 1000)
                
                all_candles = []
                current_since = since_ms
                batch_count = 0
                
                while current_since < until_ms:
                    batch_count += 1
                    if progress_callback and batch_count % 5 == 0:
                        progress_callback(f"Fetching batch {batch_count}...")
                    
                    try:
                        candles = exchange.fetch_ohlcv(
                            symbol, timeframe, since=current_since, limit=1000
                        )
                    except:
                        break
                    
                    if not candles:
                        break
                        
                    all_candles.extend(candles)
                    
                    if len(candles) < 1000:
                        break
                        
                    current_since = candles[-1][0] + 1
                    time.sleep(exchange.rateLimit / 1000)
                
                if all_candles:
                    df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df = df.set_index('datetime')
                    df = df[['open', 'high', 'low', 'close', 'volume']]
                    df = df[(df.index >= start_date) & (df.index <= end_date)]
                    
                    for col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    df = df.dropna()
                    
                    if not df.empty:
                        if progress_callback:
                            progress_callback(f"✅ Downloaded {len(df)} candles")
                        return df
                        
            except Exception as e:
                print(f"Binance error: {e}")
        
        # Generate synthetic data as fallback
        if progress_callback:
            progress_callback("Generating synthetic data...")
        
        return self._generate_synthetic_data(symbol, timeframe, start_date, end_date)
    
    def _generate_synthetic_data(self, symbol, timeframe, start_date, end_date):
        """Generate synthetic data"""
        freq_map = {
            '1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min',
            '1h': '1H', '4h': '4H', '12h': '12H', '1d': '1D'
        }
        
        freq = freq_map.get(timeframe, '1H')
        date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
        
        # Base prices
        base_prices = {'BTC': 45000, 'ETH': 2800, 'BNB': 320, 'SOL': 100}
        coin = symbol.split('/')[0] if '/' in symbol else symbol.replace('USDT', '')
        base_price = base_prices.get(coin, 100)
        
        # Generate realistic price movement
        np.random.seed(42)
        num_periods = len(date_range)
        returns = np.random.normal(0.0001, 0.02, num_periods)
        prices = base_price * np.exp(np.cumsum(returns))
        
        # Create OHLC
        opens = prices * (1 + np.random.normal(0, 0.002, num_periods))
        highs = prices * (1 + np.abs(np.random.normal(0.003, 0.003, num_periods)))
        lows = prices * (1 - np.abs(np.random.normal(0.003, 0.003, num_periods)))
        closes = prices * (1 + np.random.normal(0, 0.002, num_periods))
        
        for i in range(num_periods):
            highs[i] = max(opens[i], closes[i], highs[i])
            lows[i] = min(opens[i], closes[i], lows[i])
        
        volumes = 1000000 * (1 + np.abs(np.random.normal(0, 0.3, num_periods)))
        
        return pd.DataFrame({
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes,
            'volume': volumes
        }, index=date_range)

# ===================== STRATEGY LOADER =====================

class StrategyLoader:
    """Dynamically load strategies from the strategies folder"""
    
    @staticmethod
    def load_strategies():
        """Load all strategy files from the strategies folder"""
        strategies = {}
        strategy_dir = os.path.join(os.path.dirname(__file__), 'strategies')
        
        # Create strategies folder if it doesn't exist
        if not os.path.exists(strategy_dir):
            os.makedirs(strategy_dir)
            print(f"Created strategies folder at: {strategy_dir}")
            return strategies
        
        # Add strategies folder to Python path
        if strategy_dir not in sys.path:
            sys.path.insert(0, strategy_dir)
        
        # Load each .py file in the strategies folder
        for filename in os.listdir(strategy_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                try:
                    # Import the module
                    module_name = filename[:-3]
                    file_path = os.path.join(strategy_dir, filename)
                    
                    spec = importlib.util.spec_from_file_location(module_name, file_path)
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module  # Add to sys.modules
                    spec.loader.exec_module(module)
                    
                    # Look for strategy class
                    for item_name in dir(module):
                        item = getattr(module, item_name)
                        if (isinstance(item, type) and 
                            issubclass(item, bt.Strategy) and 
                            item != bt.Strategy and
                            hasattr(item, 'strategy_name')):
                            
                            strategy_name = getattr(item, 'strategy_name', module_name)
                            strategies[strategy_name] = item
                            print(f"✅ Loaded strategy: {strategy_name}")
                            
                except Exception as e:
                    print(f"❌ Error loading {filename}: {e}")
                    import traceback
                    traceback.print_exc()
        
        return strategies

# ===================== GUI APPLICATION =====================

class BacktestGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Professional Crypto Backtesting System v3.0")
        self.root.geometry("1400x900")
        
        style = ttk.Style()
        style.theme_use('clam')
        
        self.data_fetcher = DataFetcher()
        self.strategies = {}
        self.load_strategies()
        
        self.setup_ui()
        
    def load_strategies(self):
        """Load strategies from the strategies folder"""
        self.strategies = StrategyLoader.load_strategies()
        if not self.strategies:
            print("⚠️ No strategies found in strategies folder")
            
    def setup_ui(self):
        """Setup the user interface"""
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(1, weight=1)
        
        # ========== LEFT PANEL ==========
        left_frame = ttk.LabelFrame(main_frame, text="📊 Configuration", padding="10")
        left_frame.grid(row=0, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        row = 0
        
        # Symbol selection
        ttk.Label(left_frame, text="Trading Pair:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.symbol_var = tk.StringVar(value="BTC/USDT")
        symbol_combo = ttk.Combobox(left_frame, textvariable=self.symbol_var, width=15)
        symbol_combo['values'] = [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT',
            'ADA/USDT', 'XRP/USDT', 'AVAX/USDT', 'MATIC/USDT'
        ]
        symbol_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Strategy selection
        ttk.Label(left_frame, text="Strategy:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.strategy_var = tk.StringVar()
        self.strategy_combo = ttk.Combobox(left_frame, textvariable=self.strategy_var, width=15)
        
        if self.strategies:
            self.strategy_combo['values'] = list(self.strategies.keys())
            self.strategy_var.set(list(self.strategies.keys())[0])
        else:
            self.strategy_combo['values'] = ['No strategies loaded']
            
        self.strategy_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Timeframe selection
        ttk.Label(left_frame, text="Timeframe:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.timeframe_var = tk.StringVar(value="1h")
        timeframe_combo = ttk.Combobox(left_frame, textvariable=self.timeframe_var, width=15)
        timeframe_combo['values'] = ['1m', '5m', '15m', '30m', '1h', '4h', '12h', '1d']
        timeframe_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Initial capital
        ttk.Label(left_frame, text="Initial Capital ($):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.capital_var = tk.StringVar(value="10000")
        capital_entry = ttk.Entry(left_frame, textvariable=self.capital_var, width=15)
        capital_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Leverage
        ttk.Label(left_frame, text="Leverage (1-125x):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.leverage_var = tk.StringVar(value="1")
        leverage_entry = ttk.Entry(left_frame, textvariable=self.leverage_var, width=15)
        leverage_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Risk per trade
        ttk.Label(left_frame, text="Risk per Trade (%):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.risk_var = tk.StringVar(value="2")
        risk_entry = ttk.Entry(left_frame, textvariable=self.risk_var, width=15)
        risk_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Stop loss
        ttk.Label(left_frame, text="Stop Loss (%):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.stoploss_var = tk.StringVar(value="2")
        stoploss_entry = ttk.Entry(left_frame, textvariable=self.stoploss_var, width=15)
        stoploss_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Take profit
        ttk.Label(left_frame, text="Take Profit (%):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.takeprofit_var = tk.StringVar(value="6")
        takeprofit_entry = ttk.Entry(left_frame, textvariable=self.takeprofit_var, width=15)
        takeprofit_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Commission
        ttk.Label(left_frame, text="Commission (%):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.commission_var = tk.StringVar(value="0.1")
        commission_entry = ttk.Entry(left_frame, textvariable=self.commission_var, width=15)
        commission_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Use risk management checkbox
        self.use_risk_var = tk.BooleanVar(value=True)
        risk_check = ttk.Checkbutton(left_frame, text="Use Risk Management", variable=self.use_risk_var)
        risk_check.grid(row=row, column=0, columnspan=2, pady=10)
        row += 1
        
        # Status label
        self.status_label = ttk.Label(left_frame, text="Ready", foreground="green")
        self.status_label.grid(row=row, column=0, columnspan=2, pady=10)
        row += 1
        
        # Progress bar
        self.progress = ttk.Progressbar(left_frame, mode='indeterminate')
        self.progress.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Buttons
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=10)
        
        self.run_button = ttk.Button(
            button_frame, 
            text="🚀 Run Backtest",
            command=self.run_backtest
        )
        self.run_button.grid(row=0, column=0, padx=5)
        
        self.compare_button = ttk.Button(
            button_frame,
            text="📊 Test All Timeframes",
            command=self.test_all_timeframes
        )
        self.compare_button.grid(row=0, column=1, padx=5)
        
        # Reload strategies button
        reload_button = ttk.Button(
            button_frame,
            text="🔄 Reload Strategies",
            command=self.reload_strategies
        )
        reload_button.grid(row=1, column=0, columnspan=2, pady=5)
        
        # ========== TOP RIGHT PANEL - Results ==========
        top_right_frame = ttk.LabelFrame(main_frame, text="📈 Results", padding="10")
        top_right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5))
        
        # Results text area
        self.results_text = scrolledtext.ScrolledText(
            top_right_frame,
            width=70,
            height=20,
            wrap=tk.WORD,
            font=('Courier', 10)
        )
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure text tags
        self.results_text.tag_config('header', font=('Courier', 12, 'bold'))
        self.results_text.tag_config('profit', foreground='green')
        self.results_text.tag_config('loss', foreground='red')
        self.results_text.tag_config('info', foreground='blue')
        
        # ========== BOTTOM RIGHT PANEL - Comparison Table ==========
        bottom_right_frame = ttk.LabelFrame(main_frame, text="📊 Timeframe Comparison", padding="10")
        bottom_right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create treeview
        columns = ('Timeframe', 'Total Return', 'Win Rate', 'Trades', 'Sharpe', 'Max DD', 'Final Value')
        self.tree = ttk.Treeview(bottom_right_frame, columns=columns, show='headings', height=15)
        
        # Define headings
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(bottom_right_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Summary label
        self.summary_label = ttk.Label(bottom_right_frame, text="", font=('', 10))
        self.summary_label.grid(row=1, column=0, columnspan=2, pady=10)
        
    def reload_strategies(self):
        """Reload strategies from folder"""
        self.strategies = StrategyLoader.load_strategies()
        if self.strategies:
            self.strategy_combo['values'] = list(self.strategies.keys())
            self.strategy_var.set(list(self.strategies.keys())[0])
            self.update_status("Strategies reloaded!", 'green')
        else:
            self.update_status("No strategies found", 'red')
            
    def update_status(self, message, color='black'):
        """Update status label"""
        self.status_label.config(text=message, foreground=color)
        self.root.update()
        
    def run_backtest(self):
        """Run a single backtest"""
        if not self.strategies:
            messagebox.showerror("Error", "No strategies loaded!")
            return
            
        self.run_button.config(state='disabled')
        self.compare_button.config(state='disabled')
        self.progress.start()
        
        thread = threading.Thread(target=self._run_backtest_thread)
        thread.daemon = True
        thread.start()
        
    def _run_backtest_thread(self):
        """Run backtest in separate thread"""
        try:
            # Get parameters
            symbol = self.symbol_var.get()
            strategy_name = self.strategy_var.get()
            timeframe = self.timeframe_var.get()
            initial_capital = float(self.capital_var.get())
            leverage = int(self.leverage_var.get())
            risk_per_trade = float(self.risk_var.get())
            stop_loss = float(self.stoploss_var.get())
            take_profit = float(self.takeprofit_var.get())
            commission = float(self.commission_var.get()) / 100
            use_risk_mgmt = self.use_risk_var.get()
            
            # Validate leverage
            if leverage < 1 or leverage > 125:
                self.update_status("Leverage must be between 1 and 125", 'red')
                return
            
            # Update status
            self.update_status(f"Fetching {timeframe} data for {symbol}...", 'blue')
            
            # Fetch data
            df = self.data_fetcher.fetch_one_year_data(
                symbol, timeframe,
                progress_callback=lambda msg: self.update_status(msg, 'blue')
            )
            
            if df is None or df.empty:
                self.update_status("No data available", 'red')
                return
                
            self.update_status(f"Running backtest with {leverage}x leverage...", 'blue')
            
            # Setup backtrader
            cerebro = bt.Cerebro()
            
            # Add data
            data = PandasData_Fixed(dataname=df)
            cerebro.adddata(data)
            
            # Add strategy with parameters
            strategy_class = self.strategies[strategy_name]
            cerebro.addstrategy(
                strategy_class,
                printlog=False,
                leverage=leverage,
                risk_per_trade=risk_per_trade,
                stop_loss_pct=stop_loss,
                take_profit_pct=take_profit,
                use_risk_management=use_risk_mgmt
            )
            
            # Broker settings
            cerebro.broker.setcash(initial_capital)
            cerebro.broker.setcommission(commission=commission)
            
            # Add analyzers
            cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
            cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0)
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
            cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
            
            # Run backtest
            results = cerebro.run()
            
            # Get results
            strat = results[0]
            final_value = cerebro.broker.getvalue()
            total_return = (final_value - initial_capital) / initial_capital * 100
            
            # Display results
            self.display_results(
                strategy_name, symbol, timeframe, 
                initial_capital, final_value, total_return,
                strat, df, leverage, risk_per_trade
            )
            
            status_color = 'green' if total_return > 0 else 'red'
            self.update_status(f"✅ Complete! Return: {total_return:.2f}% (Leverage: {leverage}x)", status_color)
            
        except Exception as e:
            print(f"Error: {traceback.format_exc()}")
            self.update_status(f"Error: {str(e)[:100]}", 'red')
            messagebox.showerror("Error", str(e))
        finally:
            self.progress.stop()
            self.run_button.config(state='normal')
            self.compare_button.config(state='normal')
            
    def display_results(self, strategy, symbol, timeframe, initial, final, return_pct, strat, df, leverage, risk):
        """Display backtest results"""
        self.results_text.delete('1.0', tk.END)
        
        # Header
        self.results_text.insert(tk.END, "="*60 + "\n", 'header')
        self.results_text.insert(tk.END, f"BACKTEST RESULTS - {strategy}\n", 'header')
        self.results_text.insert(tk.END, "="*60 + "\n\n", 'header')
        
        # Basic info
        self.results_text.insert(tk.END, f"Symbol: {symbol}\n")
        self.results_text.insert(tk.END, f"Timeframe: {timeframe}\n")
        self.results_text.insert(tk.END, f"Leverage: {leverage}x\n", 'info')
        self.results_text.insert(tk.END, f"Risk per Trade: {risk}%\n", 'info')
        self.results_text.insert(tk.END, f"Total Candles: {len(df):,}\n")
        self.results_text.insert(tk.END, f"Date Range: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}\n\n")
        
        # Financial metrics
        self.results_text.insert(tk.END, "💰 FINANCIAL METRICS\n", 'header')
        self.results_text.insert(tk.END, "-"*40 + "\n")
        self.results_text.insert(tk.END, f"Initial Capital: ${initial:,.2f}\n")
        self.results_text.insert(tk.END, f"Final Value: ${final:,.2f}\n")
        
        if return_pct >= 0:
            self.results_text.insert(tk.END, f"Total Return: +{return_pct:.2f}%\n", 'profit')
            self.results_text.insert(tk.END, f"Net Profit: +${final - initial:,.2f}\n\n", 'profit')
        else:
            self.results_text.insert(tk.END, f"Total Return: {return_pct:.2f}%\n", 'loss')
            self.results_text.insert(tk.END, f"Net Loss: ${abs(final - initial):,.2f}\n\n", 'loss')
        
        # Trade statistics
        if hasattr(strat, 'trade_count'):
            self.results_text.insert(tk.END, "📊 TRADING STATISTICS\n", 'header')
            self.results_text.insert(tk.END, "-"*40 + "\n")
            self.results_text.insert(tk.END, f"Total Trades: {strat.trade_count}\n")
            
            if strat.trade_count > 0:
                self.results_text.insert(tk.END, f"Winning Trades: {strat.win_count}\n", 'profit')
                self.results_text.insert(tk.END, f"Losing Trades: {strat.trade_count - strat.win_count}\n", 'loss')
                win_rate = (strat.win_count / strat.trade_count) * 100
                self.results_text.insert(tk.END, f"Win Rate: {win_rate:.1f}%\n", 'info')
        
        # Risk metrics
        self.results_text.insert(tk.END, "\n📉 RISK METRICS\n", 'header')
        self.results_text.insert(tk.END, "-"*40 + "\n")
        
        if hasattr(strat.analyzers, 'sharpe'):
            sharpe = strat.analyzers.sharpe.get_analysis()
            if sharpe.get('sharperatio'):
                self.results_text.insert(tk.END, f"Sharpe Ratio: {sharpe['sharperatio']:.2f}\n", 'info')
                
        if hasattr(strat.analyzers, 'drawdown'):
            dd = strat.analyzers.drawdown.get_analysis()
            max_dd = dd.get('max', {}).get('drawdown', 0)
            self.results_text.insert(tk.END, f"Max Drawdown: {max_dd:.2f}%\n", 'loss')
            
    def test_all_timeframes(self):
        """Test strategy on all timeframes"""
        if not self.strategies:
            messagebox.showerror("Error", "No strategies loaded!")
            return
            
        self.run_button.config(state='disabled')
        self.compare_button.config(state='disabled')
        self.progress.start()
        
        # Clear table
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        thread = threading.Thread(target=self._test_all_timeframes_thread)
        thread.daemon = True
        thread.start()
        
    def _test_all_timeframes_thread(self):
        """Test all timeframes in separate thread"""
        try:
            # Get parameters
            symbol = self.symbol_var.get()
            strategy_name = self.strategy_var.get()
            initial_capital = float(self.capital_var.get())
            leverage = int(self.leverage_var.get())
            risk_per_trade = float(self.risk_var.get())
            stop_loss = float(self.stoploss_var.get())
            take_profit = float(self.takeprofit_var.get())
            commission = float(self.commission_var.get()) / 100
            use_risk_mgmt = self.use_risk_var.get()
            
            timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '12h', '1d']
            results = []
            
            for tf in timeframes:
                try:
                    self.update_status(f"Testing {tf} timeframe...", 'blue')
                    
                    # Fetch data
                    df = self.data_fetcher.fetch_one_year_data(
                        symbol, tf,
                        progress_callback=lambda msg: self.update_status(f"{tf}: {msg}", 'blue')
                    )
                    
                    if df is None or df.empty:
                        continue
                    
                    # Run backtest
                    cerebro = bt.Cerebro()
                    data = PandasData_Fixed(dataname=df)
                    cerebro.adddata(data)
                    
                    strategy_class = self.strategies[strategy_name]
                    cerebro.addstrategy(
                        strategy_class,
                        printlog=False,
                        leverage=leverage,
                        risk_per_trade=risk_per_trade,
                        stop_loss_pct=stop_loss,
                        take_profit_pct=take_profit,
                        use_risk_management=use_risk_mgmt
                    )
                    
                    cerebro.broker.setcash(initial_capital)
                    cerebro.broker.setcommission(commission=commission)
                    
                    # Add analyzers
                    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
                    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0)
                    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
                    
                    # Run
                    result = cerebro.run()
                    strat = result[0]
                    
                    # Get metrics
                    final_value = cerebro.broker.getvalue()
                    total_return = (final_value - initial_capital) / initial_capital * 100
                    
                    trade_count = strat.trade_count if hasattr(strat, 'trade_count') else 0
                    win_count = strat.win_count if hasattr(strat, 'win_count') else 0
                    win_rate = (win_count / trade_count * 100) if trade_count > 0 else 0
                    
                    sharpe_analysis = strat.analyzers.sharpe.get_analysis()
                    sharpe = sharpe_analysis.get('sharperatio', 0)
                    
                    dd_analysis = strat.analyzers.drawdown.get_analysis()
                    max_dd = dd_analysis.get('max', {}).get('drawdown', 0)
                    
                    # Store results
                    results.append({
                        'timeframe': tf,
                        'return': total_return,
                        'win_rate': win_rate,
                        'trades': trade_count,
                        'sharpe': sharpe if sharpe else 0,
                        'max_dd': max_dd,
                        'final_value': final_value
                    })
                    
                    # Add to tree
                    self.tree.insert('', tk.END, values=(
                        tf,
                        f"{total_return:.2f}%",
                        f"{win_rate:.1f}%",
                        trade_count,
                        f"{sharpe:.2f}" if sharpe else "N/A",
                        f"{max_dd:.2f}%",
                        f"${final_value:,.2f}"
                    ))
                    
                except Exception as e:
                    print(f"Error testing {tf}: {e}")
                    continue
                    
            # Find best timeframe
            if results:
                best = max(results, key=lambda x: x['return'])
                self.summary_label.config(
                    text=f"🏆 Best: {best['timeframe']} with {best['return']:.2f}% return (Leverage: {leverage}x)",
                    foreground='green'
                )
                
            self.update_status("✅ All timeframes tested!", 'green')
            
        except Exception as e:
            print(f"Error: {traceback.format_exc()}")
            self.update_status(f"Error: {str(e)[:100]}", 'red')
        finally:
            self.progress.stop()
            self.run_button.config(state='normal')
            self.compare_button.config(state='normal')

def main():
    """Main application entry point"""
    
    # Create strategies folder if it doesn't exist
    strategy_dir = os.path.join(os.path.dirname(__file__), 'strategies')
    if not os.path.exists(strategy_dir):
        os.makedirs(strategy_dir)
        print(f"Created strategies folder at: {strategy_dir}")
    
    root = tk.Tk()
    app = BacktestGUI(root)
    root.mainloop()

if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════╗
    ║  PROFESSIONAL BACKTESTING SYSTEM v3.0  ║
    ║     Modular Strategies & Leverage      ║
    ╚════════════════════════════════════════╝
    """)
    main()
