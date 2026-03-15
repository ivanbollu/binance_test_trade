from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
import time
import logging

# ====================== 1. Basic Configuration ======================
# Replace with your API keys
API_KEY = "***"
SECRET_KEY = "***"

# Trading Configuration
SYMBOL = "XAUUSDT"          # Trading pair (XAU/USDT)
BASE_ASSET = "USDT"         # Base asset
QUANTITY = 0.01             # Order quantity per trade (minimum trading unit for XAUUSDT is 0.01)
LEVERAGE = 1                # No leverage for spot trading (modify this if using futures)
RISK_RATIO = 0.01           # Risk ratio (single order amount does not exceed 1% of account USDT balance)

# Logging Configuration (for troubleshooting)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ====================== 2. Initialize Binance Client ======================
def init_binance_client():
    """Initialize Binance client (supports spot/futures, spot by default)"""
    client = Client(API_KEY, SECRET_KEY, testnet=True)
    # Test connection
    try:
        client.get_account()
        logger.info("Binance API connection successful!")
        return client
    except Exception as e:
        logger.error(f"API connection failed: {e}")
        raise SystemExit(1)

# ====================== 3. Parse Trading Signals ======================
def get_trade_signal():
    """
    Get trading signal (core logic, modify according to your signal source)
    Return values:
        - "BUY": Buy signal
        - "SELL": Sell signal
        - "HOLD": Hold position (no action)
    Signal sources can be replaced with:
        1. Local files/databases
        2. HTTP interfaces (e.g., third-party signal services)
        3. Technical indicator calculations (MA/RSI, etc.)
    """
    # Example 1: Fixed signal (for testing, replace with real signal source in production)
    # return "BUY"  # Test buy
    # return "SELL" # Test sell
    return "HOLD"   # Hold position

    # Example 2: Get signal from HTTP interface (common in real scenarios)
    # import requests
    # try:
    #     response = requests.get("Your signal API URL", timeout=5)
    #     signal = response.json().get("signal", "HOLD")
    #     return signal.upper()
    # except Exception as e:
    #     logger.error(f"Failed to get trading signal: {e}")
    #     return "HOLD"

# ====================== 4. Account Balance & Risk Control ======================
def get_balance(client, asset):
    """Get available balance of the specified asset"""
    account_info = client.get_account()
    for balance in account_info["balances"]:
        if balance["asset"] == asset:
            return float(balance["free"])
    return 0.0

def calculate_safe_quantity(client):
    """Calculate safe order quantity based on risk control rules"""
    usdt_balance = get_balance(client, BASE_ASSET)
    max_trade_usdt = usdt_balance * RISK_RATIO  # Maximum trade amount per order
    # Get latest price and calculate purchasable quantity (quantity = amount / price)
    ticker = client.get_symbol_ticker(symbol=SYMBOL)
    latest_price = float(ticker["price"])
    safe_quantity = max_trade_usdt / latest_price
    # Round down to the minimum trading unit (0.01)
    safe_quantity = round(safe_quantity // 0.01 * 0.01, 2)
    # Ensure quantity is not less than the minimum trading unit
    return max(safe_quantity, 0.01)

# ====================== 5. Core Trading Logic ======================
def place_order(client, side, quantity):
    """
    Place order function
    :param side: Order direction (Client.SIDE_BUY / Client.SIDE_SELL)
    :param quantity: Order quantity
    :return: Order information / None
    """
    if quantity < 0.01:
        logger.warning("Order quantity is less than minimum trading unit (0.01), skipping order placement")
        return None

    try:
        # Market order (suitable for signal trading, fast execution)
        order = client.create_order(
            symbol=SYMBOL,
            side=side,
            type=Client.ORDER_TYPE_MARKET,
            quantity=quantity
        )
        logger.info(f"{side} order successful: {order}")
        return order
    except BinanceAPIException as e:
        logger.error(f"API error: {e}")
    except BinanceOrderException as e:
        logger.error(f"Order error: {e}")
    except Exception as e:
        logger.error(f"Unknown order error: {e}")
    return None

def close_all_position(client):
    """Close all positions (sell all held XAUUSDT)"""
    xau_balance = get_balance(client, "XAU")  # Get available XAU balance
    if xau_balance < 0.01:
        logger.info("No XAU positions held, no need to close positions")
        return None
    # Sell all holdings (market order)
    return place_order(client, Client.SIDE_SELL, round(xau_balance, 2))

# ====================== 6. Main Loop (Monitor Signals + Execute Trades) ======================
def main():
    client = init_binance_client()
    logger.info("Start monitoring trading signals...")

    while True:
        try:
            # 1. Get trading signal
            signal = get_trade_signal()
            logger.info(f"Current signal: {signal}")

            # 2. Execute trade based on signal
            if signal == "BUY":
                # Calculate safe order quantity (replace fixed QUANTITY)
                safe_qty = calculate_safe_quantity(client)
                logger.info(f"Safe order quantity after risk control: {safe_qty}")
                place_order(client, Client.SIDE_BUY, safe_qty)

            elif signal == "SELL":
                # Close all positions (sell all holdings)
                close_all_position(client)

            elif signal == "HOLD":
                logger.info("Hold position, no action taken")

            # 3. Loop interval (avoid frequent requests)
            time.sleep(5)  # Check signal every 5 seconds

        except KeyboardInterrupt:
            logger.info("Program stopped manually")
            break
        except Exception as e:
            logger.error(f"Main loop exception: {e}")
            time.sleep(10)  # Pause for 10 seconds before retrying after exception

if __name__ == "__main__":
    main()
