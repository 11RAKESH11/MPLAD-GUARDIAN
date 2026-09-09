# Observability & Monitoring Plan

## 1. Request Correlation & Tracing
- **X-Request-ID Header:** All incoming requests generate a unique UUIDv4 which is attached to the request state and returned in the HTTP response headers as `X-Request-ID`.
- **Log Enrichment:** The `X-Request-ID` is injected into backend log statements, allowing analysts and site reliability engineers to trace a specific request through the entire stack.
- **Client Side:** The frontend can extract the `X-Request-ID` from the response headers and include it in any bug reports or error tracking tools (e.g., Sentry).

## 2. Standardized Error Handling
- **Format:** All API errors are normalized into a predictable `{ "error": { "code": "...", "message": "...", "request_id": "..." } }` structure.
- **Validation Errors:** Handled centrally in `main.py` via `RequestValidationError` exception handlers, keeping business logic clean.
- **HTTP Exceptions:** Managed via `HTTPException` handler, standardizing the format and maintaining `X-Request-ID` correlation.

## 3. Health & Readiness Monitoring
- **`/api/v1/health`:** Lightweight, instantaneous Liveness Probe. Indicates if the FastAPI web process is running.
- **`/api/v1/ready`:** Deep Readiness Probe. Validates the backend's connection to the database (`SELECT 1`). Returns HTTP 503 if the database is unreachable, correctly instructing load balancers to remove the node from the active pool.

## 4. Background Job Tracking
- **Job Status:** Background operations (e.g., AI Analysis) trigger a queued job. The state is tracked in the `background_jobs` table.
- **Polling / Monitoring:** Frontend or monitoring systems can poll `/api/v1/jobs/{job_id}` to track execution time, completion status, and parse error messages asynchronously.

## 5. Security & Audit Logging
- **Authentication Events:** Login attempts, failures, rate limits, and password changes are securely logged as audit events in the `audit_logs` table.
- **Business Operations:** Status changes to alerts are tracked as audit events linking the user ID and role with the action.
- **Future Integration:** Export audit logs to a centralized SIEM (Security Information and Event Management) platform like ELK, Splunk, or Datadog via a separate logging sidecar.
