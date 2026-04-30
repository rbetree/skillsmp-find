<div align="center">

# SkillsMP Find

> Search 900,000+ AI Agent skills from your terminal — zero dependencies, git clone and go.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-None-brightgreen.svg)](#dependencies)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](#install)
[![Codex](https://img.shields.io/badge/Codex-Skill-orange)](#install)
[![Hermes](https://img.shields.io/badge/Hermes-Agent-green)](#install)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-teal)](#install)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-blue)](https://agentskills.io)

<br>

Stop browsing 900,000+ skills one by one on the web.<br>
Stop copy-pasting install commands manually.<br>
Stop switching between Chinese and English search results.<br>

**One CLI to search them all — clone and go.**

<br>

Keyword search · Bilingual search (Chinese + English) · AI semantic search<br>
Star sorting · Category filter · Save to JSON · Install commands

[Install](#install) · [Usage](#usage) · [Commands](#commands) · [Configuration](#configuration) · [Demo](#demo)

[**中文**](docs/lang/README_ZH.md)

</div>

---

## Features

skillsmp-find is a multi-ecosystem AI Agent Skill search tool. AgentSkills is the
primary open-standard contract; Codex and Claude Code are validated targets;
Hermes, OpenClaw, and the shared `~/.agents/skills` path are documented
compatibility targets.

| Ecosystem | Support level | Notes |
|-----------|---------------|-------|
| AgentSkills | Primary | Open-standard `SKILL.md` contract |
| Codex | Validated | Includes `agents/openai.yaml` UI metadata |
| Claude Code | Validated | Global and project skill paths documented |
| Hermes / OpenClaw / universal agents | Documented | Compatibility paths documented; not release-blocking |

| Feature | Description |
|---------|-------------|
| Keyword Search | Find skills by name, description, or functionality |
| Bilingual Search | Chinese + English parallel search and merge results |
| AI Concurrent Search | Keyword + AI semantic search simultaneously |
| Project Analysis | Dump project info for AI agent to decide search keywords |
| Star Sorting | Discover popular and well-maintained skills |
| Category Filtering | Browse by category (devops, research, creative, etc.) |
| Occupation Filtering | Find skills relevant to your role |
| Colored Output | Source tags: `[kw]` `[cn]` `[en]` `[ai]` |
| Save Results | Export search results to JSON file |
| Verbose Mode | Get install commands with `-v` flag |
| Zero Dependencies | Python 3.8+ standard library only |

---

## Install

### For AI Agents

See [INSTALL.md](INSTALL.md) for platform detection and installation steps.

Quick install (run the command matching your platform):

```bash
# Claude Code
git clone https://github.com/rbetree/skillsmp-find.git ~/.claude/skills/skillsmp-find

# Codex CLI
git clone https://github.com/rbetree/skillsmp-find.git ~/.codex/skills/skillsmp-find

# Hermes Agent
git clone https://github.com/rbetree/skillsmp-find.git ~/.hermes/skills/research/skillsmp-find

# Universal path (Gemini CLI, Kiro, Antigravity, others)
git clone https://github.com/rbetree/skillsmp-find.git ~/.agents/skills/skillsmp-find
```

After installation, tell the user: "Installed! Type `/skillsmp-find` or describe what you want to search."

### For Humans

#### One-Click Install (Interactive Menu)

```bash
curl -sSL https://raw.githubusercontent.com/rbetree/skillsmp-find/main/install.sh | bash
```

Choose your platform: Claude Code, Codex, Hermes, OpenClaw, or all.

Or specify directly:

```bash
./install.sh --claude-code
./install.sh --codex --hermes
./install.sh --all
```

#### Manual Install

```bash
# Claude Code
git clone https://github.com/rbetree/skillsmp-find.git ~/.claude/skills/skillsmp-find

# Codex CLI
git clone https://github.com/rbetree/skillsmp-find.git ~/.codex/skills/skillsmp-find

# Hermes Agent
git clone https://github.com/rbetree/skillsmp-find.git ~/.hermes/skills/research/skillsmp-find
```

See [INSTALL.md](INSTALL.md) for all platforms and detailed configuration.

### After Installation

Use `/skillsmp-find` or describe what you want to search:

```
帮我找一个代码审查的 skill
search skills for web scraping
有没有 Docker 相关的 skill？
```

---

## Usage

### Basic Search

```bash
# Simple keyword search
python scripts/search.py search "web scraping"

# Paginated results
python scripts/search.py search "teaching" --page 2 --limit 10

# JSON output for piping
python scripts/search.py search "automation" --json | jq '.data.skills[].name'
```

### Filtered Search

```bash
# By category
python scripts/search.py search "API" --category devops

# By occupation
python scripts/search.py search "testing" --occupation software-developers-151252
```

### AI Search (requires API key)

```bash
export SKILLSMP_API_KEY=***

python scripts/search.py search "browser automation" --ai
python scripts/search.py ai-search "how to automate browser testing"
python scripts/search.py ai-search "web scraping with cloudflare bypass" -v
```

For AI agents, prefer `search "query" --ai` when an API key is configured because it preserves keyword recall while adding semantic results. Use keyword-only search for exact names, slugs, category/occupation filters, or deterministic pagination. Use `ai-search` only for pure semantic probes or semantic relevance troubleshooting.

### Analyze Project (for AI agents)

```bash
# Dump project info — AI agent reads this, decides keywords, then searches
python scripts/search.py analyze /path/to/project

# JSON output for programmatic consumption
python scripts/search.py analyze . --json
```

AI agent decision rules:

- For local repo recommendations, run `analyze /path/to/project --json` before searching.
- For Chinese requests, generate a short English keyword and use `-b`.
- With an API key, prefer `search "query" --ai` for discovery.
- Use `--limit 5` for normal recommendations; use 10-20 only for broader comparisons.
- Keep the default `recent` sort for freshness-sensitive discovery; use `--sort stars --limit 5` for popular or mature options.
- Apply `--category` or `--occupation` only when the user gives a slug or clearly bounded taxonomy target.
- For reusable downstream output, use `--json` or `--save FILE`.
- Report the top 3-5 matches with source links, stars, source tags when available, and fit/risk notes. Treat stars as popularity, not proof of quality.
- For install guidance, use `-v`, summarize links, and ask the user to review source before installing.

---

## Commands

| Command | Description |
|---------|-------------|
| `search "query"` | Keyword search |
| `search "前端鉴权" -b "frontend authorization"` | Bilingual search (Chinese + English) |
| `search "query" --ai` | Keyword + AI concurrent search |
| `search "query" --save results.json` | Save results to JSON file |
| `search "query" --sort stars` | Sort by stars |
| `search "query" --limit 10 --page 2` | Paginated results |
| `search "query" -v` | Verbose with install commands |
| `search "query" --json` | JSON output |
| `search "query" --category devops` | Filter by category |
| `search "query" --occupation software-developers` | Filter by occupation |
| `ai-search "query"` | AI semantic search (needs API key) |
| `analyze .` | Dump project info (deps, languages, traits) |
| `analyze . --json` | Project info as JSON (for AI consumption) |
| `info` | Check API status & rate limits |
| `config` | Show current configuration |

---

## Configuration

### Option 1: Environment Variable (Recommended)

```bash
export SKILLSMP_API_KEY=***
```

### Option 2: Repository `.env` File

Copy the example file in the repository root:

```bash
cp .env.example .env
```

Then edit `.env` and fill in your API key. The CLI will auto-load this file on startup without extra dependencies.

### Option 3: Config File

```bash
mkdir -p ~/.skillsmp
cat > ~/.skillsmp/config.yaml << EOF
api_key: ***
default_limit: 20
default_sort: recent
EOF
```

### Option 4: Hermes Config

```bash
hermes config set skills.config.skillsmp.api_key ***
```

**Priority order:**
1. Shell environment variable `SKILLSMP_API_KEY` (highest)
2. Repository `.env`
3. Config file `~/.skillsmp/config.yaml`
4. Hermes config `~/.hermes/config.yaml`

### Get API Key

1. Visit https://skillsmp.com/docs/api
2. Sign up for an account
3. Generate an API key

**Rate Limits:**
- Anonymous: 50 requests/day, 10 requests/min
- With API key: 500 requests/day, 30 requests/min

---

## Demo

### Keyword Search

```
$ python scripts/search.py search "auth" --sort stars --limit 3

============================================================
Found 1000 skills (page 1/1)
============================================================

[1] ★ 40012 | auth
    Implement JWT/cookie authentication and authorization in tRPC using createContext...

[2] ★ 33850 | auth-implementation-patterns
    Master authentication and authorization patterns including JWT, OAuth2, session...

[3] ★ 3957 | authentication
    Sessions, sign-in/sign-up flows, OAuth, magic links, or organization context...

Rate Limits:
   Daily: 498/500 remaining
   Minute: 29/30 remaining
```

### Bilingual Search

```
$ python scripts/search.py search "前端鉴权" -b "frontend authorization" --limit 5

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

## Dependencies

**None.** This tool uses Python 3.8+ standard library only.

```bash
# Just clone and run — no pip install needed
git clone https://github.com/rbetree/skillsmp-find.git
cd skillsmp-find
python scripts/search.py search "web scraping"
```

<details>
<summary>Optional dependency</summary>

- `pyyaml` — enables `~/.skillsmp/config.yaml` config file. Without it, use environment variable `SKILLSMP_API_KEY` instead.

</details>

---

## Project Structure

```
skillsmp-find/
├── agents/
│   └── openai.yaml      # Codex UI metadata
├── scripts/
│   ├── search.py         # Main CLI script (zero dependencies)
│   └── validate_skill.py # Multi-ecosystem skill contract validator
├── docs/
│   └── lang/
│       └── README_ZH.md  # Chinese documentation
├── AGENTS.md             # Repository-level AI agent context
├── SKILL.md              # Agent skill definition
├── INSTALL.md            # Detailed installation guide
├── install.sh            # One-click installer
├── README.md             # This file
├── LICENSE               # MIT License
└── .gitignore
```

---

## Notes

- **Rate limits**: Anonymous access is limited to 50/day. Use `info` to check remaining quota.
- **AI search requires API key**: Returns `MISSING_API_KEY` error without it.
- **Skills are from GitHub**: Always review before installing — check the source repo.
- **Pagination**: Large result sets require multiple pages. Check `hasNext` in response.
- **Network resilience**: The tool automatically retries failed network requests (3 attempts with exponential backoff).
- **Config security**: Config files with API keys should have secure permissions (600). The tool warns if config files are world-readable.

---

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

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

[SkillsMP](https://skillsmp.com) · [API Docs](https://skillsmp.com/docs/api)

</div>
