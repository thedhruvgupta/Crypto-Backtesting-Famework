# 🚀 Professional Crypto Backtesting System v3.0

## Features

### ✅ What's New
- **Modular Strategy System** - Each strategy in its own file
- **Leverage Support** - 1x to 125x leverage
- **Risk Management** - Control position size (% of account per trade)
- **Stop Loss & Take Profit** - Automatic risk controls
- **Professional Strategies** - Advanced indicators and logic
- **Easy to Extend** - Just drop new strategy files in the folder

## 📁 File Structure

```
backtest_pro.py              # Main GUI application
strategies/
├── base_strategy.py         # Base class (inherit from this)
├── sma_strategy.py          # SMA Crossover
├── rsi_strategy.py          # RSI with dynamic levels
├── macd_strategy.py         # MACD with histogram
├── bollinger_strategy.py    # Bollinger Bands with squeeze
├── scalping_strategy.py     # High-frequency scalping
└── grid_strategy.py         # Grid trading for ranges
```

## 🚀 Quick Start

```bash
python backtest_pro.py
```

## 💡 Key Features

### Leverage & Risk Management
- **Leverage**: 1x to 125x (like real exchanges)
- **Risk per Trade**: Default 2% (adjustable)
- **Stop Loss**: Automatic stop at X%
- **Take Profit**: Automatic profit taking

### Example Settings
- **Conservative**: 1-3x leverage, 1-2% risk
- **Moderate**: 5-10x leverage, 2-3% risk  
- **Aggressive**: 20-50x leverage, 3-5% risk
- **Degen**: 100-125x leverage, 5-10% risk

## 📝 Adding New Strategies

### Step 1: Create a new file in `strategies/` folder

```python
# strategies/my_strategy.py

from base_strategy import BaseStrategy
import backtrader as bt

class MyStrategy(BaseStrategy):
    
    strategy_name = "My Custom Strategy"  # This appears in dropdown
    
    params = (
        # Add your custom parameters here
        ('my_param', 20),
        # Keep these for risk management
        ('printlog', False),
        ('risk_per_trade', 2.0),
        ('leverage', 1),
        ('stop_loss_pct', 2.0),
        ('take_profit_pct', 6.0),
        ('use_risk_management', True),
    )
    
    def __init__(self):
        super().__init__()
        # Initialize your indicators here
        self.sma = bt.indicators.SMA(self.dataclose, period=self.params.my_param)
    
    def buy_signal(self):
        # Return True when you want to buy
        return self.dataclose[0] > self.sma[0]
    
    def sell_signal(self):
        # Return True when you want to sell
        return self.dataclose[0] < self.sma[0]
```

### Step 2: Click "Reload Strategies" in the GUI

That's it! Your strategy appears in the dropdown.

## 🎯 Strategy Descriptions

### SMA Crossover
- Classic moving average crossover
- Best for: Trending markets
- Timeframes: 1h, 4h, 1d

### RSI Dynamic
- RSI with dynamic exit levels
- Best for: Ranging markets
- Timeframes: 15m, 30m, 1h

### MACD Advanced
- MACD with histogram confirmation
- Best for: Momentum trading
- Timeframes: 30m, 1h, 4h

### Bollinger Bands Pro
- Mean reversion with squeeze detection
- Best for: Volatile markets
- Timeframes: 15m, 1h, 4h

### Scalper Pro
- High-frequency with tight stops
- Best for: 1m, 5m charts
- Use 10-20x leverage

### Grid Trading
- Automated grid with dynamic levels
- Best for: Sideways markets
- Timeframes: 5m, 15m, 30m

## ⚙️ Recommended Settings

### For Scalping (1m-5m)
```
Strategy: Scalper Pro
Leverage: 10-20x
Risk per Trade: 1%
Stop Loss: 0.5%
Take Profit: 1%
```

### For Day Trading (15m-1h)
```
Strategy: RSI Dynamic / MACD
Leverage: 5-10x
Risk per Trade: 2%
Stop Loss: 2%
Take Profit: 4-6%
```

### For Swing Trading (4h-1d)
```
Strategy: SMA Crossover / MACD
Leverage: 2-5x
Risk per Trade: 2-3%
Stop Loss: 3%
Take Profit: 10%
```

## 📊 Understanding Results

### With Leverage
- **10x leverage + 10% gain = 100% profit**
- **10x leverage + 10% loss = 100% loss**
- Higher leverage = higher risk/reward

### Risk Management
- **2% risk** = Maximum 50 trades to blow account
- **5% risk** = Maximum 20 trades to blow account
- Always use stop losses with leverage!

## 🔥 Pro Tips

1. **Start with low leverage** (1-5x) until profitable
2. **Backtest all timeframes** to find the best
3. **Use risk management** - Never risk more than 5%
4. **Different strategies for different markets**:
   - Trending → SMA, MACD
   - Ranging → RSI, Bollinger, Grid
   - Volatile → Scalper
5. **Combine strategies** - Use different strategies for different pairs

## ⚠️ Warnings

- **Leverage amplifies losses** - 10x leverage means 10x losses too
- **Past performance ≠ future results**
- **Test on paper trading first**
- **Never trade money you can't afford to lose**

## 🐛 Troubleshooting

### "No strategies loaded"
- Check the `strategies/` folder exists
- Ensure strategy files have `strategy_name` attribute
- Click "Reload Strategies" button

### "No trades executed"
- Strategy signals too restrictive
- Try different timeframes
- Adjust strategy parameters

### GUI not opening
```bash
pip install tkinter pandas numpy backtrader ccxt matplotlib
```

## 📈 Example Results

With proper settings you should see:
- **Win Rate**: 40-60% (typical)
- **Total Return**: Varies greatly with leverage
- **Sharpe Ratio**: > 1.5 (good)
- **Max Drawdown**: < 20% (with risk management)

## 🚀 Getting Started

1. Run: `python backtest_pro.py`
2. Select a strategy
3. Set leverage (start with 1-5x)
4. Set risk per trade (2%)
5. Click "Test All Timeframes"
6. Find best performing setup
7. Create your own strategies!

---

**Remember**: This is for backtesting only. Real trading involves real risk!
