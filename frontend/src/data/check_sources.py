import urllib.request
import json
import os

urls = [
    ('india_states_soi.json', 'https://raw.githubusercontent.com/adarshbiradar/maps-geojson/master/india_telangana.geojson'),
    ('india_states_datameet.json', 'https://raw.githubusercontent.com/datameet/maps/master/Country/india-composite.geojson'),
    ('india_states_udit.json', 'https://raw.githubusercontent.com/udit-001/india-maps-data/master/india.geojson')
]

for name, url in urls:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            features = data.get("features", [])
            print(f"{name}: features={len(features)}")
            if features:
                keys = list(features[0]['properties'].keys())
                print(f"  props keys: {keys}")
                names = [f['properties'].get('ST_NM') or f['properties'].get('st_nm') or f['properties'].get('state_name') or f['properties'].get('NAME_1') or list(f['properties'].values())[0] for f in features]
                unique_names = sorted(list(set(filter(None, names))))
                print(f"  count unique states: {len(unique_names)}")
                print(f"  sample states: {unique_names}")
    except Exception as e:
        print(f"{name} failed: {e}")
