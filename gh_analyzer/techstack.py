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

# 目录名（精确匹配，小写）-> 用途
DIR_PURPOSES = {
    # 源代码与包结构
    "src": "源代码",
    "source": "源代码",
    "sources": "源代码",
    "lib": "核心库",
    "libs": "核心库",
    "library": "核心库",
    "pkg": "包",
    "packages": "包",
    "internal": "内部实现",
    "internals": "内部实现",
    "core": "核心逻辑",
    "common": "公共代码",
    "shared": "共享代码",
    "app": "应用主目录",
    "apps": "应用模块集合",
    "cmd": "命令行入口",
    "commands": "命令行入口",
    "cli": "命令行界面",
    "bin": "可执行文件/脚本",
    "modules": "模块",
    "components": "组件",
    "plugins": "插件",
    "addons": "扩展/插件",
    "extensions": "扩展",
    "handlers": "处理器",
    "middleware": "中间件",
    "middlewares": "中间件",
    "interceptors": "拦截器",
    "guards": "守卫",
    "filters": "过滤器",
    "validators": "校验器",
    "exceptions": "异常处理",
    "errors": "错误处理",
    "controllers": "控制器",
    "services": "服务层",
    "service": "服务层",
    "models": "数据模型",
    "model": "数据模型",
    "entities": "实体",
    "entity": "实体",
    "repositories": "数据访问层",
    "repository": "数据访问层",
    "dao": "数据访问层",
    "dto": "数据传输对象",
    "schemas": "数据结构/Schema",
    "schema": "数据结构/Schema",
    "types": "类型定义",
    "interfaces": "接口定义",
    "constants": "常量定义",
    "consts": "常量定义",
    "enums": "枚举定义",
    "utils": "工具函数",
    "util": "工具函数",
    "utils_helpers": "工具函数",
    "helpers": "辅助函数",
    "helper": "辅助函数",
    # API 与路由
    "api": "API 接口",
    "apis": "API 接口",
    "endpoints": "API 端点",
    "routes": "路由",
    "router": "路由",
    "routers": "路由",
    "views": "视图",
    "pages": "页面",
    "layouts": "布局",
    "partials": "局部视图",
    "templates": "模板",
    "template": "模板",
    # 测试
    "tests": "测试代码",
    "test": "测试代码",
    "testing": "测试代码",
    "spec": "测试/规范代码",
    "specs": "测试/规范代码",
    "e2e": "端到端测试",
    "integration": "集成测试",
    "unit": "单元测试",
    "fixtures": "测试数据/夹具",
    "testdata": "测试数据",
    "mocks": "Mock 数据",
    "mock": "Mock 数据",
    "stubs": "桩代码",
    "benchmarks": "基准测试",
    "benchmark": "基准测试",
    # 文档与示例
    "docs": "文档",
    "doc": "文档",
    "documentation": "文档",
    "examples": "示例代码",
    "example": "示例代码",
    "samples": "示例代码",
    "demo": "演示代码",
    "notebooks": "Notebook",
    "guides": "指南文档",
    "tutorials": "教程",
    # 脚本与工具
    "scripts": "脚本工具",
    "script": "脚本工具",
    "tools": "工具脚本",
    "tool": "工具脚本",
    "hack": "辅助脚本",
    "build_scripts": "构建脚本",
    # 构建与产物
    "build": "构建产物",
    "dist": "发布产物",
    "out": "输出产物",
    "output": "输出产物",
    "target": "构建产物",
    "release": "发布产物",
    "artifacts": "构建产物",
    # 资源与静态文件
    "assets": "静态资源",
    "static": "静态资源",
    "public": "静态公共资源",
    "images": "图片资源",
    "img": "图片资源",
    "icons": "图标资源",
    "fonts": "字体资源",
    "media": "媒体资源",
    "css": "样式文件",
    "styles": "样式文件",
    "themes": "主题",
    "locales": "多语言资源",
    "i18n": "国际化",
    "lang": "语言资源",
    "translations": "翻译资源",
    "vendor": "第三方依赖",
    "node_modules": "Node 依赖",
    "third_party": "第三方代码",
    # 配置
    "config": "配置",
    "configs": "配置",
    "conf": "配置",
    "settings": "配置",
    "environments": "环境配置",
    "profiles": "配置档",
    # 部署与基础设施
    "docker": "容器化配置",
    "deploy": "部署配置",
    "deployment": "部署配置",
    "deployments": "部署配置",
    "k8s": "Kubernetes 配置",
    "kubernetes": "Kubernetes 配置",
    "helm": "Helm 部署模板",
    "charts": "Helm Charts",
    "infra": "基础设施配置",
    "infrastructure": "基础设施配置",
    "terraform": "基础设施即代码",
    "ci": "CI 配置",
    "workflows": "CI 工作流",
    "hooks": "Git 钩子/脚本钩子",
    ".github": "GitHub 工作流/CI",
    ".gitlab": "GitLab 配置",
    ".circleci": "CircleCI 配置",
    ".husky": "Git 钩子",
    ".vscode": "编辑器配置",
    ".idea": "IDE 配置",
    ".devcontainer": "开发容器配置",
    # 数据
    "data": "数据文件",
    "datasets": "数据集",
    "db": "数据库相关",
    "database": "数据库相关",
    "sql": "SQL 脚本",
    "migrations": "数据库迁移",
    "migration": "数据库迁移",
    "seeds": "种子数据",
    "seed": "种子数据",
    # 运行时与日志
    "logs": "日志",
    "log": "日志",
    "tmp": "临时文件",
    "temp": "临时文件",
    "cache": "缓存",
    "caches": "缓存",
    "runtime": "运行时数据",
    # 依赖声明
    "requirements": "依赖声明",
    "deps": "依赖",
    "dependencies": "依赖",
}


# 目录名分词关键词 -> 用途（按顺序匹配，先命中的优先）
TOKEN_PURPOSES = [
    ("migration", "数据库迁移"),
    ("migrate", "数据库迁移"),
    ("benchmark", "基准测试"),
    ("integration", "集成测试"),
    ("e2e", "端到端测试"),
    ("test", "测试代码"),
    ("spec", "测试/规范代码"),
    ("fixture", "测试数据/夹具"),
    ("mock", "Mock 数据"),
    ("stub", "桩代码"),
    ("controller", "控制器"),
    ("handler", "处理器"),
    ("middleware", "中间件"),
    ("interceptor", "拦截器"),
    ("guard", "守卫"),
    ("filter", "过滤器"),
    ("validator", "校验器"),
    ("repository", "数据访问层"),
    ("dao", "数据访问层"),
    ("dto", "数据传输对象"),
    ("entity", "实体"),
    ("schema", "数据结构/Schema"),
    ("model", "数据模型"),
    ("service", "服务层"),
    ("endpoint", "API 端点"),
    ("route", "路由"),
    ("router", "路由"),
    ("view", "视图"),
    ("layout", "布局"),
    ("template", "模板"),
    ("page", "页面"),
    ("component", "组件"),
    ("module", "模块"),
    ("plugin", "插件"),
    ("extension", "扩展"),
    ("example", "示例代码"),
    ("sample", "示例代码"),
    ("demo", "演示代码"),
    ("tutorial", "教程"),
    ("notebook", "Notebook"),
    ("doc", "文档"),
    ("readme", "文档"),
    ("guide", "指南文档"),
    ("script", "脚本工具"),
    ("tool", "工具脚本"),
    ("helper", "辅助函数"),
    ("util", "工具函数"),
    ("common", "公共代码"),
    ("shared", "共享代码"),
    ("core", "核心逻辑"),
    ("config", "配置"),
    ("setting", "配置"),
    ("profile", "配置档"),
    ("environment", "环境配置"),
    ("deploy", "部署配置"),
    ("deployment", "部署配置"),
    ("workflow", "CI 工作流"),
    ("kubernetes", "Kubernetes 配置"),
    ("terraform", "基础设施即代码"),
    ("infra", "基础设施配置"),
    ("docker", "容器化配置"),
    ("helm", "Helm 模板"),
    ("chart", "Helm Charts"),
    ("asset", "静态资源"),
    ("static", "静态资源"),
    ("image", "图片资源"),
    ("icon", "图标资源"),
    ("font", "字体资源"),
    ("media", "媒体资源"),
    ("style", "样式文件"),
    ("theme", "主题"),
    ("locale", "多语言资源"),
    ("i18n", "国际化"),
    ("translation", "翻译资源"),
    ("vendor", "第三方依赖"),
    ("dataset", "数据集"),
    ("database", "数据库相关"),
    ("seed", "种子数据"),
    ("sql", "SQL 脚本"),
    ("log", "日志"),
    ("cache", "缓存"),
    ("tmp", "临时文件"),
    ("temp", "临时文件"),
    ("constant", "常量定义"),
    ("enum", "枚举定义"),
    ("interface", "接口定义"),
    ("type", "类型定义"),
    ("exception", "异常处理"),
    ("error", "错误处理"),
    ("api", "API 接口"),
]


# 重要文件（精确匹配文件名，小写）-> 用途说明
IMPORTANT_FILES = {
    # 文档
    "readme.md": "项目说明文档",
    "readme.rst": "项目说明文档",
    "readme": "项目说明文档",
    "readme.txt": "项目说明文档",
    "license": "开源许可证",
    "license.md": "开源许可证",
    "license.txt": "开源许可证",
    "licence": "开源许可证",
    "changelog.md": "变更日志",
    "changelog": "变更日志",
    "contributing.md": "贡献指南",
    "code_of_conduct.md": "行为准则",
    "security.md": "安全策略",
    "authors": "作者列表",
    "authors.md": "作者列表",
    # 构建与依赖
    "dockerfile": "容器镜像构建配置",
    "docker-compose.yml": "容器编排配置",
    "docker-compose.yaml": "容器编排配置",
    "compose.yml": "容器编排配置",
    "makefile": "构建自动化脚本",
    "justfile": "构建自动化脚本",
    "cmakelists.txt": "CMake 构建配置",
    "package.json": "Node 依赖与脚本",
    "package-lock.json": "Node 依赖锁定",
    "yarn.lock": "Yarn 依赖锁定",
    "pnpm-lock.yaml": "pnpm 依赖锁定",
    "requirements.txt": "Python 依赖声明",
    "requirements-dev.txt": "Python 开发依赖",
    "pyproject.toml": "Python 项目配置",
    "setup.py": "Python 打包配置",
    "setup.cfg": "Python 打包配置",
    "poetry.lock": "Poetry 依赖锁定",
    "pipfile": "Python 依赖声明",
    "go.mod": "Go 模块定义",
    "go.sum": "Go 依赖校验",
    "cargo.toml": "Rust 包配置",
    "cargo.lock": "Rust 依赖锁定",
    "pom.xml": "Maven 构建配置",
    "build.gradle": "Gradle 构建配置",
    "build.gradle.kts": "Gradle 构建配置",
    "settings.gradle": "Gradle 项目设置",
    "gradlew": "Gradle 包装脚本",
    "gemfile": "Ruby 依赖声明",
    "gemfile.lock": "Ruby 依赖锁定",
    "rakefile": "Rake 任务定义",
    "composer.json": "PHP 依赖声明",
    "composer.lock": "PHP 依赖锁定",
    "mix.exs": "Elixir 项目配置",
    "rebar.config": "Erlang 构建配置",
    # 配置
    ".gitignore": "Git 忽略规则",
    ".gitattributes": "Git 属性配置",
    ".gitmodules": "Git 子模块配置",
    ".dockerignore": "Docker 忽略规则",
    ".editorconfig": "编辑器风格配置",
    ".env.example": "环境变量示例",
    ".env.sample": "环境变量示例",
    ".env.template": "环境变量示例",
    ".prettierrc": "Prettier 配置",
    ".prettierrc.json": "Prettier 配置",
    ".prettierrc.js": "Prettier 配置",
    ".eslintrc": "ESLint 配置",
    ".eslintrc.js": "ESLint 配置",
    ".eslintrc.json": "ESLint 配置",
    ".eslintignore": "ESLint 忽略规则",
    "tsconfig.json": "TypeScript 配置",
    "vite.config.js": "Vite 配置",
    "vite.config.ts": "Vite 配置",
    "webpack.config.js": "Webpack 配置",
    "jest.config.js": "Jest 配置",
    "babel.config.js": "Babel 配置",
    ".flake8": "Flake8 配置",
    "tox.ini": "tox 配置",
    "mypy.ini": "mypy 配置",
    ".pylintrc": "pylint 配置",
    # 入口
    "main.py": "程序入口",
    "main.go": "程序入口",
    "main.rs": "程序入口",
    "main.c": "程序入口",
    "main.cpp": "程序入口",
    "app.py": "应用入口",
    "app.go": "应用入口",
    "manage.py": "Django 管理入口",
    "index.js": "入口文件",
    "index.ts": "入口文件",
    "index.html": "入口页面",
    "server.py": "服务入口",
    "wsgi.py": "WSGI 入口",
    "asgi.py": "ASGI 入口",
}


def important_file_purpose(filename: str) -> str:
    """返回重要文件的用途说明；非重要文件返回空字符串。"""
    return IMPORTANT_FILES.get(filename.lower(), "")


def infer_dir_purpose(name: str, files: list[str]) -> str:
    """推断单个目录的用途：精确名 -> 关键词 -> 内容特征 -> 兜底。"""
    lowered = name.lower()

    # 1. 精确匹配
    if lowered in DIR_PURPOSES:
        return DIR_PURPOSES[lowered]

    # 2. 分词后做关键词匹配
    tokens = _tokens(lowered)
    for keyword, purpose in TOKEN_PURPOSES:
        if keyword in tokens:
            return purpose

    # 3. 根据目录内文件内容推断
    purpose = _infer_by_content(files)
    if purpose:
        return purpose

    # 4. 兜底：目录内是否有代码文件
    if any(LANGUAGE_BY_EXTENSION.get(_ext(f)) for f in files):
        return "代码目录"
    return "其他目录"


def _tokens(name: str) -> set[str]:
    """把目录名拆成小写单词集合（处理 camelCase / snake_case / kebab-case）。"""
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return set(s.split())


def _infer_by_content(files: list[str]) -> str:
    """根据目录内文件的名字/扩展名推断用途。"""
    if not files:
        return ""
    names = [f.rsplit("/", 1)[-1].lower() for f in files]
    exts = {_ext(f) for f in files}

    # 关键文件名
    if any(n == "dockerfile" for n in names):
        return "容器化配置"
    if any(n in ("makefile", "cmakelists.txt", "justfile") for n in names):
        return "构建配置"

    # 测试文件特征：test_*.py、*_test.go、*.spec.ts 等；测试文件需占多数，
    # 避免把「源码 + 少量测试」的目录误判为纯测试目录
    test_pattern = re.compile(r"(^|[_./-])(test|spec)(s)?($|[_./-])")
    test_count = sum(1 for n in names if test_pattern.search(n))
    if test_count and test_count * 2 > len(names):
        return "测试代码"

    # 扩展名特征（按目录内全部文件的扩展名集合判断）
    if ".sql" in exts:
        return "SQL 脚本"
    if exts and exts <= {".md", ".mdx", ".rst", ".txt"}:
        return "文档"
    if exts and exts <= {".json", ".yaml", ".yml", ".toml", ".ini", ".conf", ".env", ".properties"}:
        return "配置"
    if exts and exts <= {".sh", ".bash", ".zsh", ".bat", ".ps1"}:
        return "脚本"
    if exts and exts <= {".html", ".htm", ".css", ".scss", ".less", ".js", ".ts", ".png", ".jpg", ".jpeg", ".svg", ".gif", ".ico", ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".webp"}:
        return "静态资源"

    return ""


@dataclass
class TechStack:
    """检测出的技术栈。"""

    languages: list[tuple[str, int]] = field(default_factory=list)  # (名称, 字节数)
    frameworks: list[str] = field(default_factory=list)
    databases: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    file_count_by_language: dict[str, int] = field(default_factory=dict)
    total_files: int = 0
    structure: "StructureNode" = None  # 根节点，目录树 + 重要文件

    @property
    def primary_language(self) -> str:
        return self.languages[0][0] if self.languages else "未知"


def detect_tech_stack(data: RepoData) -> TechStack:
    """综合仓库数据，输出技术栈。"""
    stack = TechStack()

    # 1. 语言（优先用 GitHub 的语言统计，缺失或全为 0 时按扩展名统计）
    if data.languages and sum(data.languages.values()) > 0:
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

    # 4. 完整目录结构（每个目录推断用途，并标注重要文件）
    stack.structure = analyze_structure(data.files)

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


@dataclass
class StructureNode:
    """目录树节点，包含子目录和该目录下的重要文件。"""

    name: str = ""
    purpose: str = ""
    file_count: int = 0  # 直接位于该目录下的文件数
    dirs: list["StructureNode"] = field(default_factory=list)
    files: list[dict] = field(default_factory=list)  # [{"name", "purpose"}]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "purpose": self.purpose,
            "file_count": self.file_count,
            "dirs": [d.to_dict() for d in self.dirs],
            "files": self.files,
        }


def analyze_structure(files: list[str]) -> StructureNode:
    """构建嵌套目录树，标注每个目录的用途和重要文件。"""
    # 统计每个目录下（递归）的全部文件，供用途推断使用
    files_by_dir: dict[str, list[str]] = {}
    for path in files:
        parts = path.split("/")
        for i in range(1, len(parts)):
            dir_path = "/".join(parts[:i])
            files_by_dir.setdefault(dir_path, []).append(path)

    root = StructureNode()
    for path in sorted(files):
        parts = path.split("/")
        node = root
        for part in parts[:-1]:
            child = next((d for d in node.dirs if d.name == part), None)
            if child is None:
                child = StructureNode(name=part)
                node.dirs.append(child)
            node = child
        filename = parts[-1]
        node.file_count += 1
        purpose = important_file_purpose(filename)
        if purpose:
            node.files.append({"name": filename, "purpose": purpose})

    _annotate_structure(root, "", files_by_dir)
    return root


def _annotate_structure(node: StructureNode, path: str, files_by_dir: dict) -> None:
    """递归为每个目录节点推断用途。"""
    for child in node.dirs:
        child_path = f"{path}/{child.name}" if path else child.name
        child.purpose = infer_dir_purpose(child.name, files_by_dir.get(child_path, []))
        _annotate_structure(child, child_path, files_by_dir)


def render_structure_tree(root: StructureNode) -> str:
    """把嵌套目录树渲染成带用途说明的文本树（目录在前、文件在后）。"""
    if root is None:
        return ""
    lines: list[str] = []

    def walk(node: StructureNode, prefix: str) -> None:
        dirs = sorted(node.dirs, key=lambda d: d.name.lower())
        files = sorted(node.files, key=lambda f: f["name"].lower())
        items: list[tuple] = [(d, True) for d in dirs] + [(f, False) for f in files]
        for i, (item, is_dir) in enumerate(items):
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "
            if is_dir:
                count = f" ({item.file_count} 个文件)" if item.file_count else ""
                lines.append(f"{prefix}{connector}{item.name}/  # {item.purpose}{count}")
                walk(item, prefix + ("    " if is_last else "│   "))
            else:
                lines.append(f"{prefix}{connector}{item['name']}  # {item['purpose']}")

    walk(root, "")
    return "\n".join(lines)


def _add_unique(items: list[str], item: str) -> None:
    if item not in items:
        items.append(item)
