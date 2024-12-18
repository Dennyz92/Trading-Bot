from flask import Flask, request
import requests
import time
import hmac
import hashlib

app = Flask(__name__)

# Binance API credentials (replace with your keys)
BINANCE_API_KEY = "dx5zqlJnIr0NDnIgZxP6vNxVOyFiWmy9gjiKYqsUpvQp2tNDv6wDtYiUHoA8f3zi"
BINANCE_SECRET_KEY = "LwYHoI3j2HjrUgyfsxvDJmUvP4PoAoKKWqbBd1TIPJ8phHSZGMhrfA3jonykj6PU"

@app.route('/', methods=['GET'])
def home():
    return "Trading bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        if not data:
            return {"message": "No data received"}, 400

        symbol = data.get("symbol")
        action = data.get("action")

        if not symbol or not action:
            return {"message": "Invalid request format"}, 400

        # Example of processing the order (can be expanded)
        return {"status": "success", "message": f"{action.upper()} order for {symbol} received"}, 200
    except Exception as e:
        return {"message": str(e), "status": "error"}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
