# INVESTIGATION WORKFLOW

**Project:** MPLAD GUARDIAN  
**Document:** Investigation Review Lifecycle  
**Phase:** 7 — Evidence Room + Source Traceability  
**Updated:** 2026-08-28  

---

## 1. Purpose

This document defines the official Investigation Review Workflow for MPLAD GUARDIAN analytical signals. It governs how an analytical signal progresses from automated detection to human resolution.

> [!IMPORTANT]
> **Core Legal Principle:** MPLAD GUARDIAN analytical signals identify statistical anomalies and documentation patterns warranting human desk review. The system NEVER declares legal culpability, fraud, or corruption. All final determinations rest with authorized human reviewers.

---

## 2. Investigation Status Lifecycle

```
OPEN
  ↓ (Analyst assigns for review)
UNDER_REVIEW
  ↓ (Documentation needed from implementing agency)
EVIDENCE_REQUESTED
  ↓                    ↓
VALIDATED        NOT_SUBSTANTIATED
  ↓                    ↓
RESOLVED         RESOLVED
  ↓
CLOSED
```

### Status Definitions

| Status              | Description |
|--------------------|-------------|
| `OPEN`             | Signal generated; awaiting triage assignment |
| `UNDER_REVIEW`     | Active analyst desk review in progress |
| `EVIDENCE_REQUESTED` | Documentation requested from implementing agency / district authority |
| `VALIDATED`        | Analytical findings confirmed through documentation review |
| `NOT_SUBSTANTIATED`| Variance explained through documentation (e.g. scope revision, revised estimates) |
| `RESOLVED`         | Desk review concluded; all findings documented |
| `CLOSED`           | Signal archived; no further action required |

---

## 3. RBAC Authorization Matrix

| Action                    | VIEWER | ANALYST | ADMIN |
|--------------------------|--------|---------|-------|
| View evidence dossier     | ✅     | ✅      | ✅    |
| View audit history        | ✅     | ✅      | ✅    |
| View analyst notes        | ✅     | ✅      | ✅    |
| Update status             | ❌     | ✅      | ✅    |
| Add analyst note          | ❌     | ✅      | ✅    |
| Assign alert              | ❌     | ✅      | ✅    |
| Close / archive           | ❌     | ❌      | ✅    |

---

## 4. Workflow API Endpoints

### Status Transition
```
POST /api/v1/alerts/{alert_id}/status
Authorization: Bearer <ANALYST|ADMIN token>

{
  "status": "UNDER_REVIEW",
  "resolution_notes": "Initiating desk review of sanction estimates",
  "assigned_to": "Senior Investigator Ramesh"
}
```

Every status change:
1. Updates the `alerts` table (`status`, `assigned_to`, `acknowledged_by`, `resolved_by`, timestamps)
2. Inserts an immutable record in `audit_logs` (action: `ALERT_STATUS_UPDATE`)

### Add Analyst Note
```
POST /api/v1/alerts/{alert_id}/notes
Authorization: Bearer <ANALYST|ADMIN token>

{ "notes": "Requested measurement book from District PWD office." }
```

Every note addition:
1. Appends a timestamped entry to `alerts.resolution_notes`
2. Inserts an immutable record in `audit_logs` (action: `ANALYST_NOTE_ADDED`)

---

## 5. Audit Trail Format

Every investigation event logged to `audit_logs`:

```json
{
  "id": "uuid",
  "user_id": "usr-analyst-id",
  "username": "analyst",
  "user_role": "ANALYST",
  "action": "ALERT_STATUS_UPDATE | ANALYST_NOTE_ADDED",
  "target_type": "ALERT",
  "target_id": "ALT-XXXXXXXX",
  "previous_state": "OPEN",
  "new_state": "UNDER_REVIEW",
  "notes": "Desk review initiated",
  "created_at": "2026-08-28 22:11:00"
}
```

**Audit logs are append-only.** No update or delete operation is permitted on historical records.

---

## 6. Recommended Analyst Review Steps

When reviewing a high-priority analytical signal, analysts should follow:

1. **Review Administrative Approval** — Verify scope, Technical Sanction, and revision history against Works Sanctioned record.
2. **Estimate Verification** — Compare project estimate against applicable State PWD Schedule of Rates (SOR).
3. **Voucher Reconciliation** — Cross-reference disbursement vouchers against physically completed measurements.
4. **Duplicate Verification** — Confirm whether matching projects represent separate works or duplicate sanctions.
5. **Progress Documentation** — Request completion certificate, measurement book, or progress report from IDA.

---

## 7. Language & Interpretation Guidelines

### Approved Analytical Terminology
| Use This | Never Use This |
|----------|----------------|
| "Analytical Signal" | "Fraud Detected" |
| "High-Risk Anomaly" | "Fraudulent" |
| "Potential Duplicate" | "Corrupt" |
| "Statistically Unusual" | "Criminal" |
| "Progress Inconsistency" | "Illegal" |
| "Requires Review" | "Guilty" |

The UI enforces these terms in all system-generated content. Human analyst notes may contain professional assessment language but must not contain unsupported legal accusations.

---

## 8. Attachment Policy

File attachment support is documented as **future work**. Current implementation does not support file uploads to prevent premature introduction of unreviewed file storage architecture.

When implemented, attachments must:
- Validate MIME type whitelist (PDF, DOCX, XLSX, JPEG, PNG)
- Enforce file size limits (max 10MB)
- Store in controlled server-side path (no user-supplied filenames)
- Prevent path traversal (reject filenames with `..`, `/`, `\`)
- Block executable extensions (.exe, .bat, .ps1, .sh)
- Log upload events to audit_logs
