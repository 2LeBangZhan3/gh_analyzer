#!/usr/bin/env python3
"""AI GitHub 仓库分析助手 —— 交互式 Web 界面。

启动后访问 http://127.0.0.1:8000 即可在浏览器中使用。

用法：
    python3 webapp.py                 # 默认 127.0.0.1:8000
    python3 webapp.py --port 9000     # 指定端口
    python3 webapp.py --host 0.0.0.0  # 允许局域网访问
    python3 webapp.py --token <TOKEN> # 提供 GitHub token（也可用 GITHUB_TOKEN）
"""

import argparse
import json
import os
import shutil
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from gh_analyzer.github import (
    GitHubError,
    fetch_via_api,
    fetch_via_clone,
)
from gh_analyzer.interview import generate_questions
from gh_analyzer.techstack import TechStack, detect_tech_stack

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
INDEX_HTML = os.path.join(STATIC_DIR, "index.html")


def _analyze(url: str, mode: str, token: str | None) -> dict:
    """执行分析并返回可 JSON 序列化的结构化结果。"""
    tmp_dir: str | None = None
    try:
        if mode == "clone":
            data, tmp_dir = fetch_via_clone(url, token)
        else:
            data = fetch_via_api(url, token)
    except (GitHubError, ValueError) as exc:
        raise GitHubError(str(exc)) from exc

    try:
        stack = detect_tech_stack(data)
        questions = generate_questions(data, stack)
        result = {
            "meta": {
                "full_name": data.full_name,
                "url": data.url,
                "description": data.description,
                "stars": data.stars,
                "forks": data.forks,
                "topics": data.topics,
                "default_branch": data.default_branch,
            },
            "tech_stack": _stack_to_dict(stack),
            "questions": [{"category": c, "question": q} for c, q in questions],
        }
        return result
    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)


def _stack_to_dict(stack: TechStack) -> dict:
    return {
        "primary_language": stack.primary_language,
        "languages": [{"name": name, "pct": pct} for name, pct in stack.languages],
        "frameworks": stack.frameworks,
        "databases": stack.databases,
        "tools": stack.tools,
        "structure": stack.structure.to_dict() if stack.structure else None,
        "file_count_by_language": stack.file_count_by_language,
        "total_files": stack.total_files,
    }


class Handler(BaseHTTPRequestHandler):
    token: str | None = None

    def do_GET(self):  # noqa: D102
        parsed = urlparse(self.path)

        if parsed.path in ("/", "/index.html"):
            self._serve_index()
        elif parsed.path == "/api/health":
            self._json({"status": "ok"})
        elif parsed.path == "/api/analyze":
            self._handle_analyze(parsed)
        else:
            self._json({"error": "未找到该路径"}, status=404)

    def do_POST(self):  # noqa: D102
        parsed = urlparse(self.path)
        if parsed.path == "/api/analyze":
            self._handle_analyze(parsed)
        else:
            self._json({"error": "未找到该路径"}, status=404)

    def _handle_analyze(self, parsed) -> None:
        query = parse_qs(parsed.query)
        url = (query.get("url") or [""])[0].strip()
        mode = (query.get("mode") or ["api"])[0]

        if not url:
            self._json({"error": "请提供 GitHub 仓库地址"}, status=400)
            return
        if mode not in ("api", "clone"):
            self._json({"error": "mode 参数仅支持 api 或 clone"}, status=400)
            return

        try:
            result = _analyze(url, mode, self.token)
        except GitHubError as exc:
            self._json({"error": str(exc)}, status=502)
            return
        except Exception as exc:  # 兜底，避免服务端异常直接返回 HTML
            self._json({"error": f"分析失败：{exc}"}, status=500)
            return

        self._json(result)

    def _serve_index(self) -> None:
        try:
            with open(INDEX_HTML, "rb") as fh:
                body = fh.read()
        except OSError:
            self._json({"error": "缺少 static/index.html 文件"}, status=500)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:  # noqa: D102
        # 精简日志，避免刷屏
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description="AI GitHub 仓库分析助手 Web 界面")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址（默认 127.0.0.1）")
    parser.add_argument("--port", type=int, default=8000, help="监听端口（默认 8000）")
    parser.add_argument("--token", help="GitHub API token（也可通过 GITHUB_TOKEN 提供）")
    args = parser.parse_args()

    if args.token:
        Handler.token = args.token
    elif os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"):
        Handler.token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{args.port}"
    print(f"GH Analyzer Web 界面已启动：{url}")
    print("按 Ctrl+C 停止服务。")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
