from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
import requests
import time

# ====================== 配置（替换为你的测试网密钥） ======================
TEST_API_KEY = "你的测试网API_KEY"
TEST_SECRET_KEY = "你的测试网SECRET_KEY"
SYMBOL = "XAUUSDT"  # XAU/USDT 交易对
TESTNET_FUND_URL = "https://testnet.binance.vision/faucet/spot"  # 测试网领币接口

# ====================== 1. 初始化测试网客户端 ======================
def init_testnet_client():
    """初始化币安测试网客户端"""
    client = Client(TEST_API_KEY, TEST_SECRET_KEY, testnet=True)
    # 测试连接
    try:
        account_info = client.get_account()
        print(f"✅ 测试网 API 连接成功！")
        print(f"📌 账户总资产数：{len(account_info['balances'])} 种")
        return client
    except Exception as e:
        print(f"❌ API 连接失败：{e}")
        raise SystemExit(1)

# ====================== 2. 自动领取测试网 USDT（无需手动操作） ======================
def get_testnet_funds(client):
    """自动领取测试网 USDT 资金"""
    # 获取测试网账户 ID
    account_info = client.get_account()
    account_id = account_info["uid"]
    
    # 发送领币请求
    headers = {"Content-Type": "application/json"}
    data = {
        "userId": str(account_id),
        "asset": "USDT",
        "amount": 10000  # 每次领取 10000 USDT
    }
    
    try:
        response = requests.post(TESTNET_FUND_URL, json=data, headers=headers)
        if response.status_code == 200:
            print(f"✅ 领取测试网 USDT 成功！")
        else:
            print(f"⚠️ 领币提示：{response.json().get('message', '已领取过，1小时后可再领')}")
    except Exception as e:
        print(f"❌ 领币失败：{e}")
    
    # 等待资金到账
    time.sleep(2)

# ====================== 3. 查询 XAUUSDT 相关信息 ======================
def query_info(client):
    """查询账户余额 + XAUUSDT 最新价格"""
    # 1. 查询 USDT 可用余额
    usdt_balance = 0.0
    xau_balance = 0.0
    account_info = client.get_account()
    for balance in account_info["balances"]:
        if balance["asset"] == "USDT":
            usdt_balance = float(balance["free"])
        if balance["asset"] == "XAU":
            xau_balance = float(balance["free"])
    
    # 2. 查询 XAUUSDT 最新价格
    ticker = client.get_symbol_ticker(symbol=SYMBOL)
    latest_price = float(ticker["price"])
    
    print(f"\n📊 账户信息：")
    print(f"   USDT 可用余额：{usdt_balance:.2f}")
    print(f"   XAU 可用余额：{xau_balance:.4f}")
    print(f"   XAUUSDT 最新价格：{latest_price:.2f} USDT")
    
    return usdt_balance, latest_price

# ====================== 4. 测试下单/平仓 ======================
def test_trade(client):
    """测试买入 + 卖出 XAUUSDT"""
    # 下单数量（XAUUSDT 最小交易单位 0.01）
    quantity = 0.01
    
    # 1. 市价买入 XAUUSDT
    try:
        buy_order = client.create_order(
            symbol=SYMBOL,
            side=Client.SIDE_BUY,
            type=Client.ORDER_TYPE_MARKET,
            quantity=quantity
        )
        print(f"\n✅ 买入订单成功：")
        print(f"   订单ID：{buy_order['orderId']}")
        print(f"   成交数量：{buy_order['executedQty']} XAU")
    except (BinanceAPIException, BinanceOrderException) as e:
        print(f"\n❌ 买入失败：{e}")
        return
    
    time.sleep(2)  # 等待订单成交
    
    # 2. 市价卖出 XAUUSDT（平仓）
    try:
        sell_order = client.create_order(
            symbol=SYMBOL,
            side=Client.SIDE_SELL,
            type=Client.ORDER_TYPE_MARKET,
            quantity=quantity
        )
        print(f"\n✅ 卖出订单成功：")
        print(f"   订单ID：{sell_order['orderId']}")
        print(f"   成交数量：{sell_order['executedQty']} XAU")
    except (BinanceAPIException, BinanceOrderException) as e:
        print(f"\n❌ 卖出失败：{e}")

# ====================== 主函数 ======================
if __name__ == "__main__":
    # 步骤1：初始化客户端
    client = init_testnet_client()
    
    # 步骤2：领取测试资金
    get_testnet_funds(client)
    
    # 步骤3：查询账户信息
    usdt_balance, _ = query_info(client)
    
    # 步骤4：测试交易（余额足够才执行）
    if usdt_balance > 10:  # 确保有足够 USDT 下单
        test_trade(client)
        # 交易后再次查询余额
        print("\n📊 交易后账户信息：")
        query_info(client)
    else:
        print("\n⚠️ USDT 余额不足，无法测试交易！")