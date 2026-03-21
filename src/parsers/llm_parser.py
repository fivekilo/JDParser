"""基于 DeepSeek LLM 的 JD 知识抽取解析器

使用 LLM 从 JD 文本中提取细粒度技能、职责等结构化信息，
并由 RegexParser 预解析的元数据进行补充。
"""

import json
import logging
import time
from typing import Any

from openai import OpenAI

from src import config
from src.models import JobDescription, Skill
from src.parsers.base import BaseParser
from src.parsers.regex_parser import RegexParser

logger = logging.getLogger(__name__)

# ── 系统 Prompt ──
SYSTEM_PROMPT = """\
你是一个专业的职位描述（JD）知识抽取助手。
你的任务是从给定的 JD 文本中提取结构化信息，用于构建就业/职业规划知识图谱。

请严格按照以下 JSON Schema 输出，不要输出任何额外文字：

{
  "job_title": "职位名称（去掉公司/平台前缀标记）",
  "location": "工作城市",
  "education": "学历要求（博士/硕士/本科/大专/不限）",
  "experience": "工作年限要求（如 3-5年、不限）",
  "job_category": "职位所属大类（如 后端开发、前端开发、数据分析、AI/机器学习、运维、测试、产品、设计 等）",
  "responsibilities": ["职责1", "职责2", ...],
  "required_skills": [
    {"name": "技能名称（归一化英文/中文通用名）", "proficiency": "熟练度（了解/熟悉/熟练/精通/不限）", "category": "技能分类"},
    ...
  ],
  "preferred_skills": [
    {"name": "技能名称", "proficiency": "熟练度", "category": "技能分类"},
    ...
  ]
}

技能抽取规则：
1. 将每个技能拆成最小粒度，例如"熟悉 MySQL/Redis/MongoDB" → 三个独立技能
2. 技能名称归一化：使用业界通用名称，如 "JavaScript" 而非 "JS"，"Kubernetes" 而非 "K8S"
3. proficiency 取值：了解 / 熟悉 / 熟练 / 精通 / 不限（如果文中未明确说明则为"不限"）
4. category 取值范围：编程语言 / 前端框架 / 后端框架 / 数据库 / 缓存 / 消息队列 / 云平台 / DevOps工具 / AI工具 / 机器学习 / 深度学习 / 数据处理 / 操作系统 / 网络 / 测试工具 / 项目管理 / 通用技能 / 软技能 / 其他
5. 软技能也要提取，如"沟通能力""团队协作""学习能力"等，category 为"软技能"
6. 加分项里的技能放到 preferred_skills
"""


class LLMParser(BaseParser):
    """使用 DeepSeek API 进行深度知识抽取"""

    def __init__(self, api_key: str):
        self._client = OpenAI(
            api_key=api_key,
            base_url=config.DEEPSEEK_BASE_URL,
        )
        self._regex_parser = RegexParser()
        self._last_request_time = 0.0

    def parse(self, text: str, filename: str) -> JobDescription:
        # 先用正则解析器提取基础字段
        jd = self._regex_parser.parse(text, filename)

        # 调用 LLM 提取深层知识
        llm_result = self._call_llm(text)
        if llm_result:
            self._merge_llm_result(jd, llm_result)

        return jd

    def _call_llm(self, text: str) -> dict[str, Any] | None:
        """调用 DeepSeek API 并解析返回的 JSON"""
        # 速率限制
        elapsed = time.time() - self._last_request_time
        if elapsed < config.LLM_REQUEST_INTERVAL:
            time.sleep(config.LLM_REQUEST_INTERVAL - elapsed)

        for attempt in range(config.LLM_MAX_RETRIES):
            try:
                self._last_request_time = time.time()
                response = self._client.chat.completions.create(
                    model=config.DEEPSEEK_MODEL,
                    temperature=config.LLM_TEMPERATURE,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"请从以下JD中提取结构化信息：\n\n{text}"},
                    ],
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content
                if content:
                    return json.loads(content)
            except json.JSONDecodeError:
                logger.warning("LLM 返回的JSON解析失败 (尝试 %d/%d)", attempt + 1, config.LLM_MAX_RETRIES)
            except Exception as e:
                logger.warning("LLM 请求失败 (尝试 %d/%d): %s", attempt + 1, config.LLM_MAX_RETRIES, e)
                if attempt < config.LLM_MAX_RETRIES - 1:
                    time.sleep(config.LLM_RETRY_DELAY * (attempt + 1))

        logger.error("LLM 调用最终失败，将仅使用正则解析结果")
        return None

    @staticmethod
    def _merge_llm_result(jd: JobDescription, data: dict[str, Any]) -> None:
        """将 LLM 抽取结果合并到 JD 对象（LLM 结果优先补充，不覆盖已有值）"""
        # 简单字段：仅在正则未提取到时使用 LLM 结果
        for field_name in ("job_title", "location", "education", "experience", "job_category"):
            llm_val = data.get(field_name)
            if llm_val and not getattr(jd, field_name, None):
                setattr(jd, field_name, llm_val)

        # 职责：LLM 结果通常更干净
        if data.get("responsibilities"):
            jd.responsibilities = data["responsibilities"]

        # 技能：LLM 擅长细粒度拆分，直接使用 LLM 结果
        if data.get("required_skills"):
            jd.required_skills = [
                Skill(
                    name=s.get("name", ""),
                    proficiency=s.get("proficiency"),
                    category=s.get("category"),
                )
                for s in data["required_skills"]
                if s.get("name")
            ]

        if data.get("preferred_skills"):
            jd.preferred_skills = [
                Skill(
                    name=s.get("name", ""),
                    proficiency=s.get("proficiency"),
                    category=s.get("category"),
                )
                for s in data["preferred_skills"]
                if s.get("name")
            ]
