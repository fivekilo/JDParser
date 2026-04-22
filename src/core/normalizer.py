"""技能名称归一化模块

将 JD 中出现的各种技能别名统一为规范名称，
确保知识图谱中同一技能只有一个节点。
包含：技能名称归一化、类别纠错、熟练度映射、经验结构化。
"""

import re
from typing import Optional
from src.core.models import Skill


# ── 归一化映射表 ──
# key: 小写别名/缩写  →  value: 规范名称
_ALIAS_MAP: dict[str, str] = {
    # 编程语言
    "js": "JavaScript",
    "javascript": "JavaScript",
    "es6": "JavaScript",
    "es6+": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "python": "Python",
    "py": "Python",
    "java": "Java",
    "golang": "Go",
    "go": "Go",
    "c++": "C++",
    "cpp": "C++",
    "c#": "C#",
    "csharp": "C#",
    "rust": "Rust",
    "ruby": "Ruby",
    "php": "PHP",
    "scala": "Scala",
    "kotlin": "Kotlin",
    "swift": "Swift",
    "objective-c": "Objective-C",
    "objc": "Objective-C",
    "shell": "Shell",
    "bash": "Shell",
    "lua": "Lua",
    "r": "R",
    "sql": "SQL",
    "html": "HTML",
    "html5": "HTML",
    "css": "CSS",
    "css3": "CSS",

    # 前端框架
    "vue": "Vue.js",
    "vue.js": "Vue.js",
    "vue3": "Vue.js",
    "vue 3": "Vue.js",
    "vue2": "Vue.js",
    "react": "React",
    "react.js": "React",
    "reactjs": "React",
    "angular": "Angular",
    "angularjs": "Angular",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "nuxt": "Nuxt.js",
    "nuxt.js": "Nuxt.js",
    "svelte": "Svelte",
    "jquery": "jQuery",

    # 构建工具
    "webpack": "Webpack",
    "vite": "Vite",
    "rollup": "Rollup",
    "gulp": "Gulp",
    "babel": "Babel",
    "esbuild": "esbuild",

    # 后端框架
    "express": "Express.js",
    "express.js": "Express.js",
    "koa": "Koa.js",
    "koa.js": "Koa.js",
    "spring": "Spring",
    "spring boot": "Spring Boot",
    "springboot": "Spring Boot",
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "gin": "Gin",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "node": "Node.js",

    # 数据库
    "mysql": "MySQL",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "redis": "Redis",
    "elasticsearch": "Elasticsearch",
    "es": "Elasticsearch",
    "hbase": "HBase",
    "cassandra": "Cassandra",
    "sqlite": "SQLite",
    "oracle": "Oracle",
    "clickhouse": "ClickHouse",
    "tidb": "TiDB",

    # 消息队列
    "kafka": "Kafka",
    "rabbitmq": "RabbitMQ",
    "rocketmq": "RocketMQ",
    "activemq": "ActiveMQ",
    "pulsar": "Pulsar",

    # 容器 & 编排
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "swarm": "Docker Swarm",
    "docker swarm": "Docker Swarm",

    # 云平台
    "aws": "AWS",
    "阿里云": "阿里云",
    "aliyun": "阿里云",
    "gcp": "Google Cloud",
    "google cloud": "Google Cloud",
    "azure": "Azure",
    "腾讯云": "腾讯云",
    "华为云": "华为云",

    # CI/CD & DevOps
    "jenkins": "Jenkins",
    "gitlab ci": "GitLab CI",
    "github actions": "GitHub Actions",
    "terraform": "Terraform",
    "ansible": "Ansible",
    "prometheus": "Prometheus",
    "grafana": "Grafana",
    "nginx": "Nginx",
    "git": "Git",
    "gitops": "GitOps",
    "ci/cd": "CI/CD",

    # AI/ML
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "keras": "Keras",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "pandas": "pandas",
    "numpy": "NumPy",
    "spark": "Apache Spark",
    "apache spark": "Apache Spark",
    "hadoop": "Hadoop",
    "hive": "Hive",
    "flink": "Apache Flink",
    "onnx runtime": "ONNX Runtime",
    "tensorrt": "TensorRT",
    "coreml": "Core ML",

    # AI 工具
    "copilot": "GitHub Copilot",
    "github copilot": "GitHub Copilot",
    "cursor": "Cursor",
    "claude code": "Claude Code",

    # 爬虫
    "scrapy": "Scrapy",
    "selenium": "Selenium",
    "playwright": "Playwright",
    "puppeteer": "Puppeteer",

    # 游戏引擎
    "unreal engine": "Unreal Engine",
    "ue": "Unreal Engine",
    "ue4": "Unreal Engine",
    "ue5": "Unreal Engine",
    "unity": "Unity",

    # 其他工具
    "minio": "MinIO",
    "etcd": "etcd",
    "zookeeper": "ZooKeeper",
    "linux": "Linux",
    "windows": "Windows",
    "macos": "macOS",
    "ios": "iOS",
    "android": "Android",

    # 测试
    "jest": "Jest",
    "mocha": "Mocha",
    "cypress": "Cypress",
    "junit": "JUnit",
    "pytest": "pytest",

    # 协议 & 概念
    "http": "HTTP",
    "https": "HTTPS",
    "grpc": "gRPC",
    "graphql": "GraphQL",
    "restful": "RESTful",
    "rest": "RESTful",
    "websocket": "WebSocket",
    "微服务": "微服务架构",
    "分布式": "分布式系统",
    "高并发": "高并发",
    "高可用": "高可用",

    # 软技能
    "沟通能力": "沟通能力",
    "团队协作": "团队协作",
    "学习能力": "学习能力",
    "项目管理": "项目管理",
    "产品思维": "产品思维",
}


# ── 类别纠错映射表（Tier 2 - "其他"治理）──
# 将 LLM 可能错分为"其他"的技能名称映射到正确的 category
# key: 小写技能名称  →  value: (正确的 category, 正确的 skill_type)
_CATEGORY_FIX_MAP: dict[str, tuple[str, str]] = {
    # 标记语言 / Web 基础 — LLM 常把 HTML/CSS 扔到"其他"
    "html": ("编程语言", "hard"),
    "css": ("编程语言", "hard"),
    "html5": ("编程语言", "hard"),
    "css3": ("编程语言", "hard"),

    # 构建工具 — LLM 容易归到 DevOps 或"其他"
    "webpack": ("构建工具", "hard"),
    "vite": ("构建工具", "hard"),
    "rollup": ("构建工具", "hard"),
    "gulp": ("构建工具", "hard"),
    "babel": ("构建工具", "hard"),
    "esbuild": ("构建工具", "hard"),
    "cmake": ("构建工具", "hard"),
    "maven": ("构建工具", "hard"),
    "gradle": ("构建工具", "hard"),

    # 版本控制
    "git": ("版本控制", "hard"),
    "svn": ("版本控制", "hard"),
    "github": ("版本控制", "hard"),
    "gitlab": ("版本控制", "hard"),

    # 容器与编排
    "docker": ("容器与编排", "hard"),
    "kubernetes": ("容器与编排", "hard"),
    "docker compose": ("容器与编排", "hard"),
    "docker swarm": ("容器与编排", "hard"),
    "helm": ("容器与编排", "hard"),

    # API 与协议
    "http": ("API与协议", "hard"),
    "https": ("API与协议", "hard"),
    "grpc": ("API与协议", "hard"),
    "graphql": ("API与协议", "hard"),
    "restful": ("API与协议", "hard"),
    "websocket": ("API与协议", "hard"),
    "tcp/ip": ("API与协议", "hard"),
    "mqtt": ("API与协议", "hard"),

    # 架构模式
    "微服务架构": ("架构模式", "hard"),
    "分布式系统": ("架构模式", "hard"),
    "高并发": ("架构模式", "hard"),
    "高可用": ("架构模式", "hard"),
    "负载均衡": ("架构模式", "hard"),
    "服务治理": ("架构模式", "hard"),
    "领域驱动设计": ("架构模式", "hard"),
    "ddd": ("架构模式", "hard"),
    "事件驱动": ("架构模式", "hard"),
    "cqrs": ("架构模式", "hard"),
    "设计模式": ("架构模式", "hard"),

    # 大数据
    "hadoop": ("大数据", "hard"),
    "hive": ("大数据", "hard"),
    "apache spark": ("大数据", "hard"),
    "apache flink": ("大数据", "hard"),
    "presto": ("大数据", "hard"),
    "数据仓库": ("大数据", "domain"),
    "etl": ("大数据", "hard"),
    "数据治理": ("大数据", "domain"),

    # 移动开发
    "ios": ("移动开发", "hard"),
    "android": ("移动开发", "hard"),
    "react native": ("移动开发", "hard"),
    "flutter": ("移动开发", "hard"),
    "小程序开发": ("移动开发", "hard"),
    "uniapp": ("移动开发", "hard"),
    "harmonyos": ("移动开发", "hard"),

    # 安全
    "网络安全": ("安全", "hard"),
    "信息安全": ("安全", "hard"),
    "渗透测试": ("安全", "hard"),
    "前端安全": ("安全", "hard"),
    "xss防护": ("安全", "hard"),
    "csrf防护": ("安全", "hard"),
    "sql注入": ("安全", "hard"),

    # 设计工具
    "figma": ("设计工具", "tool"),
    "sketch": ("设计工具", "tool"),
    "photoshop": ("设计工具", "tool"),
    "axure": ("设计工具", "tool"),

    # 非开发工具
    "jira": ("项目管理", "tool"),
    "confluence": ("项目管理", "tool"),
    "office": ("通用技能", "tool"),
    "excel": ("通用技能", "tool"),

    # 人类语言
    "英语": ("通用技能", "language"),
    "日语": ("通用技能", "language"),
    "韩语": ("通用技能", "language"),
    "法语": ("通用技能", "language"),
    "德语": ("通用技能", "language"),
    "普通话": ("通用技能", "language"),
    "粤语": ("通用技能", "language"),
    "cet-4": ("通用技能", "certification"),
    "cet-6": ("通用技能", "certification"),
    "cet4": ("通用技能", "certification"),
    "cet6": ("通用技能", "certification"),

    # 证书
    "pmp": ("项目管理", "certification"),
    "aws certified": ("云平台", "certification"),
    "aws认证": ("云平台", "certification"),

    # 软技能常见别名归类
    "沟通能力": ("软技能", "soft"),
    "团队协作": ("软技能", "soft"),
    "协作能力": ("软技能", "soft"),
    "学习能力": ("软技能", "soft"),
    "领导力": ("软技能", "soft"),
    "抗压能力": ("软技能", "soft"),
    "责任心": ("软技能", "soft"),
    "创新能力": ("软技能", "soft"),
    "执行力": ("软技能", "soft"),
    "自驱力": ("软技能", "soft"),
    "逻辑思维": ("软技能", "soft"),
    "问题分析与解决能力": ("软技能", "soft"),
    "沟通协作能力": ("软技能", "soft"),
    "产品思维": ("软技能", "soft"),
    "用户体验意识": ("软技能", "soft"),
}


# ── 熟练度 → 数值映射 ──
_PROFICIENCY_RANK_MAP: dict[str, int] = {
    "了解": 1,
    "熟悉": 2,
    "熟练": 3,
    "精通": 4,
}


def normalize_skill_name(name: str) -> str:
    """将技能名称归一化为规范形式"""
    key = name.strip().lower()
    return _ALIAS_MAP.get(key, name.strip())


def fix_skill_category(skill: Skill) -> Skill:
    """修正技能的 category 和 skill_type（基于纠错字典）

    修正策略：
    1. 如果技能名命中纠错字典，强制使用字典中的 category 和 skill_type
    2. 如果 category 为"其他"且技能名命中字典，使用字典值
    3. 如果 skill_type 缺失但命中字典，补充 skill_type
    """
    key = skill.name.strip().lower()
    fix = _CATEGORY_FIX_MAP.get(key)

    if fix:
        correct_category, correct_skill_type = fix
        # category 为空或"其他"时，强制纠错
        if not skill.category or skill.category == "其他":
            skill.category = correct_category
        # skill_type 缺失时，补充
        if not skill.skill_type:
            skill.skill_type = correct_skill_type
    return skill


def compute_proficiency_rank(proficiency: Optional[str]) -> Optional[int]:
    """将文本熟练度映射为数值排名

    了解=1, 熟悉=2, 熟练=3, 精通=4, 其他(不限/None)=None
    """
    if not proficiency:
        return None
    return _PROFICIENCY_RANK_MAP.get(proficiency)


def parse_experience(experience: Optional[str]) -> tuple[Optional[int], Optional[int]]:
    """将经验字符串解析为 (min, max) 整数元组

    示例：
        "3-5年"    → (3, 5)
        "5年以上"  → (5, None)
        "不限"     → (None, None)
        "3年"      → (3, 3)
        None       → (None, None)
    """
    if not experience:
        return None, None

    exp = experience.strip()

    # "不限" / "无要求"
    if exp in ("不限", "无要求", "不要求"):
        return None, None

    # "3-5年" / "3~5年" / "3至5年"
    m = re.match(r"(\d+)\s*[-~～至]\s*(\d+)\s*年?", exp)
    if m:
        return int(m.group(1)), int(m.group(2))

    # "5年以上"
    m = re.match(r"(\d+)\s*年以上", exp)
    if m:
        return int(m.group(1)), None

    # "5年以下" / "5年以内"
    m = re.match(r"(\d+)\s*年以[下内]", exp)
    if m:
        return None, int(m.group(1))

    # "3年"
    m = re.match(r"(\d+)\s*年", exp)
    if m:
        val = int(m.group(1))
        return val, val

    return None, None


def normalize_skills(skills: list[Skill]) -> list[Skill]:
    """批量归一化技能列表：名称归一 + 类别纠错 + 熟练度映射 + 去重"""
    seen: set[str] = set()
    result: list[Skill] = []

    for skill in skills:
        # 1. 名称归一化
        normalized = normalize_skill_name(skill.name)
        skill.name = normalized

        # 2. 类别纠错
        fix_skill_category(skill)

        # 3. 熟练度数值映射
        skill.proficiency_rank = compute_proficiency_rank(skill.proficiency)

        # 4. 去重：相同名称只保留第一个
        if normalized.lower() not in seen:
            seen.add(normalized.lower())
            result.append(skill)

    return result