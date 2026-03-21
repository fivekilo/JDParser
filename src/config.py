"""项目配置"""

from pathlib import Path

# ── 路径配置 ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PARSED_DATA_DIR = PROJECT_ROOT / "data" / "parsed"

# ── DeepSeek API 配置 ──
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

# ── LLM 请求配置 ──
LLM_MAX_RETRIES = 3
LLM_RETRY_DELAY = 2  # 秒
LLM_TEMPERATURE = 0.1
LLM_REQUEST_INTERVAL = 0.5  # 请求间隔（秒），避免触发速率限制
