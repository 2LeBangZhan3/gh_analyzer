"""把分析结果渲染为 Markdown 报告。"""

from __future__ import annotations

from .github import RepoData
from .summary import generate_summary
from .techstack import TechStack, detect_tech_stack, render_directory_tree


def build_report(data: RepoData) -> str:
    """生成完整的 Markdown 分析报告。"""
    stack = detect_tech_stack(data)

    parts: list[str] = []
    parts.append(f"# GitHub 仓库分析报告：{data.full_name}")
    parts.append("")
    parts.append(_tech_stack_section(stack))
    parts.append(_structure_section(stack))
    parts.append(generate_summary(data, stack))
    parts.append(_interview_section(data, stack))
    return "\n".join(parts)


def _structure_section(stack: TechStack) -> str:
    """渲染完整的目录结构（每个目录都标注用途）。"""
    tree = render_directory_tree(stack.directories)
    if not tree:
        return ""
    lines = ["## 项目结构", ""]
    lines.append("```text")
    lines.append(tree)
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def _tech_stack_section(stack: TechStack) -> str:
    lines = ["## 技术栈报告", ""]

    if stack.languages:
        lines.append("### 语言分布")
        lines.append("")
        lines.append("| 语言 | 占比 |")
        lines.append("| --- | --- |")
        for name, pct in stack.languages[:8]:
            lines.append(f"| {name} | {pct}% |")
        lines.append("")

    if stack.frameworks:
        lines.append("### 框架与库")
        lines.append("")
        lines.append("、".join(stack.frameworks))
        lines.append("")

    if stack.databases:
        lines.append("### 数据库 / 存储")
        lines.append("")
        lines.append("、".join(stack.databases))
        lines.append("")

    if stack.tools:
        lines.append("### 工程化 / 基础设施")
        lines.append("")
        lines.append("、".join(stack.tools))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _interview_section(data: RepoData, stack: TechStack) -> str:
    from .interview import generate_questions  # 延迟导入，避免循环依赖

    questions = generate_questions(data, stack)
    if not questions:
        return ""

    lines = ["## 面试题", ""]
    current_category = None
    index = 0
    for category, question in questions:
        if category != current_category:
            current_category = category
            lines.append(f"### {category}")
            lines.append("")
        index += 1
        lines.append(f"{index}. {question}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
