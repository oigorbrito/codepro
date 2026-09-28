from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class R5ProductSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = (ROOT / "server.ts").read_text(encoding="utf-8-sig")
        cls.app = (ROOT / "src" / "App.tsx").read_text(encoding="utf-8-sig")

    def test_doctor_requires_explicit_python_core(self):
        self.assertIn("process.env.CODEPRO_PYTHON", self.server)
        self.assertIn("Python Execution Core (CODEPRO_PYTHON)", self.server)
        self.assertNotIn("Optional/Legacy", self.server)
        self.assertIn("checks.every((check) => check.ok)", self.server)

    def test_p1_p2_p3_are_non_authoritative_previews(self):
        self.assertIn("canonical_authority: 'src/arkx/characterization.py'", self.server)
        self.assertIn("canonical_authority: 'src/arkx/progress.py'", self.server)
        self.assertIn("canonical_authority: 'src/arkx/routing.py'", self.server)
        self.assertGreaterEqual(self.server.count("NON_AUTHORITATIVE_PREVIEW"), 4)

    def test_m1_ts_surface_cannot_issue_authoritative_accepted(self):
        self.assertIn("canonical_authority: 'src/arkx/acceptance.py'", self.server)
        self.assertIn("WOULD_ACCEPT", self.server)
        self.assertIn("WOULD_REJECT", self.server)
        self.assertNotIn("res.json(decision);", self.server)

    def test_ui_marks_preview_surfaces(self):
        self.assertIn("Task Characterization & Routing Preview", self.app)
        self.assertIn("M1 Acceptance Preview (Non-authoritative)", self.app)


if __name__ == "__main__":
    unittest.main()
