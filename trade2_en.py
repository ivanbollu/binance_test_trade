from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
import requests
import time

# ====================== Configuration (Replace with your testnet keys) ======================
TEST_API_KEY = "***"
TEST_SECRET_KEY = "***"
SYMBOL = "BTCUSDT"  # BTC/USDT trading pair (more widely available)
TESTNET_FUND_URL = "https://testnet.binance.vision/faucet/spot"  # Testnet fund claiming interface

# ====================== 1. Initialize Testnet Client ======================
def init_testnet_client():
    """Initialize Binance Testnet Client"""
    client = Client(TEST_API_KEY, TEST_SECRET_KEY, testnet=True)
    # Test connection
    try:
        account_info = client.get_account()
        print(f"Testnet API connection successful!")
        print(f"Total asset types in account: {len(account_info['balances'])}")
        return client
    except Exception as e:
        print(f"API connection failed: {e}")
        raise SystemExit(1)

# ====================== 2. Automatically claim testnet USDT (no manual operation needed) ======================
def get_testnet_funds(client):
    """Automatically claim testnet USDT funds"""
    # Get testnet account ID
    account_info = client.get_account()
    account_id = account_info["uid"]
    
    # Send fund claim request
    headers = {"Content-Type": "application/json"}
    data = {
        "userId": str(account_id),
        "asset": "USDT",
        "amount": 10000  # Claim 10000 USDT each time
    }
    
    try:
        response = requests.post(TESTNET_FUND_URL, json=data, headers=headers)
        if response.status_code == 200:
            print(f"Successfully claimed testnet USDT!")
        else:
            print(f"Fund claim prompt: {response.json().get('message', 'Already claimed, can claim again after 1 hour')}")
    except Exception as e:
        print(f"Fund claim failed: {e}")
    
    # Wait for funds to arrive
    time.sleep(2)

# ====================== 3. Query XAUUSDT related information ======================
def query_info(client):
    """Query account balance + latest BTCUSDT price"""
    # 1. Query USDT available balance
    usdt_balance = 0.0
    btc_balance = 0.0
    account_info = client.get_account()
    for balance in account_info["balances"]:
        if balance["asset"] == "USDT":
            usdt_balance = float(balance["free"])
        if balance["asset"] == "BTC":
            btc_balance = float(balance["free"])

    # 2. Query latest BTCUSDT price
    ticker = client.get_symbol_ticker(symbol=SYMBOL)
    latest_price = float(ticker["price"])

    print(f"   Account Information:")
    print(f"   USDT Available Balance: {usdt_balance:.2f}")
    print(f"   BTC Available Balance: {btc_balance:.8f}")
    print(f"   BTCUSDT Latest Price: {latest_price:.2f} USDT")

    return usdt_balance, latest_price

# ====================== 4. Test order placement / position closing ======================
def test_trade(client):
    """Test buy + sell BTCUSDT"""
    # Order quantity (BTCUSDT minimum trading unit 0.000001)
    quantity = 0.001

    # 1. Market buy BTCUSDT
    try:
        buy_order = client.create_order(
            symbol=SYMBOL,
            side=Client.SIDE_BUY,
            type=Client.ORDER_TYPE_MARKET,
            quantity=quantity
        )
        print(f"   Buy order successful:")
        print(f"   Order ID: {buy_order['orderId']}")
        print(f"   Executed Quantity: {buy_order['executedQty']} BTC")
    except (BinanceAPIException, BinanceOrderException) as e:
        print(f"   Buy failed: {e}")
        return

    time.sleep(2)  # Wait for order to execute

    # 2. Market sell BTCUSDT (close position)
    try:
        sell_order = client.create_order(
            symbol=SYMBOL,
            side=Client.SIDE_SELL,
            type=Client.ORDER_TYPE_MARKET,
            quantity=quantity
        )
        print(f"   Sell order successful:")
        print(f"   Order ID: {sell_order['orderId']}")
        print(f"   Executed Quantity: {sell_order['executedQty']} BTC")
    except (BinanceAPIException, BinanceOrderException) as e:
        print(f"   Sell failed: {e}")

# ====================== Main Function ======================
if __name__ == "__main__":
    # Step 1: Initialize client
    client = init_testnet_client()
    
    # Step 2: Claim test funds
    get_testnet_funds(client)
    
    # Step 3: Query account information
    usdt_balance, _ = query_info(client)
    
    # Step 4: Test trade (execute only if balance sufficient)
    if usdt_balance > 10:  # Ensure sufficient USDT for placing order
        test_trade(client)
        # Query balance again after trade
        print("   Account Information After Trade:")
        query_info(client)
    else:
        print("  ️ Insufficient USDT balance, unable to test trade!")
