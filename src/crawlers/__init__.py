"""职位抓取模块。"""

from src.crawlers.baidu import BaiduCrawler
from src.crawlers.meituan import MeituanCrawler
from src.crawlers.tencent import TencentCrawler

__all__ = ["BaiduCrawler", "MeituanCrawler", "TencentCrawler"]
