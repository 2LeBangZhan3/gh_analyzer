"""技术栈检测：识别语言、框架、数据库与工程化工具。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .github import RepoData

# 框架/库标识 -> 显示名称（在依赖文件内容中做大小写不敏感匹配）
FRAMEWORK_MARKERS = {
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "starlette": "Starlette",
    "tornado": "Tornado",
    "sqlalchemy": "SQLAlchemy",
    "celery": "Celery",
    "pytest": "pytest",
    "pandas": "pandas",
    "numpy": "NumPy",
    "scipy": "SciPy",
    "scikit-learn": "scikit-learn",
    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",
    "torch": "PyTorch",
    "keras": "Keras",
    "transformers": "Hugging Face Transformers",
    "react": "React",
    "vue": "Vue.js",
    "angular": "Angular",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "nuxt": "Nuxt.js",
    "svelte": "Svelte",
    "express": "Express",
    "nestjs": "NestJS",
    "koa": "Koa",
    "fastify": "Fastify",
    "redux": "Redux",
    "tailwindcss": "Tailwind CSS",
    "vite": "Vite",
    "webpack": "Webpack",
    "jest": "Jest",
    "mocha": "Mocha",
    "typescript": "TypeScript",
    "gin-gonic": "Gin",
    "gin": "Gin",
    "echo": "Echo",
    "gorm": "GORM",
    "spring": "Spring",
    "spring-boot": "Spring Boot",
    "rails": "Ruby on Rails",
    "laravel": "Laravel",
    "symfony": "Symfony",
    "actix": "Actix",
    "tokio": "Tokio",
    "serde": "serde",
    "bevy": "Bevy",
    "axios": "axios",
}

DATABASE_MARKERS = {
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "psycopg": "PostgreSQL",
    "mysql": "MySQL",
    "mariadb": "MariaDB",
    "sqlite": "SQLite",
    "mongodb": "MongoDB",
    "mongoose": "MongoDB",
    "pymongo": "MongoDB",
    "redis": "Redis",
    "elasticsearch": "Elasticsearch",
    "clickhouse": "ClickHouse",
    "cassandra": "Cassandra",
    "neo4j": "Neo4j",
    "dynamodb": "DynamoDB",
    "bigquery": "BigQuery",
}

# 工程化/基础设施标识
TOOL_MARKERS = {
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "helm": "Helm",
    "terraform": "Terraform",
    "docker-compose": "Docker Compose",
    "github actions": "GitHub Actions",
    "gitlab-ci": "GitLab CI",
    "jenkins": "Jenkins",
    "travis": "Travis CI",
    "circleci": "CircleCI",
    "gunicorn": "Gunicorn",
    "uvicorn": "Uvicorn",
    "nginx": "Nginx",
    "eslint": "ESLint",
    "prettier": "Prettier",
}

LANGUAGE_BY_EXTENSION = {
    ".py": "Python",
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".rb": "Ruby",
    ".php": "PHP",
    ".c": "C",
    ".h": "C",
    ".cc": "C++",
    ".cpp": "C++",
    ".hpp": "C++",
    ".cxx": "C++",
    ".cs": "C#",
    ".swift": "Swift",
    ".scala": "Scala",
    ".dart": "Dart",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".erl": "Erlang",
    ".hs": "Haskell",
    ".clj": "Clojure",
    ".lua": "Lua",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".sql": "SQL",
    ".sh": "Shell",
    ".bash": "Shell",
}

# 顶级目录的常见用途描述
DIR_PURPOSES = {
    "src": "源代码",
    "lib": "核心库",
    "pkg": "包",
    "app": "应用主目录",
    "api": "API 接口",
    "cmd": "命令行入口",
    "internal": "内部实现",
    "tests": "测试代码",
    "test": "测试代码",
    "spec": "测试代码",
    "docs": "文档",
    "doc": "文档",
    "examples": "示例",
    "example": "示例",
    "scripts": "脚本",
    "tools": "工具脚本",
    "docker": "容器化配置",
    "deploy": "部署配置",
    "deployment": "部署配置",
    "config": "配置",
    "configs": "配置",
    "assets": "静态资源",
    "static": "静态资源",
    "public": "公共资源",
    "migrations": "数据库迁移",
    "fixtures": "测试数据",
    ".github": "GitHub 工作流/CI",
    ".gitlab": "GitLab 配置",
}


@dataclass
class TechStack:
    """检测出的技术栈。"""

    languages: list[tuple[str, int]] = field(default_factory=list)  # (名称, 字节数)
    frameworks: list[str] = field(default_factory=list)
    databases: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    file_count_by_language: dict[str, int] = field(default_factory=dict)
    total_files: int = 0
    top_dirs: list[tuple[str, str]] = field(default_factory=list)  # (目录, 用途)

    @property
    def primary_language(self) -> str:
        return self.languages[0][0] if self.languages else "未知"


def detect_tech_stack(data: RepoData) -> TechStack:
    """综合仓库数据，输出技术栈。"""
    stack = TechStack()

    # 1. 语言（优先用 GitHub 的语言统计，缺失时按扩展名统计）
    if data.languages:
        total = sum(data.languages.values())
        ranked = sorted(data.languages.items(), key=lambda kv: kv[1], reverse=True)
        stack.languages = [(name, round(100 * count / total, 1)) for name, count in ranked]
    else:
        stack.languages = _languages_from_extensions(data.files)

    # 2. 按扩展名统计文件数
    for path in data.files:
        ext = _ext(path)
        lang = LANGUAGE_BY_EXTENSION.get(ext)
        if lang:
            stack.file_count_by_language[lang] = stack.file_count_by_language.get(lang, 0) + 1
    stack.total_files = len(data.files)

    # 3. 框架 / 数据库 / 工具：扫描依赖文件内容 + 文件路径
    blob = "\n".join(data.file_contents.values()).lower()
    stack.frameworks = _detect(blob, FRAMEWORK_MARKERS)
    stack.databases = _detect(blob, DATABASE_MARKERS)
    stack.tools = _detect(blob, TOOL_MARKERS)

    # 通过文件路径补充工具检测（如 Dockerfile、CI 配置）
    paths = " ".join(data.files).lower()
    if "dockerfile" in paths:
        _add_unique(stack.tools, "Docker")
    if ".github/workflows" in paths:
        _add_unique(stack.tools, "GitHub Actions")
    if "makefile" in paths:
        _add_unique(stack.tools, "Make")

    # 4. 顶级目录结构
    stack.top_dirs = _analyze_top_dirs(data.files)

    return stack


def _languages_from_extensions(files: list[str]) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for path in files:
        lang = LANGUAGE_BY_EXTENSION.get(_ext(path))
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
    total = sum(counts.values()) or 1
    ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    return [(name, round(100 * count / total, 1)) for name, count in ranked]


def _detect(blob: str, markers: dict[str, str]) -> list[str]:
    found: list[str] = []
    for marker, name in markers.items():
        if _contains_word(blob, marker) and name not in found:
            found.append(name)
    return found


def _contains_word(text: str, marker: str) -> bool:
    """子串匹配，但对含空格的标识做宽松处理。"""
    if " " in marker:
        return marker in text
    pattern = rf"(?<![a-z0-9_-]){re.escape(marker)}(?![a-z0-9_-])"
    return re.search(pattern, text) is not None


def _ext(path: str) -> str:
    dot = path.rfind(".")
    if dot == -1:
        return ""
    return path[dot:].lower()


def _analyze_top_dirs(files: list[str]) -> list[tuple[str, str]]:
    top: dict[str, int] = {}
    for path in files:
        parts = path.split("/")
        if len(parts) > 1 and not parts[0].startswith("."):
            top[parts[0]] = top.get(parts[0], 0) + 1
    ranked = sorted(top.items(), key=lambda kv: kv[1], reverse=True)[:12]
    return [(name, DIR_PURPOSES.get(name, "")) for name, _ in ranked]


def _add_unique(items: list[str], item: str) -> None:
    if item not in items:
        items.append(item)
