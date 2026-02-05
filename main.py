import yfinance as yf
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
SIGNAL_TICKER = "SPY"       # The stable index we watch (S&P 500)
TRADE_ASSET   = "TQQQ"      # The leveraged asset we actually buy
CASH_ASSET    = "CASH/BIL"  # Where we go when we sell
SMA_WINDOW    = 200         # 200-day Moving Average
ENTRY_PCT     = 0.04        # +4% Entry Threshold
EXIT_PCT      = 0.03        # -3% Exit Threshold

def calculate_signal():
    print(f"Fetching data for {SIGNAL_TICKER}...")
    # Fetch 3 years to ensure we have a valid 200 SMA and enough history to determine state
    ticker = yf.Ticker(SIGNAL_TICKER)
    df = ticker.history(period="3y")

    if len(df) < SMA_WINDOW:
        raise ValueError("Not enough data to calculate indicator")

    # 1. Calculate Indicators
    df['SMA'] = df['Close'].rolling(window=SMA_WINDOW).mean()
    df['Upper_Band'] = df['SMA'] * (1 + ENTRY_PCT)  # Buy when price crosses above this
    df['Lower_Band'] = df['SMA'] * (1 - EXIT_PCT)   # Sell when price drops below this

    # 2. Determine Current State (Replay Logic)
    # We need to loop through history to find the current state because of the "hold" zone.
    # We start 'out of market' by default or assume state based on long-term history.
    in_market = False 
    
    # We only need to replay the part where SMA exists
    valid_data = df.dropna(subset=['SMA'])
    
    for i, row in valid_data.iterrows():
        close = row['Close']
        upper = row['Upper_Band']
        lower = row['Lower_Band']
        
        if not in_market and close > upper:
            in_market = True # BUY SIGNAL
        elif in_market and close < lower:
            in_market = False # SELL SIGNAL
            
    # 3. Get Today's Specifics
    last_row = df.iloc[-1]
    current_price = last_row['Close']
    current_sma   = last_row['SMA']
    buy_trigger   = current_sma * (1 + ENTRY_PCT)
    sell_trigger  = current_sma * (1 - EXIT_PCT)
    
    # 4. Prepare Dashboard Data
    if in_market:
        status = "BULLISH"
        decision = f"HOLD {TRADE_ASSET}"
        color = "#2ecc71" # Green
        # If we are holding, the next relevant number is the SELL trigger
        distance = current_price - sell_trigger
        dist_pct = (distance / current_price) * 100
        message = f"Stay in {TRADE_ASSET}. Sell if SPY drops below ${sell_trigger:.2f}."
    else:
        status = "BEARISH"
        decision = f"STAY IN {CASH_ASSET}"
        color = "#e74c3c" # Red
        # If we are in cash, the next relevant number is the BUY trigger
        distance = buy_trigger - current_price
        dist_pct = (distance / current_price) * 100
        message = f"Stay in Cash. Buy {TRADE_ASSET} if SPY rises above ${buy_trigger:.2f}."

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "timestamp": datetime.now().strftime("%H:%M:%S UTC"),
        "current_price": round(current_price, 2),
        "sma": round(current_sma, 2),
        "status": status,
        "decision": decision,
        "color": color,
        "message": message,
        "dist_pct": round(dist_pct, 2),
        "buy_trigger": round(buy_trigger, 2),
        "sell_trigger": round(sell_trigger, 2)
    }

def generate_html(data):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TQQQ Strategy Tracker</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #0d1117; color: #c9d1d9; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }}
            .card {{ background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 2rem; width: 90%; max-width: 400px; box-shadow: 0 4px 12px rgba(0,0,0,0.5); text-align: center; }}
            .status-badge {{ background-color: {data['color']}20; color: {data['color']}; border: 1px solid {data['color']}; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: bold; text-transform: uppercase; display: inline-block; margin-bottom: 1rem; }}
            .action {{ font-size: 2rem; font-weight: 800; margin: 0.5rem 0; color: #ffffff; }}
            .message {{ color: #8b949e; font-size: 0.95rem; margin-bottom: 1.5rem; line-height: 1.4; }}
            .data-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; text-align: left; background: #0d1117; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; }}
            .data-item label {{ display: block; font-size: 0.75rem; color: #8b949e; margin-bottom: 2px; }}
            .data-item span {{ font-size: 1.1rem; font-weight: 600; color: #f0f6fc; }}
            .footer {{ font-size: 0.75rem; color: #484f58; margin-top: 1rem; border-top: 1px solid #30363d; padding-top: 1rem; }}
        </style>
    </head>
    <body>
        <div class="card">
            <span class="status-badge">{data['status']}</span>
            <div class="action">{data['decision']}</div>
            <div class="message">{data['message']}</div>
            
            <div class="data-grid">
                <div class="data-item">
                    <label>SPY Price</label>
                    <span>${data['current_price']}</span>
                </div>
                <div class="data-item">
                    <label>200 SMA</label>
                    <span>${data['sma']}</span>
                </div>
                <div class="data-item">
                    <label>Buy Above (+4%)</label>
                    <span style="color: #2ecc71">${data['buy_trigger']}</span>
                </div>
                <div class="data-item">
                    <label>Sell Below (-3%)</label>
                    <span style="color: #e74c3c">${data['sell_trigger']}</span>
                </div>
            </div>
            
            <div class="footer">
                Last Updated: {data['date']} @ {data['timestamp']}
            </div>
        </div>
    </body>
    </html>
    """
    with open("index.html", "w") as f:
        f.write(html_content)
    print("Website generated successfully.")

if __name__ == "__main__":
    calculate_signal()
    data = calculate_signal()
    generate_html(data)
