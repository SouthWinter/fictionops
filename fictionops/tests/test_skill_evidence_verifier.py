from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "integrations"
    / "codex-skill"
    / "fictionops-writing-agent"
    / "scripts"
    / "verify_teacher_evidence.py"
)
SPEC = importlib.util.spec_from_file_location("verify_teacher_evidence", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TeacherEvidenceVerifierTests(unittest.TestCase):
    @staticmethod
    def decision(evidence: list[str]) -> dict[str, object]:
        return {
            "schema": "fictionops.teacher_decision.v1",
            "task_id": "test-task",
            "decision": "uphold",
            "category": "prose_reader_experience",
            "severity": "P4",
            "scope": "one paragraph",
            "problem": "Repeated explanation.",
            "manuscript_evidence": evidence,
            "authority_evidence": [{"source": "rules.md", "support": "Keep evidence exact."}],
            "strongest_counterevidence": "The repetition may be functional.",
            "countercheck_effect": "The claim was narrowed.",
            "resolution_reason": "One redundant layer remains.",
            "preserve_constraints": ["Keep the action."],
            "suggested_action": "Review one paragraph later.",
            "confidence": 0.8,
            "manuscript_edited": False,
            "teacher_ground_truth": False,
        }

    def test_accepts_markdown_whitespace_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.md"
            decision = root / "decision.json"
            source.write_text("第一句。\n\n第二句。\n", encoding="utf-8")
            decision.write_text(
                json.dumps(self.decision(["第一句。第二句。"]), ensure_ascii=False),
                encoding="utf-8",
            )

            result = MODULE.verify(source, decision)

            self.assertEqual(result["status"], "pass")
            self.assertTrue(result["matches"][0]["matched"])

    def test_rejects_added_quote_marks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.md"
            decision = root / "decision.json"
            source.write_text("原纸还在。", encoding="utf-8")
            decision.write_text(
                json.dumps(self.decision(["“原纸还在。”"]), ensure_ascii=False),
                encoding="utf-8",
            )

            result = MODULE.verify(source, decision)

            self.assertEqual(result["status"], "fail")
            self.assertFalse(result["matches"][0]["matched"])

    def test_requires_typed_manuscript_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.md"
            decision = root / "decision.json"
            source.write_text("正文。", encoding="utf-8")
            decision.write_text(
                json.dumps(
                    {
                        "schema": "fictionops.teacher_decision.v1",
                        "task_id": "test-task",
                        "decision": "uphold",
                        "category": "prose_reader_experience",
                        "severity": "P4",
                        "scope": "one line",
                        "problem": "A problem.",
                        "evidence": ["正文。"],
                        "authority_evidence": [{"source": "rules.md", "support": "Rule."}],
                        "strongest_counterevidence": "Counterevidence.",
                        "countercheck_effect": "No change.",
                        "resolution_reason": "Reason.",
                        "preserve_constraints": ["Keep action."],
                        "suggested_action": "Review later.",
                        "confidence": 0.8,
                        "manuscript_edited": False,
                        "teacher_ground_truth": False,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = MODULE.verify(source, decision)

            self.assertEqual(result["status"], "fail")
            self.assertTrue(any("manuscript_evidence must be" in error for error in result["errors"]))
            self.assertTrue(any("legacy evidence" in error for error in result["errors"]))

    def test_rejects_missing_authority_and_boundary_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.md"
            decision = root / "decision.json"
            source.write_text("正文。", encoding="utf-8")
            decision.write_text(
                json.dumps({"manuscript_evidence": ["正文。"]}, ensure_ascii=False),
                encoding="utf-8",
            )

            result = MODULE.verify(source, decision)

            self.assertEqual(result["status"], "fail")
            self.assertTrue(any("authority_evidence" in error for error in result["errors"]))
            self.assertTrue(any("manuscript_edited" in error for error in result["errors"]))
            self.assertTrue(any("teacher_ground_truth" in error for error in result["errors"]))

    def test_rejects_nested_finding_and_schema_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.md"
            decision = root / "decision.json"
            source.write_text("正文。", encoding="utf-8")
            payload = self.decision(["正文。"])
            payload["finding"] = {"claim": payload.pop("problem")}
            payload["recommended_next_action"] = payload.pop("suggested_action")
            decision.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            result = MODULE.verify(source, decision)

            self.assertEqual(result["status"], "fail")
            self.assertTrue(any("nested finding" in error for error in result["errors"]))
            self.assertTrue(any("problem must be" in error for error in result["errors"]))
            self.assertTrue(any("suggested_action must be" in error for error in result["errors"]))

    def test_rejects_non_priority_severity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.md"
            decision = root / "decision.json"
            source.write_text("正文。", encoding="utf-8")
            payload = self.decision(["正文。"])
            payload["severity"] = "major"
            decision.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            result = MODULE.verify(source, decision)

            self.assertEqual(result["status"], "fail")
            self.assertTrue(any("severity must be" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
