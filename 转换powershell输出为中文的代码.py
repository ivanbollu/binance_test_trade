# 创建一个 handler 来确保 UTF-8 编码
import io
import sys

class UTF8Filter(logging.Filter):
    def filter(self, record):
        # 确保消息是字符串
        if isinstance(record.msg, str):
            return True
        return False

# 设置 stdout 为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)
logger.addFilter(UTF8Filter())