import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "search.py"
SPEC = importlib.util.spec_from_file_location("skillsmp_search", MODULE_PATH)
search = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(search)


class EnvLoadingTests(unittest.TestCase):
    def test_load_dotenv_reads_repo_env_without_overriding_existing_env(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dotenv_path = Path(tmpdir) / ".env"
            dotenv_path.write_text(
                "\n".join(
                    [
                        "# comment",
                        "SKILLSMP_API_KEY=from-dotenv",
                        "export EXTRA_FLAG='enabled'",
                    ]
                ),
                encoding="utf-8",
            )

            with mock.patch.dict(os.environ, {"SKILLSMP_API_KEY": "from-env"}, clear=True):
                loaded = search.load_dotenv(str(dotenv_path))

                self.assertTrue(loaded)
                self.assertEqual(os.environ["SKILLSMP_API_KEY"], "from-env")
                self.assertEqual(os.environ["EXTRA_FLAG"], "enabled")

    def test_load_config_uses_dotenv_when_env_not_set(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dotenv_path = Path(tmpdir) / ".env"
            dotenv_path.write_text("SKILLSMP_API_KEY=from-dotenv\n", encoding="utf-8")

            with mock.patch.object(search, "DOTENV_PATH", str(dotenv_path)):
                with mock.patch.object(search, "CONFIG_PATH", str(Path(tmpdir) / "missing-config.yaml")):
                    with mock.patch.object(search, "HERMES_CONFIG_PATH", str(Path(tmpdir) / "missing-hermes.yaml")):
                        with mock.patch.dict(os.environ, {}, clear=True):
                            config = search.load_config()

            self.assertEqual(config["api_key"], "from-dotenv")


if __name__ == "__main__":
    unittest.main()
