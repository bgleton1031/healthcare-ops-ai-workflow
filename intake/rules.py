"""Pure validation and routing recommendations for fictional intake records."""

from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
import re

RULE_VERSION = "0.1.0"
PRACTICES = {"SYN-PRACTICE-01", "SYN-PRACTICE-02"}
REQUIRED = {
    "billing_request": ("practice_id", "case_id", "service_date", "request_description"),
    "payment_notice": ("practice_id", "case_id", "payment_reference", "payment_date", "payment_amount"),
    "follow_up": ("practice_id", "case_id", "correspondence_date", "issue_summary"),
}
QUEUES = {
    "billing_request": "Billing preparation",
    "payment_notice": "Payment review",
    "follow_up": "Follow-up review",
}
STATUSES = {"ready", "unreadable", "unsupported", "ambiguous", "processing_error"}


@dataclass(frozen=True)
class IntakeRecord:
    intake_id: str
    source_filename: str
    document_class: str
    fields: dict[str, str | None]
    processing_status: str = "ready"

    @classmethod
    def from_dict(cls, value: dict) -> "IntakeRecord":
        if not isinstance(value, dict):
            raise ValueError("Record must be a JSON object")
        allowed = {"intake_id", "source_filename", "document_class", "fields", "processing_status"}
        if set(value) - allowed:
            raise ValueError("Record contains unsupported properties")
        for key in ("intake_id", "source_filename", "document_class"):
            if not isinstance(value.get(key), str) or not value[key].strip():
                raise ValueError(f"{key} must be a nonempty string")
        fields = value.get("fields")
        if not isinstance(fields, dict) or any(
            not isinstance(k, str) or (v is not None and not isinstance(v, str))
            for k, v in fields.items()
        ):
            raise ValueError("fields must map names to strings or null")
        status = value.get("processing_status", "ready")
        if not isinstance(status, str) or status not in STATUSES:
            raise ValueError("Unsupported processing_status")
        return cls(**{**value, "fields": dict(fields)})


@dataclass(frozen=True)
class Recommendation:
    intake_id: str
    proposed_queue: str
    findings: tuple[str, ...]
    reason: str
    rule_version: str = RULE_VERSION
    approval_required: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


def evaluate(record: IntakeRecord) -> Recommendation:
    # Revalidate even callers that construct the dataclass directly.
    record = IntakeRecord.from_dict(asdict(record))
    if record.processing_status != "ready" or record.document_class not in REQUIRED:
        reason = (f"Processing status: {record.processing_status}"
                  if record.processing_status != "ready" else "Unknown document class")
        return Recommendation(record.intake_id, "Manual review", (reason,), reason)

    findings = []
    for name in REQUIRED[record.document_class]:
        value = record.fields.get(name)
        if value is None or not value.strip():
            findings.append(f"{name}: required")
            continue
        value = value.strip()
        if name == "practice_id" and value not in PRACTICES:
            findings.append(f"{name}: not in synthetic practice allowlist")
        elif name == "case_id" and not re.fullmatch(r"SYN-CASE-[0-9]{3}", value):
            findings.append(f"{name}: expected SYN-CASE-NNN")
        elif name.endswith("_date"):
            try:
                if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
                    raise ValueError
                date.fromisoformat(value)
            except ValueError:
                findings.append(f"{name}: expected a real date in YYYY-MM-DD format")
        elif name == "payment_amount":
            try:
                amount = Decimal(value)
                if not amount.is_finite() or amount < 0:
                    raise InvalidOperation
            except InvalidOperation:
                findings.append(f"{name}: expected a finite nonnegative number")

    queue = "Needs information" if findings else QUEUES[record.document_class]
    reason = "Required-field validation failed" if findings else f"Complete {record.document_class}"
    return Recommendation(record.intake_id, queue, tuple(findings), reason)
