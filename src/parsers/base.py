"""解析器抽象基类"""

from abc import ABC, abstractmethod
from src.models import JobDescription


class BaseParser(ABC):
    """JD 解析器基类"""

    @abstractmethod
    def parse(self, text: str, filename: str) -> JobDescription:
        """将原始 JD 文本解析为结构化对象

        Args:
            text: 原始 JD 文本内容
            filename: 源文件名（用于溯源）

        Returns:
            结构化的 JobDescription 对象
        """
        ...
