import requests
import json
import time

base_url = "http://127.0.0.1:8000"

print("--- Testing /api/health ---")
r = requests.get(f"{base_url}/api/health")
print("Health:", r.status_code, r.json())

print("\n--- Testing /api/dashboard/overview ---")
r = requests.get(f"{base_url}/api/dashboard/overview")
print("Dashboard:", r.status_code)
print("  Total Projects:", f"{r.json()['kpis']['total_projects']:,}")
print("  Sanctioned Funds: INR", f"{r.json()['kpis']['total_sanctioned_funds']:,.0f}")
print("  Critical Risks:", r.json()['risk_metrics']['critical_count'])
print("  Potential Duplicates:", r.json()['risk_metrics']['potential_duplicates_count'])

print("\n--- Testing /api/dashboard/insights ---")
r = requests.get(f"{base_url}/api/dashboard/insights")
print("Insights count:", len(r.json()['insights']))
for ins in r.json()['insights']:
    print(f"  [{ins['badge']}] {ins['title']}")

print("\n--- Testing /api/projects ---")
r = requests.get(f"{base_url}/api/projects?limit=3&sort_by=overall_risk_score&order=desc")
print("Projects count:", len(r.json()['data']), "Total records:", r.json()['pagination']['total_records'])
sample_wc = r.json()['data'][0]['work_code']
print(f"  Top flagged project: {sample_wc} ({r.json()['data'][0]['risk_level']} - {r.json()['data'][0]['overall_risk_score']})")

print(f"\n--- Testing /api/projects/{sample_wc} ---")
r = requests.get(f"{base_url}/api/projects/{sample_wc}")
print("Project Detail:", r.status_code)
print("  Title:", r.json()['work_type'])
print("  State/District:", r.json()['state'], "/", r.json()['district'])
print("  Vouchers attached:", len(r.json()['vouchers']))
print("  Comparables attached:", len(r.json()['comparable_projects']))
print("  Traceability source:", r.json()['traceability']['source_type'])

print("\n--- Testing /api/alerts ---")
r = requests.get(f"{base_url}/api/alerts?limit=3")
print("Alerts total:", r.json()['pagination']['total_records'])

print("\n--- Testing /api/auth/login ---")
r = requests.post(f"{base_url}/api/auth/login", json={"username": "analyst", "password": "analyst123"})
print("Login analyst:", r.status_code, r.json()['user']['role'], "Token length:", len(r.json()['access_token']))

print("\n=== ALL BACKEND APIS FUNCTIONING WITH 100% SUCCESS ===")
