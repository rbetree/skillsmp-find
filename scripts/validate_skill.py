#!/usr/bin/env python3
"""Validate the skillsmp-find AgentSkills multi-ecosystem contract."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover - exercised when PyYAML is absent
    yaml = None


ALLOWED_FRONTMATTER_KEYS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}

REQUIRED_PLATFORM_KEYS = {
    "agent_skills",
    "codex",
    "claude_code",
    "hermes",
    "openclaw",
    "universal_agents",
}

FORBIDDEN_TOP_LEVEL_KEYS = {
    "activation",
    "argument-hint",
    "user-invocable",
    "provenance",
    "version",
}


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return {}
    if value in {"true", "false"}:
        return value == "true"
    if value.isdigit():
        return int(value)
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _parse_frontmatter_without_yaml(frontmatter_text: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    stack: list[tuple[int, Dict[str, Any]]] = [(-1, data)]

    for raw_line in frontmatter_text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line.lstrip().startswith("- "):
            # Lists are not needed by the contract checks. Keep the parser small.
            continue
        if ":" not in raw_line:
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        key, raw_value = raw_line.strip().split(":", 1)
        value = _parse_scalar(raw_value)

        while stack and indent <= stack[-1][0]:
            stack.pop()

        parent = stack[-1][1]
        parent[key] = value
        if isinstance(value, dict):
            stack.append((indent, value))

    return data


def _load_frontmatter(skill_md: Path) -> Tuple[Dict[str, Any], str]:
    content = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not match:
        raise ValueError("SKILL.md must start with YAML frontmatter")

    frontmatter_text = match.group(1)
    if yaml is None:
        return _parse_frontmatter_without_yaml(frontmatter_text), content

    data = yaml.safe_load(frontmatter_text)
    if not isinstance(data, dict):
        raise ValueError("SKILL.md frontmatter must be a mapping")
    return data, content


def validate(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    openai_yaml = skill_dir / "agents" / "openai.yaml"

    if not skill_md.exists():
        return ["SKILL.md is missing"]

    try:
        frontmatter, content = _load_frontmatter(skill_md)
    except Exception as exc:
        return [str(exc)]

    keys = set(frontmatter)
    unexpected = keys - ALLOWED_FRONTMATTER_KEYS
    if unexpected:
        errors.append(f"Unexpected top-level frontmatter keys: {', '.join(sorted(unexpected))}")

    forbidden = keys & FORBIDDEN_TOP_LEVEL_KEYS
    if forbidden:
        errors.append(f"Move platform-specific keys into metadata.platforms: {', '.join(sorted(forbidden))}")

    if frontmatter.get("name") != "skillsmp-find":
        errors.append("name must be skillsmp-find")

    description = frontmatter.get("description", "")
    if not isinstance(description, str) or len(description.strip()) < 120:
        errors.append("description must be a detailed trigger description")
    for phrase in ("Search SkillsMP", "AI agent skills", "Do not use as an installer"):
        if phrase not in description:
            errors.append(f"description must include: {phrase}")

    if frontmatter.get("license") != "MIT":
        errors.append("license must be MIT")

    metadata = frontmatter.get("metadata", {})
    if not isinstance(metadata, dict):
        errors.append("metadata must be a mapping")
        metadata = {}

    if metadata.get("primary_audience") != "AI agents":
        errors.append("metadata.primary_audience must be AI agents")
    if metadata.get("positioning") != "multi-ecosystem AI Agent Skill search tool":
        errors.append("metadata.positioning must document the multi-ecosystem positioning")

    platforms = metadata.get("platforms", {})
    if not isinstance(platforms, dict):
        errors.append("metadata.platforms must be a mapping")
        platforms = {}
    missing_platforms = REQUIRED_PLATFORM_KEYS - set(platforms)
    if missing_platforms:
        errors.append(f"metadata.platforms missing: {', '.join(sorted(missing_platforms))}")

    if platforms.get("agent_skills", {}).get("tier") != "primary":
        errors.append("metadata.platforms.agent_skills.tier must be primary")

    if not openai_yaml.exists():
        errors.append("agents/openai.yaml is missing")

    required_body_phrases = (
        "runtime contract",
        "Keyword Generation",
        "Project-Aware Search",
        "Boundaries",
        "run `analyze /path/to/project --json` first",
        'prefer AI-assisted search with `--ai`',
        "preserves keyword recall while adding semantic results",
        "keyword-only search",
        "`--limit 5` for normal recommendations",
        "default `recent` sort",
        "`--sort stars --limit 5`",
        "do not invent obscure occupation slugs",
        "Use `ai-search` only for pure semantic probes",
        "`--json` or `--save FILE`",
        "Report the top 3-5 matches",
        "Treat stars as a popularity signal",
        "do not install third-party skills yourself",
        "quota, missing-key, or network errors",
    )
    for phrase in required_body_phrases:
        if phrase not in content:
            errors.append(f"SKILL.md body must include: {phrase}")

    return errors


def main() -> int:
    skill_dir = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors = validate(skill_dir)
    if errors:
        print("Skill validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Skill validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
