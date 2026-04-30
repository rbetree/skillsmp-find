# skillsmp-find Agent Context

skillsmp-find is a multi-ecosystem AI Agent Skill search tool for SkillsMP. Optimize first for AI agents; the CLI is the execution surface.

## Positioning

- AgentSkills is the primary open-standard contract.
- Codex and Claude Code are validated ecosystems.
- Hermes, OpenClaw, and `~/.agents/skills` are documented compatibility paths.
- `SKILL.md` is the runtime contract. Keep human-facing install and usage detail in `README.md` and `INSTALL.md`.
- Keep the project zero-dependency by default. Optional dependencies must preserve standard-library operation.

## Commands

| Task | Command |
|------|---------|
| Search | `python3 scripts/search.py search "web scraping"` |
| Bilingual search | `python3 scripts/search.py search "前端鉴权" -b "frontend authorization"` |
| Analyze project | `python3 scripts/search.py analyze . --json` |
| Show config | `python3 scripts/search.py config` |
| Run tests | `python3 -m unittest discover -s tests -p 'test_*.py'` |
| Validate skill | `python3 scripts/validate_skill.py .` |

## Repository Map

| Path | Purpose |
|------|---------|
| `SKILL.md` | Agent runtime contract and trigger metadata |
| `scripts/search.py` | Zero-dependency SkillsMP CLI |
| `scripts/validate_skill.py` | Project AgentSkills multi-ecosystem validator |
| `agents/openai.yaml` | Codex UI metadata only |
| `README.md`, `docs/lang/README_ZH.md` | Human-facing docs |
| `INSTALL.md`, `install.sh` | Multi-ecosystem installation docs and helper |
| `REVIEW.md` | Review notes and future roadmap |

## Quality Gate

Before finishing changes that affect behavior or docs, run:

1. `python3 scripts/validate_skill.py .`
2. `python3 -m unittest discover -s tests -p 'test_*.py'`
3. At least one relevant CLI smoke command, usually `config`, `analyze . --json`, and a focused search.

## Boundaries

- Do not add install, favorite, recommendation, or third-party execution features unless explicitly requested.
- Do not make `skill-creator quick_validate.py` the only source of truth; it is a reference for Codex-specific checks.
- Keep future feature ideas in `REVIEW.md` until a separate implementation plan exists.
