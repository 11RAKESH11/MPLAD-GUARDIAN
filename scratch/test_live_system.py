#!/usr/bin/env python3
"""
Test Live Endpoints across Docker Stack via Host Ports 8000 (Backend) and 80 (Nginx)
"""
import urllib.request
import json
import ssl
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def test_endpoint(url, method="GET", body=None, headers=None):
    if headers is None:
        headers = {}
    if body and "Content-Type" not in headers:
        headers["Content-Type"] = "application/json"
    
    data = json.dumps(body).encode('utf-8') if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            status = resp.status
            content = json.loads(resp.read().decode('utf-8'))
            return status, content
    except urllib.error.HTTPError as e:
        content = e.read().decode('utf-8')
        try:
            content = json.loads(content)
        except:
            pass
        return e.code, content
    except Exception as e:
        return 500, str(e)

print("=" * 70)
print("  TESTING LIVE DOCKER STACK ENDPOINTS (PORT 8000 & PORT 80 NGINX)")
print("=" * 70)

results = []

def record(name, status_code, details=""):
    is_pass = 200 <= status_code < 300
    tag = "[PASS]" if is_pass else "[FAIL]"
    print(f"  {tag} {name} -> HTTP {status_code} {details}")
    results.append((name, is_pass, status_code, details))

# 1. Backend Health & Readiness
code, res = test_endpoint("http://localhost:8000/api/v1/health")
record("Backend Direct /health", code, f"env={res.get('environment') if isinstance(res, dict) else ''}")

code, res = test_endpoint("http://localhost:8000/api/v1/ready")
record("Backend Direct /ready", code, f"status={res.get('status') if isinstance(res, dict) else ''}")

# 2. Nginx Reverse Proxy /health
code, res = test_endpoint("http://localhost/api/v1/health")
record("Nginx Proxy -> /api/v1/health", code, f"status={res.get('status') if isinstance(res, dict) else ''}")

# 3. Authentication
login_payload = {"username": "admin", "password": "admin123"}
code, res = test_endpoint("http://localhost/api/v1/auth/login", method="POST", body=login_payload)
token = res.get("access_token") if isinstance(res, dict) else ""
auth_headers = {"Authorization": f"Bearer {token}"} if token else {}
record("Auth /login", code, f"user={res.get('user', {}).get('username') if isinstance(res, dict) else ''}")

# 4. Executive Dashboard
code, res = test_endpoint("http://localhost/api/v1/dashboard/overview", headers=auth_headers)
kpis = res.get("kpis", {}) if isinstance(res, dict) else {}
record("Dashboard /overview", code, f"projects={kpis.get('total_projects'):,}, sanctioned=Rs {float(kpis.get('total_sanctioned_funds') or 0):,.2f}")

code, res = test_endpoint("http://localhost/api/v1/dashboard/attention", headers=auth_headers)
record("Dashboard /attention", code, f"items={len(res.get('attention_items', [])) if isinstance(res, dict) else 0}")

code, res = test_endpoint("http://localhost/api/v1/dashboard/financial-flow", headers=auth_headers)
record("Dashboard /financial-flow", code, f"stages={len(res.get('stages', [])) if isinstance(res, dict) else 0}")

# 5. Projects Listing & Detail
code, res = test_endpoint("http://localhost/api/v1/projects?limit=5", headers=auth_headers)
meta = res.get("meta", {}) if isinstance(res, dict) else {}
first_work_code = res.get("data", [{}])[0].get("work_code") if isinstance(res, dict) and res.get("data") else ""
record("Projects List /projects", code, f"total={meta.get('total'):,}, returned={len(res.get('data', [])) if isinstance(res, dict) else 0}")

if first_work_code:
    code, res = test_endpoint(f"http://localhost/api/v1/projects/{first_work_code}", headers=auth_headers)
    record(f"Project Detail /projects/{first_work_code}", code, f"work_code={res.get('work_code') if isinstance(res, dict) else ''}")

# 6. Map / GIS Summary
code, res = test_endpoint("http://localhost/api/v1/map/summary", headers=auth_headers)
record("Map /map/summary", code, f"totalProjects={res.get('totalProjects'):,}, totalSanctioned=Rs {float(res.get('totalSanctioned') or 0):,.2f}")

code, res = test_endpoint("http://localhost/api/v1/map/states", headers=auth_headers)
record("Map /map/states", code, f"states_count={res.get('count') if isinstance(res, dict) else 0}")

# 7. Risk Engine Metrics
code, res = test_endpoint("http://localhost/api/v1/risks/summary", headers=auth_headers)
record("Risks /risks/summary", code, f"tiers={len(res.get('tiers', [])) if isinstance(res, dict) else 0}")

# 8. Alert Management Center
code, res = test_endpoint("http://localhost/api/v1/alerts?limit=5", headers=auth_headers)
record("Alerts /alerts", code, f"total={res.get('meta', {}).get('total') if isinstance(res, dict) else 0}")

# 9. Analytics Map Overview
code, res = test_endpoint("http://localhost/api/v1/analytics/map", headers=auth_headers)
record("Analytics /analytics/map", code, f"states_count={res.get('count') if isinstance(res, dict) else 0}")

# 10. Data Quality Summary
code, res = test_endpoint("http://localhost/api/v1/data-quality/summary", headers=auth_headers)
record("Data Quality /data-quality/summary", code, f"completeness={res.get('completeness_pct') if isinstance(res, dict) else ''}")

# 11. Audit Logs
code, res = test_endpoint("http://localhost/api/v1/audit-logs?limit=5", headers=auth_headers)
record("Audit Logs /audit-logs", code, f"total={res.get('meta', {}).get('total') if isinstance(res, dict) else 0}")

# 12. Frontend SPA Root (Nginx Port 80)
req = urllib.request.Request("http://localhost/")
try:
    with urllib.request.urlopen(req, timeout=5) as resp:
        html = resp.read().decode('utf-8')
        has_app = "<div id=\"root\">" in html or "<script" in html
        record("Frontend SPA Root (Nginx :80)", resp.status, "HTML SPA index loaded" if has_app else "HTML loaded")
except Exception as e:
    record("Frontend SPA Root (Nginx :80)", 500, str(e))

print("=" * 70)
passes = [r for r in results if r[1]]
fails = [r for r in results if not r[1]]
print(f"RESULTS: {len(passes)} PASSED, {len(fails)} FAILED")
print("=" * 70)
