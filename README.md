# AI GitHub 仓库分析助手

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

## 功能

- **项目结构分析**：构建完整目录树，**为每个目录自动推断用途**并标注（来源：目录名精确匹配 → 关键词 → 目录内容特征），并为 README、Dockerfile、package.json 等**重要文件**标注说明；Web 界面中的目录树**每一层都可展开/收起**
- **技术栈报告**：识别主要语言、框架、数据库与工程化工具
- **项目总结**：生成结构化总结（简介、基本信息、技术定位、项目规模）
- **面试题生成**：根据检测到的语言与框架，自动生成项目题 + 语言题 + 框架题
- **交互式 Web 界面**：提供浏览器可视化界面，输入地址即可查看分析结果

## 环境要求

- Python 3.9+
- （可选）`git` 命令行工具，仅在使用 `--clone` 时需要

## 快速开始

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

## 交互式 Web 界面

启动本地 Web 服务后，在浏览器中即可使用可视化界面：

```bash
# 启动（默认 http://127.0.0.1:8000）
python3 webapp.py

# 指定端口
python3 webapp.py --port 9000

# 提供 token（避免 API 限流，也可用 GITHUB_TOKEN 环境变量）
python3 webapp.py --token your_token_here
```

浏览器打开 http://127.0.0.1:8000 后，输入 GitHub 地址即可看到：

- 仓库基本信息（Star、Fork、描述、主题标签）
- 语言分布条形图与框架/数据库/工具标签
- 项目结构树（每层可展开/收起，目录与重要文件均标注用途）
- 项目总结
- 分组面试题

Web 界面同样支持「git clone」模式，勾选页面上的 `git clone` 复选框即可在 API 限流时改用克隆方式分析。

## 数据获取方式

分析助手支持三种数据来源：

| 方式 | 说明 |
| --- | --- |
| GitHub API（默认） | 读取仓库元数据、语言统计、文件树和关键文件内容，速度快、无需下载完整代码 |
| `--clone` | 通过 `git clone --depth 1` 浅克隆后本地分析，适用于 API 限流时 |
| `--local <路径>` | 直接分析一个本地目录，无需联网 |

## 认证

GitHub API 对未认证请求有严格限流（每小时 60 次）。建议设置 token：

```bash
export GITHUB_TOKEN="your_token_here"
python3 analyzer.py owner/repo
```

也可通过 `--token` 参数传入，或已登录 `gh` CLI 时自动复用其凭证。

## 输出示例

```text
# GitHub 仓库分析报告：psf/requests

## 技术栈报告
### 语言分布
| 语言 | 占比 |
| --- | --- |
| Python | 100.0% |
### 框架与库
pytest

## 项目结构
├── .github/          # GitHub 工作流/CI
├── README.md         # 项目说明文档
├── docs/             # 文档
├── src/              # 源代码
│   └── main.py       # 程序入口
└── tests/            # 测试代码
...
```

完整报告包含：技术栈报告、项目结构、项目总结、面试题四个部分。

## 命令行参数

| 参数 | 说明 |
| --- | --- |
| `repo` | GitHub 仓库地址（`https://github.com/owner/repo` 或 `owner/repo`） |
| `--local PATH` | 分析本地目录 |
| `--clone` | 通过 git clone 获取仓库 |
| `--output/-o FILE` | 将报告写入指定文件 |
| `--token` | GitHub API token |

## 项目结构

```text
analyzer.py               # CLI 入口
webapp.py                 # Web 服务入口（HTTP 服务器 + 分析 API）
static/
└── index.html            # 交互式前端界面（HTML/CSS/JS）
gh_analyzer/
├── __init__.py
├── github.py             # 数据获取（GitHub API / clone / 本地目录）
├── techstack.py          # 技术栈检测（语言、框架、数据库、工具）
├── summary.py             # 项目总结生成
├── interview.py          # 面试题知识库与生成
└── report.py             # Markdown 报告渲染
```
