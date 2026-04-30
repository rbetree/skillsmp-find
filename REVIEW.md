# SkillsMP-Find Review and Roadmap

> Review date: 2026-05-01
> Version: 1.1.0

## Confirmed Positioning

- skillsmp-find is a multi-ecosystem AI Agent Skill search tool.
- Primary audience: AI agents. Human CLI usage is secondary.
- Primary contract: AgentSkills open-standard `SKILL.md`.
- Validated targets: Codex and Claude Code.
- Documented compatibility: Hermes, OpenClaw, and the shared `~/.agents/skills` path.
- `SKILL.md` is a runtime contract, not the full human manual.

## Current Quality Gate

| Check | Command |
|-------|---------|
| Multi-ecosystem skill contract | `python3 scripts/validate_skill.py .` |
| Unit tests | `python3 -m unittest discover -s tests -p 'test_*.py'` |
| Config smoke | `python3 scripts/search.py config` |
| Project analysis smoke | `python3 scripts/search.py analyze . --json` |
| Search smoke | `python3 scripts/search.py search "code review" --limit 2 --json` |
| Bilingual smoke | `python3 scripts/search.py search "前端鉴权" -b "frontend authorization" --limit 3 --json` |

## Recently Completed

| Area | Result |
|------|--------|
| Skill metadata | Top-level `SKILL.md` fields aligned to the open-standard contract |
| Platform metadata | Platform-specific fields moved under `metadata.platforms` |
| Codex UI metadata | Added `agents/openai.yaml` |
| Agent context | Added `AGENTS.md` as repository-level AI guidance |
| Pagination semantics | Single keyword search preserves upstream API pagination; merged searches report local merged pagination |
| Installer | Fixed `--claude-code --project` argument order dependency and invalid target handling |
| Chinese docs | Fixed malformed feature table row |
| Compatibility docs | Added ecosystem support matrix to English and Chinese README |
| Validation tests | Covered the no-PyYAML fallback parser |

## Known Follow-Up Candidates

| Priority | Area | Candidate |
|----------|------|-----------|
| Medium | CLI | Add mock-based API tests for pagination and merged search semantics |
| Low | Code structure | Consider splitting project analysis helpers out of `scripts/search.py` only if future changes keep growing |

## Future Feature Research Pool

These are roadmap research topics only. Do not implement them without a separate plan.

### Intelligent Discovery

- Project analysis to keyword suggestion: assess whether agents need deterministic hints or should keep generating keywords themselves.
- Semantic search strategy: compare keyword-only, bilingual, `--ai`, and hybrid result quality.
- Ranking explanation: evaluate whether results should include fit reasons, source tags, freshness, and risk notes.
- Result quality evaluation: define small benchmark prompts for common Chinese and English discovery tasks.

### Install Loop

- One-click install from search results.
- Source repository review before install.
- Compatibility detection for Codex, Claude Code, Hermes, OpenClaw, and universal paths.
- Security boundaries for third-party skill execution.

### Integration Interfaces

- Stable JSON schema for embedding in other tools.
- MCP or API wrapper feasibility.
- Saved collections or exported skill shortlists.
