from flask import Flask, request
import requests
import time
import hashlib
import hmac

app = Flask(__name__)

# Binance API credentials (replace with your actual keys)
BINANCE_API_KEY = "dx5zqlJnIr0NDnIgZxP6vNxVOyFiWmy9gjiKYqsUpvQp2tNDv6wDtYiUHoA8f3zi"
BINANCE_SECRET_KEY = "LwYHoI3j2HjrUgyfsxvDJmUvP4PoAoKKWqbBd1TIPJ8phHSZGMhrfA3jonykj6PU"

# Function to fetch the current market price from Binance.US
def get_market_price(symbol):
    url = f"https://api.binance.us/api/v3/ticker/price?symbol={symbol}"
    response = requests.get(url)
    price_data = response.json()

    if "price" not in price_data:
        raise ValueError(f"Could not fetch price for {symbol}: {price_data}")
    return float(price_data["price"])

# Function to send an order to Binance.US
def send_order_to_binance(symbol, side, usdt_amount):
    # Fetch the market price
    market_price = get_market_price(symbol)
    print(f"Market price for {symbol}: {market_price}")

    # Calculate the quantity to trade
    quantity = usdt_amount / market_price

    # Fetch LOT_SIZE filters for the trading pair
    exchange_info_url = "https://api.binance.us/api/v3/exchangeInfo"
    response_info = requests.get(exchange_info_url).json()
    symbol_filters = [
        s for s in response_info["symbols"] if s["symbol"] == symbol
    ]

    if not symbol_filters:
        raise ValueError(f"Symbol {symbol} not found in Binance exchange info.")

    lot_size_filter = next(
        f for f in symbol_filters[0]["filters"] if f["filterType"] == "LOT_SIZE"
    )

    # Apply LOT_SIZE restrictions
    min_qty = float(lot_size_filter["minQty"])
    step_size = float(lot_size_filter["stepSize"])

    # Ensure quantity meets the LOT_SIZE requirements
    if quantity < min_qty:
        raise ValueError(f"Trade quantity {quantity} is below the minimum {min_qty}.")
    quantity = round(quantity - (quantity % step_size), 5)  # Adjust to step size

    print(f"Adjusted trade quantity for {symbol}: {quantity}")

    # Prepare the order details
    url_order = "https://api.binance.us/api/v3/order"
    headers = {
        "X-MBX-APIKEY": BINANCE_API_KEY
    }
    params = {
        "symbol": symbol,
        "side": side.upper(),  # "BUY" or "SELL"
        "type": "MARKET",
        "quantity": quantity,
        "timestamp": int(time.time() * 1000)  # Current timestamp in milliseconds
    }

    # Create the signature
    query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
    signature = hmac.new(BINANCE_SECRET_KEY.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    params["signature"] = signature

    # Send the request to Binance.US
    response = requests.post(url_order, headers=headers, params=params)
    print(f"Binance response for {symbol}: {response.json()}")
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

        if not symbol or not action or usdt_amount <= 0:
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
