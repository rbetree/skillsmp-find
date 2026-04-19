<div align="center">

# SkillsMP Find

> 从终端搜索 90 万+ AI Agent 技能 — 零依赖，克隆即用。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-None-brightgreen.svg)](#依赖)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](#安装)
[![Codex](https://img.shields.io/badge/Codex-Skill-orange)](#安装)
[![Hermes](https://img.shields.io/badge/Hermes-Agent-green)](#安装)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-teal)](#安装)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-blue)](https://agentskills.io)

<br>

别再在网页上一个一个翻 90 万+ 技能了。<br>
别再手动复制粘贴安装命令了。<br>
别再在中英文搜索结果之间来回切换了。<br>

**一个 CLI 搜索全部 — 克隆即用。**

<br>

关键词搜索 · 中文自动翻译 · AI 语义搜索<br>
按星排序 · 分类过滤 · 保存 JSON · 获取安装命令

[安装](#安装) · [使用](#使用) · [命令速查](#命令速查) · [配置](#配置) · [演示](#演示)

[**English**](../../README.md)

</div>

---

## 功能特性

| 功能 | 说明 |
|------|------|
| 关键词搜索 | 按名称、描述或功能查找技能 |
| 双语搜索 | 中文 + 英文，自动翻译并合并结果 |
| AI 并发搜索 | 关键词 + AI 语义搜索同时执行 |
| 按星排序 | 发现热门且维护良好的技能 |
| 分类过滤 | 按类别浏览（devops、research、creative 等） |
| 职业过滤 | 查找与你角色相关的技能 |
| 彩色输出 | 来源标签：`[kw]` `[cn]` `[en]` `[ai]` |
| 保存结果 | 将搜索结果导出为 JSON 文件 |
| 详细模式 | 使用 `-v` 参数获取安装命令 |
| 零依赖 | 仅需 Python 3.8+ 标准库 |

---

## 安装

### 最简单的方式

复制下面这段发给你的 AI Agent（Claude Code、Codex、Cursor 等）：

```
帮我把 https://github.com/rbetree/skillsmp-find.git 克隆并安装到你对应的位置。
```

就这样，Agent 会自己搞定。

### 一键安装

```bash
curl -sSL https://raw.githubusercontent.com/rbetree/skillsmp-find/main/install.sh | bash
```

交互式菜单选择平台：Claude Code、Codex、Hermes、OpenClaw、Cursor，或全部安装。

或直接指定：

```bash
./install.sh --claude-code
./install.sh --codex --hermes
./install.sh --all
```

### 手动安装

```bash
# Claude Code
git clone https://github.com/rbetree/skillsmp-find.git ~/.claude/skills/skillsmp-find

# Codex CLI
git clone https://github.com/rbetree/skillsmp-find.git ~/.codex/skills/skillsmp-find

# Hermes Agent
git clone https://github.com/rbetree/skillsmp-find.git ~/.hermes/skills/research/skillsmp-find
```

详见 [INSTALL.md](../../INSTALL.md) 了解所有平台和详细配置。

---

## 使用

### 基础搜索

```bash
# 简单关键词搜索
python scripts/search.py search "web scraping"

# 分页结果
python scripts/search.py search "teaching" --page 2 --limit 10

# JSON 输出，便于管道处理
python scripts/search.py search "automation" --json | jq '.data.skills[].name'
```

### 过滤搜索

```bash
# 按分类
python scripts/search.py search "API" --category devops

# 按职业
python scripts/search.py search "testing" --occupation software-developers-151252
```

### AI 搜索（需要 API Key）

```bash
export SKILLSMP_API_KEY=***

python scripts/search.py ai-search "how to automate browser testing"
python scripts/search.py ai-search "web scraping with cloudflare bypass" -v
```

### 查看状态

```bash
python scripts/search.py info      # API 状态和速率限制
python scripts/search.py config    # 当前配置
```

---

## 命令速查

| 命令 | 说明 |
|------|------|
| `search "query"` | 关键词搜索 |
| `search "前端鉴权" -b` | 双语搜索（中文 + 英文） |
| `search "query" --ai` | 关键词 + AI 并发搜索 |
| `search "query" --save results.json` | 保存结果为 JSON 文件 |
| `search "query" --sort stars` | 按星排序 |
| `search "query" --limit 10 --page 2` | 分页结果 |
| `search "query" -v` | 详细模式，包含安装命令 |
| `search "query" --json` | JSON 输出 |
| `search "query" --category devops` | 按分类过滤 |
| `search "query" --occupation software-developers` | 按职业过滤 |
| `ai-search "query"` | AI 语义搜索（需 API Key） |
| `info` | 查看 API 状态和速率限制 |
| `config` | 查看当前配置 |

---

## 配置

### 方式一：环境变量（推荐）

```bash
export SKILLSMP_API_KEY=***
```

### 方式二：配置文件

```bash
mkdir -p ~/.skillsmp
cat > ~/.skillsmp/config.yaml << EOF
api_key: ***
default_limit: 20
default_sort: recent
EOF
```

### 方式三：Hermes 配置

```bash
hermes config set skills.config.skillsmp.api_key ***
```

**优先级顺序：**
1. 环境变量 `SKILLSMP_API_KEY`（最高）
2. 配置文件 `~/.skillsmp/config.yaml`
3. Hermes 配置 `~/.hermes/config.yaml`

### 获取 API Key

1. 访问 https://skillsmp.com/docs/api
2. 注册账号
3. 生成 API Key

**速率限制：**
- 匿名访问：50 次/天，10 次/分钟
- 使用 API Key：500 次/天，30 次/分钟

---

## 演示

### 关键词搜索

```
$ python scripts/search.py search "auth" --sort stars --limit 3

============================================================
找到 1000 个技能 (第 1 页/共 1 页)
============================================================

[1] ★ 40012 | auth
    在 tRPC 中实现 JWT/Cookie 认证和授权...

[2] ★ 33850 | auth-implementation-patterns
    掌握认证和授权模式，包括 JWT、OAuth2、会话管理...

[3] ★ 3957 | authentication
    会话、登录注册流程、OAuth、Magic Links...

速率限制：
   每日：498/500 剩余
   每分钟：29/30 剩余
```

### 双语搜索

```
$ python scripts/search.py search "前端鉴权" -b --limit 5

============================================================
搜索 前端鉴权 + authorization frontend 共 10 条
   [cn]=中文 | [en]=英文
============================================================

[1] ★ 832 | iam [cn]
    基于蓝鲸 IAM 的前端鉴权方案，包含 v-authority 指令实现...

[2] ★ 51 | authorization [en]
    Set up permission-based authorization in Spiderly...
```

---

## 依赖

**零依赖。** 本工具仅使用 Python 3.8+ 标准库。

```bash
# 克隆即用 — 无需 pip install
git clone https://github.com/rbetree/skillsmp-find.git
cd skillsmp-find
python scripts/search.py search "web scraping"
```

<details>
<summary>可选依赖</summary>

- `pyyaml` — 启用 `~/.skillsmp/config.yaml` 配置文件。不安装则使用环境变量 `SKILLSMP_API_KEY`。

</details>

---

## 项目结构

```
skillsmp-find/
├── scripts/
│   └── search.py         # 主 CLI 脚本（零依赖）
├── docs/
│   └── lang/
│       └── README_ZH.md  # 中文文档
├── SKILL.md              # Agent 技能定义
├── INSTALL.md            # 详细安装指南
├── install.sh            # 一键安装脚本
├── README.md             # 英文文档
├── LICENSE               # MIT 许可证
└── .gitignore
```

---

## 注意事项

- **速率限制**：匿名访问限制为 50 次/天。使用 `info` 命令检查剩余配额。
- **AI 搜索需要 API Key**：没有 API Key 会返回 `MISSING_API_KEY` 错误。
- **技能来自 GitHub**：安装前请务必检查来源仓库。
- **分页**：大量结果需要翻页查看，检查响应中的 `hasNext` 字段。

---

## 贡献

欢迎贡献。

1. Fork 本仓库
2. 创建功能分支（`git checkout -b feature/amazing-feature`）
3. 提交更改（`git commit -m 'feat: add amazing feature'`）
4. 推送到分支（`git push origin feature/amazing-feature`）
5. 发起 Pull Request

---

## Star History

<a href="https://www.star-history.com/#rbetree/skillsmp-find&type=date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=rbetree/skillsmp-find&type=date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=rbetree/skillsmp-find&type=date" />
   <img alt="Star History Chart" src="https://api.star-history.com/image?repos=rbetree/skillsmp-find&type=date" />
 </picture>
</a>

---

<div align="center">

MIT License | [rbetree](https://github.com/rbetree)

[SkillsMP](https://skillsmp.com) · [API 文档](https://skillsmp.com/docs/api)

</div>
