# ⚡ QUICK START GUIDE

## 🚀 Installation & First Run

### Windows:
1. Double-click `install_and_run.bat`
2. Done! The GUI will open automatically.

### Mac/Linux:
1. Open terminal in this folder
2. Run: `chmod +x install_and_run.sh`
3. Run: `./install_and_run.sh`

### Alternative (All platforms):
```bash
pip install -r requirements.txt
python run.py
```

## 📊 Your First Backtest

1. **Start the application** (see above)
2. **Select settings:**
   - Trading Pair: `BTC/USDT`
   - Strategy: `SMA Crossover`
   - Timeframe: `1h`
   - Leverage: `5`
   - Risk per Trade: `2`
3. **Click:** `🚀 Run Backtest`
4. **View results** in the right panel

## 🎯 Quick Tests to Try

### Test 1: Find Best Timeframe
1. Pick any strategy
2. Click `📊 Test All Timeframes`
3. See which timeframe performs best

### Test 2: Scalping with Leverage
1. Strategy: `Scalper Pro`
2. Timeframe: `5m`
3. Leverage: `20`
4. Risk: `1%`
5. Run backtest

### Test 3: Conservative Swing Trade
1. Strategy: `MACD Advanced`
2. Timeframe: `4h`
3. Leverage: `2`
4. Risk: `2%`
5. Run backtest

## 💡 Understanding Leverage

- **1x** = No leverage (normal trading)
- **10x** = 1% price move = 10% account change
- **50x** = 1% price move = 50% account change
- **100x** = 1% price move = 100% account change

⚠️ **WARNING**: High leverage = high risk!

## 📁 Folder Structure

```
crypto_backtest_pro/
├── backtest_pro.py          # Main application
├── run.py                   # Launcher script
├── requirements.txt         # Python packages
├── strategies/              # Strategy files
│   ├── base_strategy.py     # Base class
│   ├── sma_strategy.py      # SMA Crossover
│   ├── rsi_strategy.py      # RSI Strategy
│   ├── macd_strategy.py     # MACD Strategy
│   ├── bollinger_strategy.py # Bollinger Bands
│   ├── scalping_strategy.py  # Scalping
│   ├── grid_strategy.py      # Grid Trading
│   ├── ichimoku_strategy.py  # Ichimoku Cloud
│   └── volume_profile_strategy.py # Volume Profile
└── README.md                # Full documentation
```

## 🔥 Pro Settings

### Aggressive Scalping
- Timeframe: `1m` or `5m`
- Leverage: `20-50x`
- Risk: `1-2%`
- Stop Loss: `0.5-1%`

### Safe Day Trading
- Timeframe: `30m` or `1h`
- Leverage: `3-5x`
- Risk: `2%`
- Stop Loss: `2%`

### Long-term Swing
- Timeframe: `4h` or `1d`
- Leverage: `1-2x`
- Risk: `3%`
- Stop Loss: `5%`

## ❓ Troubleshooting

**"No module named tkinter"**
- Windows: Reinstall Python with tkinter
- Mac: `brew install python-tk`
- Linux: `sudo apt-get install python3-tk`

**"No strategies loaded"**
- Make sure you're running from the correct folder
- Check that `strategies/` folder exists
- Click "Reload Strategies" button

**Application won't start**
- Make sure Python 3.6+ is installed
- Run: `python --version` to check
- Try: `pip install --upgrade pip`

## 📈 Success Tips

1. **Start small** - Test with 1-5x leverage first
2. **Use stop losses** - Always enable risk management
3. **Test all timeframes** - Find what works best
4. **Paper trade first** - Test strategies with fake money
5. **Keep learning** - Modify and create new strategies

---

**Ready to start? Run the application and start backtesting!** 🚀
