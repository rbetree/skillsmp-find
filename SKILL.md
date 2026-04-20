---
name: skillsmp-find
description: "Search 900K+ AI agent skills from SkillsMP | 从 SkillsMP 搜索 90 万+ AI Agent 技能"
argument-hint: "[query] [-b EN_KEYWORD] [--sort stars] [--ai] [--save FILE]"
version: "1.1.0"
license: MIT
user-invocable: true
allowed-tools: bash, read
activation: /skillsmp-find
metadata:
  author: rbetree
  version: "1.1.0"
  created: 2024-01-01
  last_reviewed: 2026-04-20
  review_interval_days: 90
provenance:
  maintainer: rbetree
  source_references:
    - https://skillsmp.com/docs/api
---

> **Language / 语言**: This skill supports both English and Chinese. Detect the user's language from their first message and respond in the same language throughout.
>
> 本 Skill 支持中英文。根据用户第一条消息的语言，全程使用同一语言回复。

# SkillsMP Search

Search and discover AI agent skills from [SkillsMP](https://skillsmp.com) — a marketplace with **900,000+ skills** compatible with Claude Code, Codex CLI, ChatGPT, and other AI agents.

## When to Use

- Finding skills for specific tasks (web scraping, code review, data analysis)
- Browsing skills by category or occupation
- AI-powered semantic search for complex requirements
- Discovering new tools and workflows
- Checking API rate limit status

## Installation

Clone this repo to your platform's skill directory:

```bash
# Claude Code
git clone https://github.com/rbetree/skillsmp-find.git ~/.claude/skills/skillsmp-find

# Codex CLI
git clone https://github.com/rbetree/skillsmp-find.git ~/.codex/skills/skillsmp-find

# Hermes Agent
git clone https://github.com/rbetree/skillsmp-find.git ~/.hermes/skills/research/skillsmp-find

# Universal (Gemini CLI, Kiro, Antigravity, others)
git clone https://github.com/rbetree/skillsmp-find.git ~/.agents/skills/skillsmp-find
```

See [INSTALL.md](INSTALL.md) for platform detection and detailed instructions.

## Trigger Phrases

- `/skillsmp-find`
- "search skills for ..."
- "find a skill that does ..."
- "帮我找一个 ... 的 skill"
- "搜索 ... 技能"
- "有什么好用的 ... skill"

## Quick Reference

| Command | Description |
|---------|-------------|
| `python scripts/search.py search "query"` | Keyword search |
| `python scripts/search.py search "前端鉴权" -b "frontend authorization"` | Bilingual: Chinese + English parallel search |
| `python scripts/search.py search "query" --ai` | Keyword + AI concurrent search |
| `python scripts/search.py search "query" --sort stars` | Sort by stars |
| `python scripts/search.py search "query" --limit 10 --page 2` | Paginated results |
| `python scripts/search.py search "query" -v` | Verbose with install commands |
| `python scripts/search.py search "query" --json` | JSON output |
| `python scripts/search.py search "query" --category devops` | Filter by category |
| `python scripts/search.py search "query" --occupation software-developers` | Filter by occupation |
| `python scripts/search.py ai-search "query"` | AI semantic search (needs API key) |
| `python scripts/search.py analyze .` | Dump project info (deps, languages, traits) |
| `python scripts/search.py analyze . --json` | Project info as JSON (for AI consumption) |
| `python scripts/search.py info` | Check API status & rate limits |
| `python scripts/search.py config` | Show current configuration |
| `python scripts/search.py search "query" --save results.json` | Save results to JSON file |

### AI Workflow: Analyze + Search

The `analyze` command dumps raw project info — it does NOT auto-generate keywords or search.
The AI agent (you) reads the analysis, understands the project, decides keywords, then searches.

```bash
# Step 1: AI runs analyze to understand the project
python scripts/search.py analyze /path/to/project

# Step 2: AI reads the output, decides keywords based on project context
# Step 3: AI runs search with its own keywords
python scripts/search.py search "docker deployment" --sort stars --limit 5
python scripts/search.py search "static site generator" --sort stars --limit 5
```

This separation lets AI use its understanding of the project to generate better keywords
than any hardcoded rule system.

## Configuration

### Option 1: Environment Variable (Recommended)

```bash
export SKILLSMP_API_KEY=***
```

### Option 2: Config File

```bash
mkdir -p ~/.skillsmp
cat > ~/.skillsmp/config.yaml << EOF
api_key: ***
default_limit: 20
default_sort: recent
EOF
```

### Option 3: Hermes Config (if using hermes agent)

```bash
hermes config set skills.config.skillsmp.api_key ***
```

**Priority order:**
1. Environment variable `SKILLSMP_API_KEY` (highest)
2. Config file `~/.skillsmp/config.yaml`
3. Hermes config `~/.hermes/config.yaml`

### Get API Key

1. Visit https://skillsmp.com/docs/api
2. Sign up for an account
3. Generate an API key

**Rate Limits:**
- Anonymous: 50 requests/day, 10 requests/min
- With API key: 500 requests/day, 30 requests/min

## Installation

See [INSTALL.md](INSTALL.md) for detailed installation instructions across all platforms.

### Quick Install

```bash
# Clone and run directly
git clone https://github.com/rbetree/skillsmp-find.git
cd skillsmp-find
python scripts/search.py search "web scraping"

# Or use the one-click installer
curl -sSL https://raw.githubusercontent.com/rbetree/skillsmp-find/main/install.sh | bash
```

## Keyword Generation (关键步骤)

SkillsMP primarily indexes English content. When the user speaks Chinese, **you** (the agent) are responsible for generating the English keyword. The CLI only executes searches.

### Core Principle

> **Think like a skill author, not like a user searching.**
> Skills are named by capability, not by need.

### Step 1: Extract Intent

From the user's description, identify:
- **Core action**: What should the skill do? (write / review / generate / analyze / test / format / search / debug / deploy / monitor...)
- **Target object**: What does it act on? (readme / code / csv / api / image / pr / commit / docker / database...)
- **Domain / tech stack** (if mentioned): react / python / sql / docker / markdown...

### Step 2: Generate Keywords

Use 1–2 words. Prefer:

| Strategy | Example |
|----------|---------|
| Action noun (most common skill naming) | `reviewer`, `writer`, `generator`, `analyzer` |
| Domain word (single) | `csv`, `testing`, `readme`, `documentation` |
| Action + domain (when precise) | `code review`, `readme writer` |

**Do NOT use**: full need descriptions (`help me write project documentation`), implementation details (`using langchain to process csv`), or Chinese words (SkillsMP won't match them).

### Step 3: Choose the Best Keyword

- Prefer the broadest term (`testing` > `pytest unit test`)
- When multiple English words exist for the same concept, pick the one a skill author would most likely use
- When unsure, pick the shortest

### Examples

| User says (用户说的) | Thinking process | Chinese query | English keyword (`-b`) |
|---------------------|-----------------|---------------|----------------------|
| "帮我找个写 README 的" | action=write, object=readme → author would call it readme writer | README | `readme writer` |
| "有没有代码审查的？" | action=review, object=code → common name | 代码审查 | `code review` |
| "我需要处理 CSV 文件" | object=csv, action=process → domain word is more precise | CSV | `csv` |
| "找个能生成单元测试的" | action=generate, object=test → domain word | 单元测试 | `testing` |
| "有 React 相关的吗" | tech=react → use directly | React | `react` |
| "想找个调试助手" | action=debug → action noun | 调试 | `debugging` |
| "前端鉴权怎么做" | object=frontend+auth → domain terms | 前端鉴权 | `frontend authorization` |

### Bilingual Search Strategy

For best coverage, always search with **both** the original Chinese and the generated English keyword:

```bash
# You (the agent) generate the English keyword, then call:
python scripts/search.py search "前端鉴权" -b "frontend authorization"
```

The CLI runs both queries in parallel and merges results by skill ID. Results are tagged `[cn]`, `[en]`, or `[cn+en]` to show source.

## Usage Examples

### Basic Search

```bash
python scripts/search.py search "web scraping"
python scripts/search.py search "code review" --sort stars --limit 5
python scripts/search.py search "teaching" --page 2 --limit 10
python scripts/search.py search "docker" -v
python scripts/search.py search "automation" --json | jq '.data.skills[].name'
```

### Bilingual Search

```bash
# Agent generates English keyword from Chinese input, searches both in parallel
python scripts/search.py search "前端鉴权" -b "frontend authorization"
python scripts/search.py search "爬虫" -b "web scraping"
python scripts/search.py search "代码审查" -b "code review"
```

### Filtered Search

```bash
python scripts/search.py search "API" --category devops
python scripts/search.py search "testing" --occupation software-developers-151252
```

### AI Search (with API key)

```bash
export SKILLSMP_API_KEY=***
python scripts/search.py ai-search "how to automate browser testing"
python scripts/search.py ai-search "web scraping with cloudflare bypass" -v
```

### Check API Status

```bash
python scripts/search.py info
```

## API Reference

### Keyword Search

```
GET https://skillsmp.com/api/v1/skills/search
```

**Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| q | string | Yes | Search query |
| page | number | No | Page number (default: 1) |
| limit | number | No | Items per page (default: 20, max: 100) |
| sortBy | string | No | Sort: `stars` or `recent` (default: recent) |
| category | string | No | Filter by category slug |
| occupation | string | No | Filter by SOC occupation slug |

### AI Semantic Search

```
GET https://skillsmp.com/api/v1/skills/ai-search
```

**Requires API key.** Uses Cloudflare AI for natural language understanding.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| q | string | Yes | AI search query |

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| MISSING_API_KEY | 401 | API key not provided (required for AI search) |
| INVALID_API_KEY | 401 | Invalid API key |
| MISSING_QUERY | 400 | Missing required query parameter |
| DAILY_QUOTA_EXCEEDED | 429 | Daily API quota exceeded |
| INTERNAL_ERROR | 500 | Internal server error |

## Pitfalls

- **Rate limits**: Anonymous access is limited to 50/day. Use `info` to check remaining quota.
- **AI search requires API key**: Returns `MISSING_API_KEY` error without it.
- **Skills are from GitHub**: Always review before installing — check the source repo.
- **Pagination**: Large result sets require multiple pages. Check `hasNext` in response.
- **Network issues**: The tool automatically retries failed network requests (3 attempts with exponential backoff).
- **Config file security**: Config files containing API keys should have secure permissions (600). The tool warns if config files are world-readable.

## Dependencies

**None.** This tool uses Python 3.8+ standard library only.

Optional (for config file support):
- `pyyaml` — enables `~/.skillsmp/config.yaml` config file. Without it, use environment variable `SKILLSMP_API_KEY` instead.

MIT License - see LICENSE file for details.
