---
name: skillsmp-find
description: "Search 900K+ AI agent skills from SkillsMP | 从 SkillsMP 搜索 90 万+ AI Agent 技能"
argument-hint: "[query] [--sort stars] [--ai] [-b] [--save FILE]"
version: "1.0.0"
user-invocable: true
allowed-tools: Bash, Read
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
| `python scripts/search.py search "前端鉴权" -b` | Bilingual search (Chinese + English) |
| `python scripts/search.py search "query" --ai` | Keyword + AI concurrent search |
| `python scripts/search.py search "query" --sort stars` | Sort by stars |
| `python scripts/search.py search "query" --limit 10 --page 2` | Paginated results |
| `python scripts/search.py search "query" -v` | Verbose with install commands |
| `python scripts/search.py search "query" --json` | JSON output |
| `python scripts/search.py search "query" --category devops` | Filter by category |
| `python scripts/search.py search "query" --occupation software-developers` | Filter by occupation |
| `python scripts/search.py ai-search "query"` | AI semantic search (needs API key) |
| `python scripts/search.py info` | Check API status & rate limits |
| `python scripts/search.py config` | Show current configuration |
| `python scripts/search.py search "query" --save results.json` | Save results to JSON file |

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

## Usage Examples

### Basic Search

```bash
python scripts/search.py search "web scraping"
python scripts/search.py search "code review" --sort stars --limit 5
python scripts/search.py search "teaching" --page 2 --limit 10
python scripts/search.py search "docker" -v
python scripts/search.py search "automation" --json | jq '.data.skills[].name'
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

## Dependencies

**None.** This tool uses Python 3.8+ standard library only.

Optional (for config file support):
- `pyyaml` — enables `~/.skillsmp/config.yaml` config file. Without it, use environment variable `SKILLSMP_API_KEY` instead.

MIT License - see LICENSE file for details.
