from flask import Flask, request
import requests
import time
import hashlib
import hmac

app = Flask(__name__)

# Binance API credentials (replace with your actual keys)
BINANCE_API_KEY = "your_binance_api_key"
BINANCE_SECRET_KEY = "your_binance_secret_key"

# Function to fetch the current market price from Binance.US
def get_market_price(symbol):
    url = f"https://api.binance.us/api/v3/ticker/price?symbol={symbol}"
    response = requests.get(url)
    price_data = response.json()

    if "price" not in price_data:
        raise ValueError(f"Could not fetch price for {symbol}: {price_data}")
    return float(price_data["price"])

# Function to send an order to Binance.US
def send_order_to_binance(symbol, side, usdt_amount=None):
    # Fetch account balance for the asset being traded
    url_account = "https://api.binance.us/api/v3/account"
    headers = {"X-MBX-APIKEY": BINANCE_API_KEY}
    params = {"timestamp": int(time.time() * 1000)}
    query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
    signature = hmac.new(BINANCE_SECRET_KEY.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    params["signature"] = signature

    response_account = requests.get(url_account, headers=headers, params=params)
    balances = response_account.json().get("balances", [])

    # Determine the base asset (e.g., ETH in ETHUSDT)
    base_asset = symbol[:-4]  # Removes 'USDT' to get ETH
    available_balance = 0

    for balance in balances:
        if balance["asset"] == base_asset:
            available_balance = float(balance["free"])
            break

    # For 'sell', use the available balance
    if side.lower() == "sell":
        quantity = available_balance
    else:
        # For 'buy', calculate quantity based on USDT amount
        market_price = get_market_price(symbol)
        quantity = usdt_amount / market_price

    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")

    # Prepare the order
    url_order = "https://api.binance.us/api/v3/order"
    params = {
        "symbol": symbol,
        "side": side.upper(),
        "type": "MARKET",
        "quantity": round(quantity, 5),  # Binance requires specific precision
        "timestamp": int(time.time() * 1000),
    }
    query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
    signature = hmac.new(BINANCE_SECRET_KEY.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    params["signature"] = signature

    # Send the request to Binance
    response = requests.post(url_order, headers=headers, params=params)
    return response.json()

# Default route to indicate the app is running
@app.route('/', methods=['GET'])
def home():
    return """
    <html>
        <head><title>Trading Bot</title></head>
        <body>
            <h1>The app is running!</h1>
            <p>Your trading bot is ready to receive alerts from TradingView.</p>
        </body>
    </html>
    """

# Webhook route for TradingView
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Receive the alert data
        data = request.json
        print("Received alert:", data)

        # Extract data from TradingView alert
        symbol = data.get("symbol")
        action = data.get("action")  # "buy" or "sell"
        usdt_amount = 20  # Fixed $20 per trade

        if not symbol or not action:
            return {"error": "Invalid data format"}, 400

        # Send trade order to Binance.US
        result = send_order_to_binance(symbol, action, usdt_amount)
        return {"status": "success", "result": result}, 200
    except Exception as e:
        print("Error processing alert:", str(e))
        return {"status": "error", "message": str(e)}, 500

# Run the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

