#!/usr/bin/env python3
"""AI GitHub 仓库分析助手。

输入一个 GitHub 仓库地址，自动分析项目结构、生成技术栈报告、项目总结和面试题。

用法示例：
    python3 analyzer.py https://github.com/psf/requests
    python3 analyzer.py owner/repo --output report.md
    python3 analyzer.py --local ./my-project
    python3 analyzer.py https://github.com/psf/requests --clone
"""

import argparse
import shutil
import sys

from gh_analyzer.github import (
    GitHubError,
    fetch_from_local,
    fetch_via_api,
    fetch_via_clone,
)
from gh_analyzer.report import build_report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AI GitHub 仓库分析助手：分析项目结构、技术栈并生成总结与面试题。"
    )
    parser.add_argument(
        "repo",
        nargs="?",
        help="GitHub 仓库地址（如 https://github.com/owner/repo 或 owner/repo）",
    )
    parser.add_argument(
        "--local",
        metavar="PATH",
        help="直接分析本地目录，而不是从 GitHub 获取",
    )
    parser.add_argument(
        "--clone",
        action="store_true",
        help="通过 git clone 获取仓库（在 API 限流时使用）",
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        help="将报告写入指定文件（默认打印到标准输出）",
    )
    parser.add_argument(
        "--token",
        help="GitHub API token（也可通过 GITHUB_TOKEN 环境变量提供）",
    )
    args = parser.parse_args()

    if args.local:
        try:
            data = fetch_from_local(args.local)
        except GitHubError as exc:
            print(f"错误：{exc}", file=sys.stderr)
            return 1
    elif args.repo:
        try:
            if args.clone:
                data, tmp_dir = fetch_via_clone(args.repo, args.token)
            else:
                data = fetch_via_api(args.repo, args.token)
        except (GitHubError, ValueError) as exc:
            print(f"错误：{exc}", file=sys.stderr)
            return 1
    else:
        parser.print_help()
        return 1

    report = build_report(data)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"报告已写入: {args.output}")
    else:
        print(report)

    # 清理 clone 产生的临时目录
    if args.clone and not args.local and args.repo:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
