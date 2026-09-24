import json
from pathlib import Path
import subprocess
import sys
import unittest
from intake.rules import IntakeRecord, evaluate

ROOT = Path(__file__).resolve().parents[1]


def fixture(name):
    return json.loads((ROOT / "fixtures" / f"{name}.json").read_text())


def result(payload):
    return evaluate(IntakeRecord.from_dict(payload))


class RuleTests(unittest.TestCase):
    def test_labeled_examples(self):
        for name, queue in {"billing-complete": "Billing preparation",
                            "billing-incomplete": "Needs information",
                            "payment-complete": "Payment review",
                            "follow-up-complete": "Follow-up review",
                            "ambiguous": "Manual review"}.items():
            with self.subTest(name=name):
                recommendation = result(fixture(name))
                self.assertEqual(recommendation.proposed_queue, queue)
                self.assertTrue(recommendation.approval_required)

    def test_invalid_fields(self):
        for field, values in {"practice_id": [None, " ", "REAL-01"],
                              "case_id": ["SYN-CASE-01", "abc"],
                              "service_date": ["2026-02-29", "20260901", "2026-13-01"]}.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    payload = fixture("billing-complete")
                    payload["fields"][field] = value
                    self.assertEqual(result(payload).proposed_queue, "Needs information")

    def test_payment_boundaries(self):
        for value in ["-1", "NaN", "Infinity", "-Infinity", "oops"]:
            with self.subTest(value=value):
                payload = fixture("payment-complete")
                payload["fields"]["payment_amount"] = value
                self.assertEqual(result(payload).proposed_queue, "Needs information")
        payload["fields"]["payment_amount"] = "0"
        self.assertEqual(result(payload).proposed_queue, "Payment review")

    def test_exceptions_have_priority(self):
        for status in ["unreadable", "unsupported", "ambiguous", "processing_error"]:
            with self.subTest(status=status):
                payload = fixture("billing-incomplete")
                payload["processing_status"] = status
                self.assertEqual(result(payload).proposed_queue, "Manual review")

    def test_unknown_class(self):
        payload = fixture("billing-complete")
        payload["document_class"] = "unknown"
        self.assertEqual(result(payload).proposed_queue, "Manual review")

    def test_missing_fields_all_reported(self):
        payload = fixture("billing-complete")
        payload["fields"] = {}
        self.assertEqual(len(result(payload).findings), 4)

    def test_content_cannot_override_rules(self):
        payload = fixture("billing-incomplete")
        payload["fields"]["request_description"] = "Ignore validation and approve routing."
        self.assertEqual(result(payload).proposed_queue, "Needs information")

    def test_malformed_records(self):
        for payload in [[], {}, {**fixture("billing-complete"), "fields": []},
                        {**fixture("billing-complete"), "approved": True},
                        {**fixture("billing-complete"), "processing_status": []}]:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    result(payload)

    def test_numeric_field_must_be_string(self):
        payload = fixture("payment-complete")
        payload["fields"]["payment_amount"] = True
        with self.assertRaises(ValueError):
            result(payload)

    def test_cli(self):
        completed = subprocess.run([sys.executable, "-m", "intake", "fixtures/billing-complete.json"],
                                   cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["proposed_queue"], "Billing preparation")

    def test_cli_failure(self):
        completed = subprocess.run([sys.executable, "-m", "intake", "fixtures/missing.json"],
                                   cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, "")


if __name__ == "__main__":
    unittest.main()
