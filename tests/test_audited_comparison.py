import unittest
from unittest.mock import patch

from arkx.event_log import ChainIntegrity
from arkx.harness import AttemptStore


class AuditedComparisonTests(unittest.TestCase):
    def test_comparison_rejects_incomplete_audited_chain(self):
        audit = type("Audit", (), {"integrity": ChainIntegrity.INCOMPLETE})()
        with patch("arkx.harness.load_attempt", side_effect=["left", "right"]):
            with patch.object(AttemptStore, "load_audited", side_effect=[audit, audit]):
                with self.assertRaises(ValueError):
                    AttemptStore("artifacts").compare_audited("left", "left-events", "right", "right-events")


if __name__ == "__main__":
    unittest.main()
