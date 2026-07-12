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
            "manuscript_evidence": evidence,
            "authority_evidence": [{"source": "rules.md", "support": "Keep evidence exact."}],
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
                        "evidence": ["正文。"],
                        "authority_evidence": [{"source": "rules.md", "support": "Rule."}],
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


if __name__ == "__main__":
    unittest.main()
