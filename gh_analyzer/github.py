"""从 GitHub 或本地目录获取仓库数据。

支持三种数据来源：

1. GitHub API（默认，推荐）：读取仓库元数据、语言统计、文件树和关键文件内容。
2. ``git clone``：当 API 被限流或没有 token 时，可浅克隆后本地分析。
3. 本地目录：直接分析一个已经存在的本地项目。
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

API_BASE = "https://api.github.com"

# 需要读取内容以识别框架/依赖/数据库的关键文件
DEPENDENCY_FILES = (
    "requirements.txt",
    "requirements-dev.txt",
    "Pipfile",
    "Pipfile.lock",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "package.json",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "go.mod",
    "go.sum",
    "Cargo.toml",
    "Cargo.lock",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
    "Gemfile",
    "Gemfile.lock",
    "composer.json",
    "composer.lock",
    "build.sbt",
    "mix.exs",
    "pubspec.yaml",
    "Project.toml",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "Makefile",
    "CMakeLists.txt",
    ".gitlab-ci.yml",
)

# 遍历本地目录时需要跳过的路径
SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "vendor",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".tox",
    "dist",
    "build",
    "target",
    ".idea",
    ".vscode",
    ".mypy_cache",
    ".pytest_cache",
}


class GitHubError(Exception):
    """获取 GitHub 数据时发生的错误。"""


@dataclass
class RepoData:
    """统一的仓库数据表示，供后续分析模块使用。"""

    owner: str
    repo: str
    description: str = ""
    homepage: str = ""
    stars: int = 0
    forks: int = 0
    default_branch: str = "main"
    topics: list[str] = field(default_factory=list)
    languages: dict[str, int] = field(default_factory=dict)
    files: list[str] = field(default_factory=list)
    file_contents: dict[str, str] = field(default_factory=dict)
    readme: str = ""
    source: str = "api"

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.repo}"

    @property
    def url(self) -> str:
        return f"https://github.com/{self.owner}/{self.repo}"


def parse_repo_url(url: str) -> tuple[str, str]:
    """把用户输入的地址解析为 (owner, repo)。

    支持 ``https://github.com/owner/repo``、``git@github.com:owner/repo.git``、
    以及简写 ``owner/repo``。
    """
    url = url.strip().rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]

    patterns = (
        r"github\.com[:/]([\w.-]+)/([\w.-]+)",
        r"^([\w.-]+)/([\w.-]+)$",
    )
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            owner, repo = match.group(1), match.group(2)
            if repo:
                return owner, repo
    raise ValueError(f"无法解析 GitHub 地址: {url!r}")


def _api_request(path: str, token: str | None = None, raw: bool = False) -> object:
    """请求 GitHub API 并返回 JSON（或 raw 文本）。"""
    headers = {
        "Accept": "application/vnd.github.raw" if raw else "application/vnd.github+json",
        "User-Agent": "gh-analyzer",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(API_BASE + path, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return body if raw else json.loads(body)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise GitHubError(f"仓库不存在或无权访问: {path}") from exc
        if exc.code in (403, 429):
            raise GitHubError(
                "GitHub API 访问受限（可能触发限流）。"
                "请设置 GITHUB_TOKEN 环境变量，或改用 --clone / --local。"
            ) from exc
        raise GitHubError(f"GitHub API 请求失败（HTTP {exc.code}）: {path}") from exc
    except urllib.error.URLError as exc:
        raise GitHubError(f"无法连接到 GitHub: {exc.reason}") from exc


def _resolve_token(explicit: str | None) -> str | None:
    """按优先级解析 token：显式参数 > GITHUB_TOKEN > GH_TOKEN > gh CLI。"""
    if explicit:
        return explicit
    for var in ("GITHUB_TOKEN", "GH_TOKEN"):
        value = os.environ.get(var)
        if value:
            return value
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        token = result.stdout.strip()
        return token or None
    except (OSError, subprocess.SubprocessError):
        return None


def fetch_via_api(url: str, token: str | None = None) -> RepoData:
    """通过 GitHub API 获取仓库数据。"""
    owner, repo = parse_repo_url(url)
    token = _resolve_token(token)

    meta = _api_request(f"/repos/{owner}/{repo}", token)
    assert isinstance(meta, dict)

    languages = _api_request(f"/repos/{owner}/{repo}/languages", token)
    assert isinstance(languages, dict)

    default_branch = meta.get("default_branch") or "main"
    tree = _api_request(
        f"/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1", token
    )
    assert isinstance(tree, dict)

    files: list[str] = []
    for entry in tree.get("tree", []):
        if entry.get("type") == "blob":
            path = entry.get("path", "")
            if path and not _is_skipped_path(path):
                files.append(path)

    readme = _fetch_readme(owner, repo, token)
    file_contents = _fetch_dependency_files(owner, repo, files, token)

    data = RepoData(
        owner=owner,
        repo=repo,
        description=(meta.get("description") or "").strip(),
        homepage=meta.get("homepage") or "",
        stars=int(meta.get("stargazers_count") or 0),
        forks=int(meta.get("forks_count") or 0),
        default_branch=default_branch,
        topics=list(meta.get("topics") or []),
        languages={k: int(v) for k, v in languages.items()},
        files=files,
        file_contents=file_contents,
        readme=readme,
        source="api",
    )
    return data


def fetch_via_clone(url: str, token: str | None = None) -> tuple[RepoData, str]:
    """浅克隆仓库到临时目录后做本地分析，返回 (数据, 临时目录)。"""
    owner, repo = parse_repo_url(url)
    token = _resolve_token(token)

    tmp_dir = tempfile.mkdtemp(prefix="gh_analyzer_")
    clone_url = url if url.startswith(("http://", "https://", "git@")) else f"https://github.com/{owner}/{repo}.git"
    if token and clone_url.startswith("https://"):
        parsed = urllib.parse.urlparse(clone_url)
        clone_url = parsed._replace(netloc=f"x-access-token:{token}@{parsed.netloc}").geturl()

    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", clone_url, tmp_dir],
            check=True,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise GitHubError(f"git clone 失败: {exc}") from exc

    data = fetch_from_local(tmp_dir)
    data.owner, data.repo = owner, repo
    data.source = "clone"
    return data, tmp_dir


def fetch_from_local(path: str) -> RepoData:
    """分析一个本地目录，构造与 API 相同的统一数据结构。"""
    path = os.path.abspath(path)
    if not os.path.isdir(path):
        raise GitHubError(f"目录不存在: {path}")

    files: list[str] = []
    for root, dirs, names in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in names:
            full = os.path.join(root, name)
            rel = os.path.relpath(full, path).replace(os.sep, "/")
            files.append(rel)

    file_contents: dict[str, str] = {}
    readme = ""
    languages: dict[str, int] = {}

    for rel in files:
        full = os.path.join(path, rel)
        try:
            size = os.path.getsize(full)
        except OSError:
            size = 0
        ext = _language_from_path(rel)
        if ext:
            languages[ext] = languages.get(ext, 0) + size

        base = rel.rsplit("/", 1)[-1].lower()
        if base in ("readme.md", "readme.rst", "readme.txt", "readme"):
            readme = _read_text(full)
        if base in DEPENDENCY_FILES:
            file_contents[rel] = _read_text(full)

    description = ""
    for line in readme.splitlines():
        line = line.strip().lstrip("#").strip()
        if line:
            description = line[:120]
            break

    return RepoData(
        owner="local",
        repo=os.path.basename(path),
        description=description,
        languages=languages,
        files=files,
        file_contents=file_contents,
        readme=readme,
        source="local",
    )


def _fetch_readme(owner: str, repo: str, token: str | None) -> str:
    """尝试获取 README，不存在时返回空字符串。"""
    try:
        content = _api_request(f"/repos/{owner}/{repo}/readme", token, raw=True)
        return content if isinstance(content, str) else ""
    except GitHubError:
        return ""


def _fetch_dependency_files(
    owner: str, repo: str, files: list[str], token: str | None
) -> dict[str, str]:
    """读取文件树中出现的依赖文件内容，用于识别框架与数据库。"""
    contents: dict[str, str] = {}
    for path in files:
        base = path.rsplit("/", 1)[-1].lower()
        if base in DEPENDENCY_FILES:
            try:
                quoted = urllib.parse.quote(path, safe="/")
                content = _api_request(f"/repos/{owner}/{repo}/contents/{quoted}", token, raw=True)
                if isinstance(content, str) and len(content) < 1_000_000:
                    contents[path] = content
            except GitHubError:
                continue
    return contents


def _read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def _is_skipped_path(path: str) -> bool:
    parts = path.split("/")
    return any(part in SKIP_DIRS for part in parts)


def _language_from_path(path: str) -> str:
    """根据扩展名粗略映射语言（本地模式用）。"""
    ext = os.path.splitext(path)[1].lower()
    mapping = {
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
        ".vue": "Vue",
        ".svelte": "Svelte",
        ".sql": "SQL",
        ".sh": "Shell",
        ".bash": "Shell",
    }
    return mapping.get(ext, "")
