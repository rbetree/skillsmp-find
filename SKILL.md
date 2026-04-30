---
name: skillsmp-find
description: "Search SkillsMP for AI agent skills across AgentSkills, Codex, Claude Code, Hermes, OpenClaw, and shared agent ecosystems. Use when the user asks to find, discover, compare, or search for reusable AI Agent skills; when Chinese requests need English skill keywords; when an agent should analyze a project before choosing search terms; or when API quota/config status is needed. Do not use as an installer or package manager."
license: MIT
allowed-tools: bash, read
metadata:
  author: rbetree
  version: "1.1.0"
  created: "2024-01-01"
  last_reviewed: "2026-05-01"
  review_interval_days: 90
  positioning: "multi-ecosystem AI Agent Skill search tool"
  primary_audience: "AI agents"
  source_references:
    - "https://skillsmp.com/docs/api"
    - "https://agentskills.io/specification"
  platforms:
    agent_skills:
      tier: primary
      role: "open-standard contract"
    codex:
      tier: validated
      activation: "/skillsmp-find"
      argument_hint: "[query] [-b EN_KEYWORD] [--sort stars] [--ai] [--save FILE]"
      user_invocable: true
      install_path: "~/.codex/skills/skillsmp-find"
    claude_code:
      tier: validated
      install_path: "~/.claude/skills/skillsmp-find"
    hermes:
      tier: documented
      install_path: "~/.hermes/skills/research/skillsmp-find"
    openclaw:
      tier: documented
      install_path: "~/.openclaw/workspace/skills/skillsmp-find"
    universal_agents:
      tier: documented
      install_path: "~/.agents/skills/skillsmp-find"
---

# SkillsMP Search

Search SkillsMP for AI Agent skills. Treat this skill as a runtime contract for agents; use `README.md` and `INSTALL.md` for human-facing installation details.

## Core Workflow

1. Detect the user's language and respond in that language.
2. If the user asks for skills for a local project or repository, run `analyze /path/to/project --json` first, then choose search keywords from the project context.
3. If the user asks in Chinese, generate a short English keyword and search with both Chinese and English using `-b`.
4. Choose the search mode:
   - If an API key is configured, prefer AI-assisted search with `--ai` for normal discovery tasks. Use `search "query" --ai` as the agent default because it preserves keyword recall while adding semantic results.
   - If no API key is configured, use keyword search and bilingual keyword search.
   - Use keyword-only search when the user asks for an exact name, slug, category, occupation, or deterministic pagination.
   - Use `--limit 5` for normal recommendations. Use 10-20 only when the user asks for a broader comparison or pagination.
   - Use the default `recent` sort for freshness-sensitive discovery. Use `--sort stars --limit 5` when the user asks for popular, mature, or high-signal options.
   - Apply category or occupation filters only when the user provides a slug or a clearly bounded taxonomy target; do not invent obscure occupation slugs.
   - Use `ai-search` only for pure semantic probes, troubleshooting semantic relevance, or when hybrid `search --ai` is not useful. It has no keyword pagination or category/occupation filters.
   - Use `--json` or `--save FILE` when another tool, script, or follow-up analysis needs structured output.
   - Use `-v` when the user asks how to install a result, but do not install third-party skills yourself.
5. Run the CLI from this skill folder:

```bash
python scripts/search.py search "query"
python scripts/search.py search "query" --ai
python scripts/search.py search "前端鉴权" -b "frontend authorization" --ai
python scripts/search.py search "query" --sort stars --limit 5
python scripts/search.py search "query" --json
python scripts/search.py search "query" --save results.json
python scripts/search.py analyze /path/to/project --json
python scripts/search.py info
python scripts/search.py config
```

6. Report the top 3-5 matches, including name, purpose, source URL, source tag when available, stars, and fit/risk notes. Treat stars as a popularity signal, not proof of quality.
7. If the API reports quota, missing-key, or network errors, explain the failure and retry with the lower-cost keyword path only when that can still answer the user.
8. Remind the user to review the source repository before installing a third-party skill.

## Keyword Generation

SkillsMP primarily indexes English skill names and descriptions. For Chinese requests, search with both the original Chinese query and an English keyword using `-b`.

Use 1-2 words. Prefer capability terms a skill author would use:

| User intent | English keyword |
|-------------|-----------------|
| 写 README | `readme writer` |
| 代码审查 | `code review` |
| 处理 CSV | `csv` |
| 生成单元测试 | `testing` |
| React 相关 | `react` |
| 调试助手 | `debugging` |
| 前端鉴权 | `frontend authorization` |

Avoid long need descriptions, implementation details, and Chinese-only keyword searches when the user needs broad coverage.

## Project-Aware Search

When the user asks for skills for the current project, first inspect the project with:

```bash
python scripts/search.py analyze /path/to/project --json
```

Use the analysis to choose search keywords yourself. The CLI intentionally does not auto-generate recommendations.

Use project analysis before search for requests like "find useful skills for this repo", "what skills should I install here", or "scan this project and suggest skills". Do not run analysis for simple global queries like "find a code review skill".

## Configuration

API keys are optional for keyword search and required for AI semantic search.
When `python scripts/search.py config` shows an API key is available, use `search "query" --ai` as the default discovery command unless the user needs exact keyword-only behavior.

Priority order:

1. `SKILLSMP_API_KEY`
2. Repository `.env`
3. `~/.skillsmp/config.yaml`
4. `~/.hermes/config.yaml`

Anonymous access is rate limited. Run `python scripts/search.py info` to check current quota.

## Boundaries

- This skill searches and explains skills; it does not install, pin, audit, or execute third-party skills.
- Keep `SKILL.md` concise. Human install docs belong in `README.md` and `INSTALL.md`.
- Future capabilities such as install flows, saved collections, or recommendation engines belong in `REVIEW.md` as roadmap items until explicitly implemented.
