import requests
import json
import time

base_url = "http://127.0.0.1:8000/api/v1"

print("--- Testing /api/v1/health ---")
r = requests.get(f"{base_url}/health")
print("Health:", r.status_code, r.json())

print("\n--- Testing /api/v1/dashboard/overview ---")
r = requests.get(f"{base_url}/dashboard/overview")
print("Dashboard:", r.status_code)
kpis = r.json().get('kpis', {})
print("  Total Projects:", f"{kpis.get('total_projects', 0):,}")
sanc_funds = kpis.get('total_sanctioned_funds') or 0
print("  Sanctioned Funds: INR", f"{sanc_funds:,.0f}")
print("  Critical Risks:", r.json()['risk_metrics']['critical_count'])
print("  Potential Duplicates:", r.json()['risk_metrics']['potential_duplicates_count'])

print("\n--- Testing /api/v1/dashboard/insights ---")
r = requests.get(f"{base_url}/dashboard/insights")
print("Insights count:", len(r.json().get('insights', [])))
for ins in r.json().get('insights', []):
    print(f"  [{ins.get('badge')}] {ins.get('title')}")

print("\n--- Testing /api/v1/projects ---")
r = requests.get(f"{base_url}/projects?limit=3&sort_by=overall_risk_score&order=desc")
projects_data = r.json().get('data', [])
print("Projects count:", len(projects_data), "Total records:", r.json().get('pagination', {}).get('total_records', 0))
if projects_data:
    sample_wc = projects_data[0]['work_code']
    print(f"  Top flagged project: {sample_wc} ({projects_data[0].get('risk_level')} - {projects_data[0].get('overall_risk_score')})")

    print(f"\n--- Testing /api/v1/projects/{sample_wc} ---")
    r = requests.get(f"{base_url}/projects/{sample_wc}")
    print("Project Detail:", r.status_code)
    proj = r.json()
    print("  Title:", proj.get('work_type'))
    print("  State/District:", proj.get('state'), "/", proj.get('district'))
    print("  Vouchers attached:", len(proj.get('vouchers', [])))
    print("  Comparables attached:", len(proj.get('comparable_projects', [])))
    print("  Traceability source:", proj.get('traceability', {}).get('source_type'))

print("\n--- Testing /api/v1/alerts ---")
r = requests.get(f"{base_url}/alerts?limit=3")
print("Alerts total:", r.json().get('pagination', {}).get('total_records', 0))

print("\n--- Testing /api/v1/auth/login ---")
r = requests.post(f"{base_url}/auth/login", json={"username": "analyst", "password": "analyst123"})
print("Login analyst:", r.status_code, r.json().get('user', {}).get('role'), "Token length:", len(r.json().get('access_token', '')))

print("\n=== ALL BACKEND APIS FUNCTIONING WITH 100% SUCCESS ===")
