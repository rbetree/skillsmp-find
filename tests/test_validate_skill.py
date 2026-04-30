import importlib.util
import tempfile
import textwrap
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_skill.py"
SPEC = importlib.util.spec_from_file_location("skillsmp_validate", MODULE_PATH)
validate_skill = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validate_skill)


class ValidateSkillTests(unittest.TestCase):
    def test_current_skill_contract_is_valid(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(validate_skill.validate(root), [])

    def test_skill_prompts_agents_to_prefer_ai_when_key_exists(self):
        root = Path(__file__).resolve().parents[1]
        content = (root / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("If an API key is configured", content)
        self.assertIn('prefer AI-assisted search with `--ai`', content)
        self.assertIn("keyword-only search", content)

    def test_skill_documents_runtime_decision_rules(self):
        root = Path(__file__).resolve().parents[1]
        content = (root / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("run `analyze /path/to/project --json` first", content)
        self.assertIn("search with both Chinese and English using `-b`", content)
        self.assertIn("`--json` or `--save FILE`", content)
        self.assertIn("do not install third-party skills yourself", content)
        self.assertIn("quota, missing-key, or network errors", content)

    def test_skill_documents_agent_search_selection_rules(self):
        root = Path(__file__).resolve().parents[1]
        content = (root / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("preserves keyword recall while adding semantic results", content)
        self.assertIn("`--limit 5` for normal recommendations", content)
        self.assertIn("default `recent` sort", content)
        self.assertIn("do not invent obscure occupation slugs", content)
        self.assertIn("Use `ai-search` only for pure semantic probes", content)
        self.assertIn("Report the top 3-5 matches", content)
        self.assertIn("Treat stars as a popularity signal", content)

    def test_readmes_document_bilingual_argument_value(self):
        root = Path(__file__).resolve().parents[1]
        readme = (root / "README.md").read_text(encoding="utf-8")
        readme_zh = (root / "docs" / "lang" / "README_ZH.md").read_text(encoding="utf-8")

        expected = 'search "前端鉴权" -b "frontend authorization"'
        self.assertIn(expected, readme)
        self.assertIn(expected, readme_zh)
        self.assertNotIn('search "前端鉴权" -b --limit', readme)
        self.assertNotIn('search "前端鉴权" -b --limit', readme_zh)

    def test_rejects_platform_specific_top_level_keys(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "agents").mkdir()
            (root / "agents" / "openai.yaml").write_text("interface: {}\n", encoding="utf-8")
            (root / "SKILL.md").write_text(
                textwrap.dedent(
                    """\
                    ---
                    name: skillsmp-find
                    description: "Search SkillsMP for AI agent skills. Do not use as an installer. This intentionally long trigger description mentions AI agent skills and Search SkillsMP."
                    license: MIT
                    activation: /skillsmp-find
                    metadata:
                      primary_audience: "AI agents"
                      positioning: "multi-ecosystem AI Agent Skill search tool"
                      platforms:
                        agent_skills:
                          tier: primary
                        codex: {}
                        claude_code: {}
                        hermes: {}
                        openclaw: {}
                        universal_agents: {}
                    ---

                    runtime contract
                    Keyword Generation
                    Project-Aware Search
                    Boundaries
                    """
                ),
                encoding="utf-8",
            )

            errors = validate_skill.validate(root)

        self.assertTrue(
            any("Move platform-specific keys" in error for error in errors),
            errors,
        )

    def test_fallback_parser_supports_nested_platform_metadata(self):
        root = Path(__file__).resolve().parents[1]
        skill_md = root / "SKILL.md"
        original_yaml = validate_skill.yaml

        try:
            validate_skill.yaml = None
            frontmatter, _ = validate_skill._load_frontmatter(skill_md)
        finally:
            validate_skill.yaml = original_yaml

        platforms = frontmatter["metadata"]["platforms"]
        self.assertEqual(platforms["agent_skills"]["tier"], "primary")
        self.assertEqual(platforms["codex"]["tier"], "validated")


if __name__ == "__main__":
    unittest.main()
