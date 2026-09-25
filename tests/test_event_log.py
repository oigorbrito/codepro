import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory
import unittest

from arkx.event_log import (
    ChainIntegrity,
    EventLogFormatError,
    audit_restored_chain,
)


def snapshot():
    return SimpleNamespace(
        manifest=SimpleNamespace(
            attempt_id="run-1",
            protocol_version="protocol-v1",
            schema_version=1,
            configuration_digest="config-digest",
            budget_digest="budget-digest",
            treatment="control",
            capability_digest="capability-digest",
        )
    )


def event(sequence, event_type, payload, previous_digest=None):
    value = {
        "sequence": sequence,
        "event_type": event_type,
        "payload": payload,
        "previous_digest": previous_digest,
    }
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    value["digest"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return value


def write_events(path: Path, events):
    path.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in events), encoding="utf-8")


class EventLogV1Tests(unittest.TestCase):
    def test_valid_single_event_is_complete(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            write_events(path, [event(0, "TASK_STARTED", {"task_id": "task-1"})])
            audit = audit_restored_chain(path, snapshot())
            self.assertIs(audit.integrity, ChainIntegrity.COMPLETE)
            self.assertEqual(audit.replay.run_id, "run-1")

    def test_valid_multi_event_chain_is_complete(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            first = event(0, "TASK_STARTED", {"task_id": "task-1"})
            second = event(1, "TASK_FINISHED", {"status": "BLOCKED"}, first["digest"])
            write_events(path, [first, second])
            audit = audit_restored_chain(path, snapshot())
            self.assertIs(audit.integrity, ChainIntegrity.COMPLETE)
            self.assertEqual(audit.chain.to_dict()["event_count"], 2)

    def test_empty_history_is_not_complete(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            path.write_text("", encoding="utf-8")
            audit = audit_restored_chain(path, snapshot())
            self.assertIs(audit.integrity, ChainIntegrity.EMPTY)
            self.assertIsNone(audit.chain.to_dict()["head_digest"])

    def test_invalid_schema_fails_closed(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            path.write_text(json.dumps({"sequence": 0}) + "\n", encoding="utf-8")
            with self.assertRaises(EventLogFormatError):
                audit_restored_chain(path, snapshot())

    def test_invalid_sequence_returns_invalid(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            write_events(path, [event(0, "TASK_STARTED", {}), event(2, "TASK_FINISHED", {}, "wrong")])
            audit = audit_restored_chain(path, snapshot())
            self.assertIs(audit.integrity, ChainIntegrity.INVALID)

    def test_invalid_digest_returns_tampered(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            item = event(0, "TASK_STARTED", {})
            item["digest"] = "0" * 64
            write_events(path, [item])
            audit = audit_restored_chain(path, snapshot())
            self.assertIs(audit.integrity, ChainIntegrity.TAMPERED)

    def test_invalid_previous_digest_returns_tampered(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            first = event(0, "TASK_STARTED", {})
            second = event(1, "TASK_FINISHED", {}, "f" * 64)
            write_events(path, [first, second])
            audit = audit_restored_chain(path, snapshot())
            self.assertIs(audit.integrity, ChainIntegrity.TAMPERED)

    def test_missing_or_invalid_file_raises_format_error(self):
        with TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.jsonl"
            with self.assertRaises(EventLogFormatError):
                audit_restored_chain(missing, snapshot())
            invalid = Path(directory) / "invalid.jsonl"
            invalid.write_text("not-json\n", encoding="utf-8")
            with self.assertRaises(EventLogFormatError):
                audit_restored_chain(invalid, snapshot())

    def test_to_dict_is_deterministic(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            write_events(path, [event(0, "EVIDENCE_ADDED", {"z": 1, "a": "é"})])
            first = audit_restored_chain(path, snapshot()).chain.to_dict()
            second = audit_restored_chain(path, snapshot()).chain.to_dict()
            self.assertEqual(first, second)
            self.assertEqual(json.dumps(first, ensure_ascii=False, sort_keys=True), json.dumps(second, ensure_ascii=False, sort_keys=True))

    def test_to_dict_includes_consumed_chain_references(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            first = event(0, "EVIDENCE_ADDED", {"stage": "verification", "ref": "verification://1"})
            second = event(1, "EVIDENCE_ADDED", {"stage": "acceptance", "ref": "acceptance://1"}, first["digest"])
            third = event(2, "EVIDENCE_ADDED", {"stage": "promotion", "ref": "promotion://1"}, second["digest"])
            write_events(path, [first, second, third])
            values = audit_restored_chain(path, snapshot()).chain.to_dict()
            self.assertEqual(values["verification_ref"], "verification://1")
            self.assertEqual(values["acceptance_ref"], "acceptance://1")
            self.assertEqual(values["promotion_ref"], "promotion://1")

    def test_missing_required_reference_is_explicitly_null(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            write_events(path, [event(0, "EVIDENCE_ADDED", {"stage": "verification", "ref": "verification://1"})])
            values = audit_restored_chain(path, snapshot()).chain.to_dict()
            self.assertIsNone(values["acceptance_ref"])
            self.assertIsNone(values["promotion_ref"])

    def test_references_are_deterministic_and_bound_to_audited_events(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            item = event(0, "EVIDENCE_ADDED", {"stage": "verification", "ref": "verification://1"})
            write_events(path, [item])
            first = audit_restored_chain(path, snapshot()).chain.to_dict()
            second = audit_restored_chain(path, snapshot()).chain.to_dict()
            self.assertEqual(first["verification_ref"], second["verification_ref"])
            self.assertEqual(first["verification_ref"], "verification://1")

    def test_digest_uses_canonical_payload_order_and_utf8(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            item = event(0, "EVIDENCE_ADDED", {"b": "é", "a": 1})
            write_events(path, [item])
            audit = audit_restored_chain(path, snapshot())
            self.assertIs(audit.integrity, ChainIntegrity.COMPLETE)

    def test_events_are_ordered_and_immutable(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            write_events(path, [event(0, "TASK_STARTED", {})])
            events = audit_restored_chain(path, snapshot()).chain.events
            self.assertIsInstance(events, tuple)
            with self.assertRaises(TypeError):
                events[0] = events[0]


if __name__ == "__main__":
    unittest.main()
