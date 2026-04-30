import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALL_SH = ROOT / "install.sh"


class InstallScriptTests(unittest.TestCase):
    def run_install(self, *args):
        return subprocess.run(
            ["bash", str(INSTALL_SH), *args],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_project_requires_claude_code_target(self):
        result = self.run_install("--project")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No install target selected", result.stderr)

    def test_all_cannot_be_project_scoped(self):
        result = self.run_install("--all", "--project")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--project can only be used with --claude-code", result.stderr)


if __name__ == "__main__":
    unittest.main()
