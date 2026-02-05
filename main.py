import yfinance as yf
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
SIGNAL_TICKER = "SPY"
TRADE_ASSET   = "TQQQ"
CASH_ASSET    = "CASH/BIL"
SMA_WINDOW    = 200
ENTRY_PCT     = 0.04
EXIT_PCT      = 0.03

def calculate_signal():
    print(f"Fetching data for {SIGNAL_TICKER}...")
    ticker = yf.Ticker(SIGNAL_TICKER)
    df = ticker.history(period="3y")

    if len(df) < SMA_WINDOW:
        raise ValueError("Not enough data to calculate indicator")

    # 1. Calculate Indicators
    df['SMA'] = df['Close'].rolling(window=SMA_WINDOW).mean()
    df['Upper_Band'] = df['SMA'] * (1 + ENTRY_PCT)
    df['Lower_Band'] = df['SMA'] * (1 - EXIT_PCT)

    # 2. Replay History to determine State
    valid_data = df.dropna(subset=['SMA'])
    
    # We need to track the state day-by-day to compare Today vs Yesterday
    # state_history will be a list of booleans (True = In Market, False = Out)
    state_history = []
    in_market = False # Start assuming out
    
    for i, row in valid_data.iterrows():
        close = row['Close']
        upper = row['Upper_Band']
        lower = row['Lower_Band']
        
        if not in_market and close > upper:
            in_market = True
        elif in_market and close < lower:
            in_market = False
            
        state_history.append(in_market)

    # 3. Determine Today's Status
    today_in_market = state_history[-1]
    yesterday_in_market = state_history[-2] if len(state_history) > 1 else today_in_market
    
    last_row = df.iloc[-1]
    current_price = last_row['Close']
    current_sma   = last_row['SMA']
    buy_trigger   = current_sma * (1 + ENTRY_PCT)
    sell_trigger  = current_sma * (1 - EXIT_PCT)

    # 4. Select Image & Message based on CHANGE
    # If state changed TODAY, we show Buy/Sell. Otherwise, we show Hold.
    
    if today_in_market and not yesterday_in_market:
        # Just bought today
        image = "buy.jpg"
        status = "BUY SIGNAL"
        decision = f"BUY {TRADE_ASSET}"
        color = "#2ecc71" # Green
        message = "Price crossed above entry threshold. Enter position."
        
    elif not today_in_market and yesterday_in_market:
        # Just sold today
        image = "sell.jpg"
        status = "SELL SIGNAL"
        decision = f"SELL {TRADE_ASSET}"
        color = "#e74c3c" # Red
        message = "Price dropped below exit threshold. Exit to Cash."
        
    elif today_in_market:
        # Bullish but no change (Holding)
        image = "hold.jpg"
        status = "BULLISH (HOLD)"
        decision = f"HOLD {TRADE_ASSET}"
        color = "#3498db" # Blue
        message = f"Trend is healthy. Sell if SPY closes below ${sell_trigger:.2f}."
        
    else:
        # Bearish but no change (Waiting)
        image = "hold.jpg"
        status = "BEARISH (WAIT)"
        decision = "HOLD CASH"
        color = "#95a5a6" # Grey
        message = f"Trend is weak. Buy if SPY closes above ${buy_trigger:.2f}."

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "timestamp": datetime.now().strftime("%H:%M:%S UTC"),
        "current_price": round(current_price, 2),
        "sma": round(current_sma, 2),
        "status": status,
        "decision": decision,
        "color": color,
        "message": message,
        "image": image,
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
        <title>Strategy Dashboard</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #0d1117; color: #c9d1d9; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }}
            .card {{ background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 2rem; width: 100%; max-width: 400px; box-shadow: 0 4px 12px rgba(0,0,0,0.5); text-align: center; }}
            .signal-img {{ width: 100%; max-height: 250px; object-fit: cover; border-radius: 8px; margin-bottom: 1.5rem; border: 2px solid {data['color']}; }}
            .status-badge {{ background-color: {data['color']}20; color: {data['color']}; border: 1px solid {data['color']}; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: bold; text-transform: uppercase; display: inline-block; margin-bottom: 0.5rem; }}
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
            <!-- This image changes based on the signal -->
            <img src="{data['image']}" class="signal-img" alt="Signal Image">
            
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
                    <label>Buy Above</label>
                    <span style="color: #2ecc71">${data['buy_trigger']}</span>
                </div>
                <div class="data-item">
                    <label>Sell Below</label>
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
    data = calculate_signal()
    generate_html(data)
