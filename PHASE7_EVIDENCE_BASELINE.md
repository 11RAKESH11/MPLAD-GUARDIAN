# PHASE 7.0 — EVIDENCE ROOM & INVESTIGATION BASELINE AUDIT

**Project:** MPLAD GUARDIAN — Evidence Room + Source Traceability + Investigation Workspace  
**Audit Timestamp:** 2026-08-28T22:22:00+05:30  
**Auditor:** Principal Product Designer & Investigation Workflow Architect  

---

## 1. Executive Summary

A comprehensive forensic audit of the existing Evidence Room, Project Detail, Alert Detail, Relationship Graph, and Data Lineage was conducted.

**Current Foundation Verified:**
- 96,654 canonical projects with genuine, deterministic risk scores and model version tracking (`guardian-risk-2.0.0`).
- 270 verified analytical alerts with structured evidence and priority rankings.
- 36,732 comparable project relationships computed via multi-signal similarity.
- 106,442 expenditure payment vouchers linked directly to canonical work codes.
- 5-tier data lineage tracing projects to raw source CSV files.

**Audit Findings & Transformation Requirements:**
1. **From Modal to Analyst Workbench:** The previous implementation rendered evidence inside a dialog modal (`EvidenceRoomModal.tsx`). It must be elevated into a full-featured, vertical narrative **Analyst Workbench / Investigation Workspace** with dedicated shareable routing (`/evidence/:id` or deep-linked from `/alerts` and `/projects/:id`).
2. **Unified 11-Section Evidence Narrative:** Structure the investigation journey progressively:
   - `Signal Header & Summary` (Overall Score, Risk Tier, Confidence %, Evidence Coverage %, Investigation Priority, Model Version)
   - `Why Flagged` (Horizontal score contribution bars)
   - `Statistical Evidence` (Peer median, sample size, IQR, MAD, Robust Z, Percentile, Small-sample disclosures)
   - `Potential Duplicate Evidence` (Side-by-side Project A vs Project B comparison across 5 dimensions)
   - `Progress Gap Evidence` (Triggered Rule ID R1–R8, observed utilization vs threshold, elapsed months)
   - `Financial Position & Lifecycle Timeline` (Sanctioned, Disbursed, Expenditure, Remaining balance, Inconsistencies, Milestone timeline)
   - `Geographic Context` (District administrative context, zero GPS fabrication badge)
   - `Relationship Graph & Comparable Records` (Interactive connected nodes, similarity %, comparison reasons)
   - `Source Record & Collapsible Raw Viewer` (Source CSV, File, Ingestion run ID, raw JSON viewer)
   - `Data Lineage & Field-Level Provenance` (End-to-end 5-tier pipeline from Source CSV to Analyst Review; field-level value tracking)
   - `Actionable Review Checklist, Human Review Triage & Audit History` (Triage workflow `OPEN` $\to$ `UNDER_REVIEW` $\to$ `EVIDENCE_REQUESTED` $\to$ `RESOLVED` $\to$ `CLOSED`, Analyst notes, Audit log)
3. **Backend API Polish:** Ensure specialized REST endpoints (`/api/v1/alerts/{id}/evidence`, `/api/v1/projects/{id}/evidence`, `/api/v1/projects/{id}/lineage`, `/api/v1/projects/{id}/relationships`, `/api/v1/projects/{id}/vouchers`, `/api/v1/alerts/{id}/status`, `/api/v1/investigations/{id}/notes`, `/api/v1/investigations/{id}/history`) return rich, typed payloads with strict RBAC.
