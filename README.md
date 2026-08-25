# Python 实用工具集

本仓库包含两个命令行工具：

1. [Todo List](#todo-list) —— 命令行待办事项
2. [AI GitHub 仓库分析助手](#ai-github-仓库分析助手) —— 输入 GitHub 地址，自动分析项目并生成报告与面试题

两个工具都仅使用 Python 标准库，无需安装任何第三方依赖。

---

## Todo List

一个简单的 Python 命令行待办事项程序。任务数据保存在本地 `tasks.json`
文件中，关闭程序后任务不会丢失。

### 功能

- 添加任务
- 删除任务
- 查看任务

### 环境要求

- Python 3.6+

### 使用方法

```bash
# 添加任务
python3 todo.py add "买牛奶"
# => 已添加任务 #1: 买牛奶

# 查看任务
python3 todo.py list
# => 1. [ ] 买牛奶

# 删除任务
python3 todo.py delete 1
# => 已删除任务 #1
```

### 命令说明

| 命令 | 说明 | 示例 |
| --- | --- | --- |
| `add <内容>` | 添加一条任务 | `python3 todo.py add "写周报"` |
| `list` | 查看所有任务 | `python3 todo.py list` |
| `delete <编号>` | 删除指定编号的任务 | `python3 todo.py delete 2` |

### 数据存储

任务保存在与脚本同目录下的 `tasks.json` 文件中，格式如下：

```json
[
  { "id": 1, "text": "买牛奶", "done": false }
]
```

---

## AI GitHub 仓库分析助手

输入一个 GitHub 仓库地址，自动完成以下流程：

```
输入 GitHub 地址
       ↓
自动分析项目结构
       ↓
生成技术栈报告
       ↓
生成项目总结
       ↓
生成面试题
```

### 功能

- **项目结构分析**：读取仓库文件树，识别顶级目录及用途、统计文件规模
- **技术栈报告**：识别主要语言、框架、数据库与工程化工具
- **项目总结**：生成结构化总结（简介、基本信息、技术定位、目录解读）
- **面试题生成**：根据检测到的语言与框架，自动生成项目题 + 语言题 + 框架题

### 环境要求

- Python 3.9+
- （可选）`git` 命令行工具，仅在使用 `--clone` 时需要

### 快速开始

```bash
# 分析一个 GitHub 仓库（需要可访问 GitHub API）
python3 analyzer.py https://github.com/psf/requests

# 使用简写地址
python3 analyzer.py psf/requests

# 将报告写入文件
python3 analyzer.py psf/requests --output report.md

# 分析本地目录
python3 analyzer.py --local ./my-project
```

### 数据获取方式

分析助手支持三种数据来源：

| 方式 | 说明 |
| --- | --- |
| GitHub API（默认） | 读取仓库元数据、语言统计、文件树和关键文件内容，速度快、无需下载完整代码 |
| `--clone` | 通过 `git clone --depth 1` 浅克隆后本地分析，适用于 API 限流时 |
| `--local <路径>` | 直接分析一个本地目录，无需联网 |

### 认证

GitHub API 对未认证请求有严格限流（每小时 60 次）。建议设置 token：

```bash
export GITHUB_TOKEN="your_token_here"
python3 analyzer.py owner/repo
```

也可通过 `--token` 参数传入，或已登录 `gh` CLI 时自动复用其凭证。

### 输出示例

```text
# GitHub 仓库分析报告：psf/requests

## 技术栈报告
### 语言分布
| 语言 | 占比 |
| --- | --- |
| Python | 100.0% |
### 框架与库
pytest
...
```

完整报告包含：技术栈报告、项目总结、面试题三个部分。

### 命令行参数

| 参数 | 说明 |
| --- | --- |
| `repo` | GitHub 仓库地址（`https://github.com/owner/repo` 或 `owner/repo`） |
| `--local PATH` | 分析本地目录 |
| `--clone` | 通过 git clone 获取仓库 |
| `--output/-o FILE` | 将报告写入指定文件 |
| `--token` | GitHub API token |

### 项目结构

```text
analyzer.py               # CLI 入口
gh_analyzer/
├── __init__.py
├── github.py             # 数据获取（GitHub API / clone / 本地目录）
├── techstack.py          # 技术栈检测（语言、框架、数据库、工具）
├── summary.py            # 项目总结生成
├── interview.py          # 面试题知识库与生成
└── report.py             # Markdown 报告渲染
```
