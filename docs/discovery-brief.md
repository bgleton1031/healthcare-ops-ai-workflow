# Discovery Brief: Healthcare Billing Intake

**Status:** Proposed MVP scope for a portfolio demonstration  
**Date:** September 23, 2026  
**Customer:** Harborview Billing Services (fictional)

## 1. Purpose and evidence boundary

Build an AI-assisted intake workflow that helps a billing coordinator identify a document, extract relevant information, check completeness, and approve its destination queue.

The repository README establishes the business problem and intended capabilities: classification, extraction, deterministic validation, routing, human approval, and audit logging. The customer profile, operating model, rules, and targets below are design assumptions for this fictional scenario. They are not findings from customer interviews, measured results, or claims about a real healthcare organization.

Use synthetic documents and invented identifiers only. Do not include real patient information, client documents, credentials, internal configurations, or proprietary workflow details.

## 2. Fictional customer

Harborview Billing Services is a small outsourced billing operations team supporting several fictional outpatient practices. Its intake coordinators prepare incoming administrative documents for downstream billing specialists. An operations manager owns queue performance and exception handling.

For this scenario, documents arrive through shared email, scanned attachments, and manual uploads. Staff download them, inspect their contents, record key details in a tracking sheet, and choose a work queue. The MVP represents these channels through a single manual upload interface; connecting actual inboxes is outside the first release.

**Business objective:** Reduce repetitive intake work while making missing information and routing decisions visible to staff.

## 3. Current-state workflow and pain points

| Current step | Assumed pain point | Operational effect |
| --- | --- | --- |
| Collect documents from several channels | Inconsistent naming and packet structure | Staff repeatedly open files to understand the request |
| Identify document type and practice | Manual interpretation varies by coordinator | Items reach the wrong team or need a second review |
| Copy identifiers and request details | Repetitive data entry | More handling time and opportunities for transcription errors |
| Check required information | Checks depend on memory and informal checklists | Missing fields are discovered downstream |
| Select a destination queue | Routing rules are not consistently visible | Reassignment and avoidable delays |
| Record the decision | Notes are fragmented | Managers struggle to explain how an item was handled |

The initial hypothesis is that a reviewable draft containing extracted fields, explicit validation failures, and a proposed queue will reduce handling time without increasing routing mistakes. This needs evaluation; automation alone is not evidence of improvement.

## 4. Users and ownership

| Role | Needs | MVP responsibility |
| --- | --- | --- |
| Intake coordinator — primary user | A quick way to inspect source evidence, correct fields, and see missing information | Reviews every item and approves or overrides its proposed destination |
| Billing specialist — downstream user | Complete, correctly categorized work with clear context | Evaluates whether approved items are usable |
| Operations manager — business owner | Consistent rules, exception visibility, and measurable outcomes | Owns the fictional rules and pilot acceptance decision |
| Technical maintainer | Reproducible failures and traceable processing | Maintains extraction, validation, routing, and evaluation artifacts |

One reviewer role is sufficient for the local demo. Production identity, access control, and integration design remain future discovery work.

## 5. First workflow to build

**Workflow:** Review and route a single synthetic billing intake document.

**Trigger:** A coordinator uploads a supported document.

**Input boundary:** One text-based PDF per submission, containing one document. Start with three fictional document classes: billing request, payment/remittance notice, and follow-up correspondence. Scanned images, mixed-document packets, and password-protected files are unsupported in the MVP and must receive a clear exception outcome.

**Sequence:**

1. Assign an intake ID and retain the source for the local review session.
2. Extract readable text. If parsing fails or text is absent, stop automatic processing and show the exception.
3. Suggest a document class and extract structured fields, with supporting source excerpts or page references. Missing values remain empty; the system must not invent them.
4. Apply deterministic completeness and format checks using the rules below.
5. Propose a queue and display the rule that produced that recommendation.
6. Show the source, extracted fields, validation findings, and proposed queue together. Let the coordinator correct fields and rerun validation.
7. Require an explicit human decision to approve or override the destination. Require a reason for an override.
8. Save the approved result to a local simulated queue and record the decision in an audit event.

**Output:** A structured intake record containing the intake ID, source filename, suggested and reviewed class, extracted fields and evidence, validation findings, proposed and final queue, review decision, and timestamps.

**Completion condition:** The record has a human-approved destination, or a visible unresolved exception. A successful extraction alone does not mean intake is complete.

## 6. Initial validation and routing rules

These are fictional administrative rules, not healthcare billing standards. Required identifiers use invented values such as `SYN-CASE-001` and `SYN-PRACTICE-01`.

| Document class | Required information | Proposed queue when complete |
| --- | --- | --- |
| Billing request | Practice ID, case ID, service date, request description | Billing preparation |
| Payment/remittance notice | Practice ID, case ID, payment reference, payment date, payment amount | Payment review |
| Follow-up correspondence | Practice ID, case ID, correspondence date, issue summary | Follow-up review |

Rules execute in this order:

1. Unreadable, unsupported, unknown, or ambiguous documents go to **Manual review** as a recommendation, with a reason.
2. Recognized documents with missing or invalid required fields go to **Needs information** as a recommendation, listing each failed check.
3. Complete documents receive the class-specific queue recommendation above.

Validate dates as real calendar dates, practice IDs against a synthetic allowlist, case IDs against the defined synthetic pattern, and payment amounts as nonnegative numeric values. A format check does not establish that a value is factually correct; the reviewer compares it with the source. Conflicting candidate values require review rather than an arbitrary selection.

Avoid treating model-reported confidence as a calibrated probability. Any future confidence threshold must be justified with labeled examples. All queue recommendations still require human approval.

## 7. Constraints and safeguards

- **Data:** Use only synthetic fixtures, including document text and audit records. Do not connect live clinical, billing, or email systems.
- **Decision authority:** AI proposes a class and fields. Deterministic rules propose routing. A human authorizes the final destination.
- **Scope of action:** No claim submission, payment posting, external messaging, clinical advice, or changes to patient records.
- **Untrusted input:** Treat document content as data. Instructions embedded in a document must not change system rules or trigger actions.
- **Failure behavior:** Parsing errors, malformed model responses, and timeouts produce visible exceptions. They must not create an approved queue item.
- **Traceability:** Record intake ID, processing outcome, model/prompt/rule versions, validation findings, reviewer changes, decision reason, and timestamps. Keep secrets out of logs.
- **Review integrity:** Any edit after approval invalidates that approval and requires review again. Repeated approval of the same intake record must not create duplicate queue entries.
- **Implementation:** Start with a local demonstration and a simulated queue. Select the model, libraries, and storage approach during technical design; no production compliance certification is implied.

## 8. Success metrics and evaluation plan

All targets below are proposed acceptance criteria, not achieved results. The manual baseline has not been measured.

Create 60 labeled synthetic fixtures: 30 complete documents (10 per supported class), 15 incomplete or invalid documents (5 per class), and 15 exception cases covering unknown types, ambiguous values, unsupported inputs, and embedded instructions. Record expected fields, validation failures, and queue outcomes before testing. Reserve 20 fixtures as a held-out set, including each class and exception category; do not tune prompts against that set.

| Metric | How to measure | Proposed target |
| --- | --- | --- |
| Coordinator handling time | Compare manual intake with assisted intake, including review and correction, on at least 20 matched cases; counterbalance order to reduce familiarity effects | At least 30% lower median time, with no increase in final routing errors |
| Classification accuracy | Correct suggested class / supported, unambiguous held-out documents | At least 90%; report counts and errors by class |
| Required-field extraction accuracy | Correct normalized values / expected required-field slots on supported held-out documents; score correct absence separately from present values | At least 95%; report invented values separately |
| Validation correctness | Compare deterministic rule outcomes with labeled missing/invalid fields | 100% of defined rule checks pass on the rule test set |
| Routing correctness | Compare queue recommendations with labeled expected queues, including exception queues | At least 95% on held-out cases |
| Human control | Attempt routing before approval and after edits invalidate approval | Zero unapproved queue writes |
| Audit completeness | Inspect all approved and failed test runs for required events and decision fields | 100% traceable outcomes |

Report numerators, denominators, timing conditions, model version, latency, and model cost per processed document alongside percentages. The small synthetic set supports a portfolio demonstration; it does not establish real-world performance. Failed acceptance criteria should be documented and resolved or used to narrow scope before declaring the MVP complete.

## 9. MVP acceptance scenarios

- A complete billing request yields source-supported fields and a Billing preparation recommendation; nothing is routed until approval.
- A document missing its practice ID visibly identifies that failure and recommends Needs information.
- A coordinator corrects a misread field, reruns validation, and approves the updated destination; the audit record preserves the change.
- An unknown or ambiguous document recommends Manual review and explains why.
- An unreadable file or failed model call produces an exception without an approved queue record.
- A document containing instructions to bypass validation cannot bypass checks or human approval.
- An override records the reviewer-selected queue and reason; approving the same record twice produces one queue item.

## 10. Out of scope for the first release

Live inbox ingestion; OCR; multiple documents per packet; real patient or customer data; EHR or billing-platform integrations; medical coding; denial or eligibility decisions; automatic claim submission; automatic payment posting; production authentication; and production deployment.

## 11. Questions to validate in a real discovery engagement

1. Which intake document types account for the most volume and rework?
2. What are the actual daily volumes, handling times, misrouting rates, and backlog ages?
3. Which fields and destination queues are required, and who owns those rules?
4. What information would let a reviewer safely resolve an ambiguous or incomplete item?
5. Which systems, access restrictions, retention requirements, and approved AI environments constrain deployment?
6. Who can approve or override routing, and which decisions require escalation?
7. What operational improvement would justify a pilot, and who can authorize it?

## 12. Immediate implementation handoff

Define the intake record schema and synthetic fixtures first. Implement deterministic validation and queue rules against those fixtures, then add extraction and classification. Finish the first end-to-end slice with a review screen, explicit approval, a simulated queue, and an audit trail. Run the evaluation plan and record results before expanding input types or adding integrations.
