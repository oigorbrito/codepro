import importlib
import unittest


class AdapterImportBoundaryTests(unittest.TestCase):
    def test_openrouter_module_import_does_not_select_a_fallback(self):
        module = importlib.import_module("tools.p82_openrouter_model")
        self.assertTrue(hasattr(module, "MINISWEAGENT_AVAILABLE"))
        if not module.MINISWEAGENT_AVAILABLE:
            with self.assertRaises(RuntimeError):
                module.ArkxOpenRouterModel()

    def test_bash_module_import_does_not_select_a_fallback(self):
        module = importlib.import_module("tools.p82_bash_environment")
        self.assertTrue(hasattr(module, "MINISWEAGENT_AVAILABLE"))
        if not module.MINISWEAGENT_AVAILABLE:
            with self.assertRaises(RuntimeError):
                module.BashLocalEnvironment()


if __name__ == "__main__":
    unittest.main()
