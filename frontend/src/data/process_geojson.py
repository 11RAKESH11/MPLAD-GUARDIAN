import json
import os

with open('frontend/src/data/india_states.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total features: {len(data['features'])}")
states = []
for f in data['features']:
    props = f['properties']
    name = props.get('NAME_1') or props.get('ST_NM') or props.get('st_nm') or props.get('State_Name') or props.get('NAME') or props.get('state_name') or list(props.values())[0]
    states.append(name)

print("States extracted:", states)
