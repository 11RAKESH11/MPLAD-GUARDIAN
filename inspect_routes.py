import inspect
from backend.app.main import app
import json

routes = []
for r in app.routes:
    if hasattr(r, "methods") and hasattr(r, "path"):
        methods = list(r.methods)
        path = r.path
        name = r.name
        doc = inspect.getdoc(r.endpoint) or ""
        routes.append({
            "path": path,
            "methods": methods,
            "name": name,
            "summary": doc.split("\n")[0] if doc else ""
        })

print(f"Total API Routes Registered: {len(routes)}")
for route in routes:
    print(f"  {','.join(route['methods']):<10} {route['path']:<45} ({route['name']})")

with open("api_routes_summary.json", "w", encoding="utf-8") as f:
    json.dump(routes, f, indent=2)
