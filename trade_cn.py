from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
import time
import logging

# ====================== 1. 基础配置 ======================
# 替换为你的 API 密钥
API_KEY = "***"
SECRET_KEY = "***"

# 交易配置
SYMBOL = "XAUUSDT"          # 交易对（XAU/USDT）
BASE_ASSET = "USDT"         # 基础资产
QUANTITY = 0.01             # 每次下单数量（XAUUSDT 最小交易单位 0.01）
LEVERAGE = 1                # 现货无杠杆，若用合约需修改
RISK_RATIO = 0.01           # 风险比例（单次下单金额不超过账户 USDT 余额的 1%）

# 日志配置（方便排查问题）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ====================== 2. 初始化币安客户端 ======================
def init_binance_client():
    """初始化币安客户端（支持现货/合约，这里默认现货）"""
    client = Client(API_KEY, SECRET_KEY, testnet=True)
    # 测试连接
    try:
        client.get_account()
        logger.info("币安 API 连接成功！")
        return client
    except Exception as e:
        logger.error(f"API 连接失败：{e}")
        raise SystemExit(1)

# ====================== 3. 解析交易信号 ======================
def get_trade_signal():
    """
    获取交易信号（核心逻辑，需根据你的信号源修改）
    返回值：
        - "BUY"：买入信号
        - "SELL"：卖出信号
        - "HOLD"：持仓观望
    信号源可替换为：
        1. 本地文件/数据库
        2. HTTP 接口（如第三方信号服务）
        3. 技术指标计算（MA/RSI 等）
    """
    # 示例1：固定信号（测试用，实际需替换为真实信号源）
    # return "BUY"  # 测试买入
    # return "SELL" # 测试卖出
    return "HOLD"   # 观望

    # 示例2：从 HTTP 接口获取信号（真实场景常用）
    # import requests
    # try:
    #     response = requests.get("你的信号接口地址", timeout=5)
    #     signal = response.json().get("signal", "HOLD")
    #     return signal.upper()
    # except Exception as e:
    #     logger.error(f"获取信号失败：{e}")
    #     return "HOLD"

# ====================== 4. 账户余额与风控 ======================
def get_balance(client, asset):
    """获取指定资产的可用余额"""
    account_info = client.get_account()
    for balance in account_info["balances"]:
        if balance["asset"] == asset:
            return float(balance["free"])
    return 0.0

def calculate_safe_quantity(client):
    """根据风控规则计算安全下单数量"""
    usdt_balance = get_balance(client, BASE_ASSET)
    max_trade_usdt = usdt_balance * RISK_RATIO  # 单次最大交易金额
    # 获取最新价格，计算可买数量（数量 = 金额 / 价格）
    ticker = client.get_symbol_ticker(symbol=SYMBOL)
    latest_price = float(ticker["price"])
    safe_quantity = max_trade_usdt / latest_price
    # 向下取整到最小交易单位（0.01）
    safe_quantity = round(safe_quantity // 0.01 * 0.01, 2)
    # 确保数量不小于最小交易单位
    return max(safe_quantity, 0.01)

# ====================== 5. 核心交易逻辑 ======================
def place_order(client, side, quantity):
    """
    下单函数
    :param side: 下单方向（Client.SIDE_BUY / Client.SIDE_SELL）
    :param quantity: 下单数量
    :return: 订单信息 / None
    """
    if quantity < 0.01:
        logger.warning("下单数量小于最小交易单位（0.01），跳过下单")
        return None

    try:
        # 市价单（适合信号交易，快速成交）
        order = client.create_order(
            symbol=SYMBOL,
            side=side,
            type=Client.ORDER_TYPE_MARKET,
            quantity=quantity
        )
        logger.info(f"{side} 订单成功：{order}")
        return order
    except BinanceAPIException as e:
        logger.error(f"API 错误：{e}")
    except BinanceOrderException as e:
        logger.error(f"订单错误：{e}")
    except Exception as e:
        logger.error(f"未知下单错误：{e}")
    return None

def close_all_position(client):
    """平仓（卖出所有持仓的 XAUUSDT）"""
    xau_balance = get_balance(client, "XAU")  # 获取 XAU 可用余额
    if xau_balance < 0.01:
        logger.info("无 XAU 持仓，无需平仓")
        return None
    # 卖出所有持仓（市价单）
    return place_order(client, Client.SIDE_SELL, round(xau_balance, 2))

# ====================== 6. 主循环（监听信号 + 执行交易） ======================
def main():
    client = init_binance_client()
    logger.info("开始监听交易信号...")

    while True:
        try:
            # 1. 获取交易信号
            signal = get_trade_signal()
            logger.info(f"当前信号：{signal}")

            # 2. 根据信号执行交易
            if signal == "BUY":
                # 计算安全下单数量（替代固定 QUANTITY）
                safe_qty = calculate_safe_quantity(client)
                logger.info(f"风控后下单数量：{safe_qty}")
                place_order(client, Client.SIDE_BUY, safe_qty)

            elif signal == "SELL":
                # 平仓（卖出所有持仓）
                close_all_position(client)

            elif signal == "HOLD":
                logger.info("持仓观望，无操作")

            # 3. 循环间隔（避免频繁请求）
            time.sleep(5)  # 每 5 秒检查一次信号

        except KeyboardInterrupt:
            logger.info("手动停止程序")
            break
        except Exception as e:
            logger.error(f"主循环异常：{e}")
            time.sleep(10)  # 异常后暂停 10 秒再重试

if __name__ == "__main__":
    main()
