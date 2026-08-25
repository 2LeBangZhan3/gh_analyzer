"""生成项目总结。"""

from __future__ import annotations

import re

from .github import RepoData
from .techstack import TechStack


def generate_summary(data: RepoData, stack: TechStack) -> str:
    """生成一段结构化的项目总结（Markdown 文本）。"""
    lines: list[str] = []

    # 简介
    lines.append("## 项目总结")
    lines.append("")
    intro = data.description or _first_sentence(data.readme) or "（仓库未提供描述）"
    lines.append(f"**简介**：{intro}")
    lines.append("")

    # 基本信息
    lines.append("**基本信息**")
    lines.append("")
    lines.append(f"- 仓库地址：{data.url}")
    lines.append(f"- Star：{data.stars}　Fork：{data.forks}")
    lines.append(f"- 默认分支：{data.default_branch}")
    lines.append(f"- 文件总数：{stack.total_files}")
    if data.topics:
        lines.append(f"- 主题标签：{'、'.join(data.topics)}")
    lines.append("")

    # 技术定位
    lines.append("**技术定位**")
    lines.append("")
    primary = stack.primary_language
    if stack.languages:
        lang_text = "、".join(f"{name} ({pct}%)" for name, pct in stack.languages[:5])
        lines.append(f"- 主要语言：{lang_text}")
    if stack.frameworks:
        lines.append(f"- 核心框架：{'、'.join(stack.frameworks)}")
    if stack.databases:
        lines.append(f"- 数据存储：{'、'.join(stack.databases)}")
    if stack.tools:
        lines.append(f"- 工程化工具：{'、'.join(stack.tools)}")
    lines.append("")

    # 项目规模（按语言统计文件数）
    if stack.file_count_by_language:
        lines.append("**项目规模（按语言统计文件数）**")
        lines.append("")
        for lang, count in sorted(
            stack.file_count_by_language.items(), key=lambda kv: kv[1], reverse=True
        )[:8]:
            lines.append(f"- {lang}：{count} 个文件")
        lines.append("")

    # 目录结构解读
    if stack.top_dirs:
        lines.append("**目录结构解读**")
        lines.append("")
        lines.append("| 目录 | 用途 |")
        lines.append("| --- | --- |")
        for name, purpose in stack.top_dirs:
            lines.append(f"| `{name}/` | {purpose or '—'} |")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _first_sentence(text: str) -> str:
    """取 README 的第一句话作为简介。"""
    for line in text.splitlines():
        line = re.sub(r"[#>*_\-\s]+", " ", line).strip()
        if not line:
            continue
        sentence = re.split(r"[。.!！?？]", line)[0].strip()
        if sentence:
            return sentence[:160]
    return ""
