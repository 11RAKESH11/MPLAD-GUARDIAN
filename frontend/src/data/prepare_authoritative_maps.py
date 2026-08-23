import urllib.request
import json
import os

print("Fetching Authoritative India State and District GeoJSON datasets...")

# 1. State Normalization Mapping (matches SQLite database 36 States/UTs exactly)
STATE_NAME_MAP = {
    'Andaman & Nicobar': 'Andaman And Nicobar Islands',
    'Andaman & Nicobar Islands': 'Andaman And Nicobar Islands',
    'Andaman and Nicobar': 'Andaman And Nicobar Islands',
    'Andaman and Nicobar Islands': 'Andaman And Nicobar Islands',
    'ANDAMAN AND NICOBAR ISLANDS': 'Andaman And Nicobar Islands',
    'Andhra Pradesh': 'Andhra Pradesh',
    'ANDHRA PRADESH': 'Andhra Pradesh',
    'Arunanchal Pradesh': 'Arunachal Pradesh',
    'Arunachal Pradesh': 'Arunachal Pradesh',
    'ARUNACHAL PRADESH': 'Arunachal Pradesh',
    'Assam': 'Assam',
    'ASSAM': 'Assam',
    'Bihar': 'Bihar',
    'BIHAR': 'Bihar',
    'Chandigarh': 'Chandigarh',
    'CHANDIGARH': 'Chandigarh',
    'Chhattisgarh': 'Chhattisgarh',
    'CHHATTISGARH': 'Chhattisgarh',
    'Dadra & Nagar Haveli': 'Dadra And Nagar Haveli And Daman And Diu',
    'Dadra & Nagar Haveli & Daman & Diu': 'Dadra And Nagar Haveli And Daman And Diu',
    'Dadra and Nagar Haveli and Daman and Diu': 'Dadra And Nagar Haveli And Daman And Diu',
    'Dadara & Nagar Havelli': 'Dadra And Nagar Haveli And Daman And Diu',
    'Daman & Diu': 'Dadra And Nagar Haveli And Daman And Diu',
    'Daman and Diu': 'Dadra And Nagar Haveli And Daman And Diu',
    'The Dadra And Nagar Haveli And Daman And Diu': 'Dadra And Nagar Haveli And Daman And Diu',
    'DADRA & NAGAR HAVELI & DAMAN & DIU': 'Dadra And Nagar Haveli And Daman And Diu',
    'GUJARAT and DNH & DD ISLANDS': 'Dadra And Nagar Haveli And Daman And Diu',
    'Delhi': 'Delhi',
    'DELHI': 'Delhi',
    'NCT of Delhi': 'Delhi',
    'Goa': 'Goa',
    'GOA': 'Goa',
    'Gujarat': 'Gujarat',
    'GUJARAT': 'Gujarat',
    'Haryana': 'Haryana',
    'HARYANA': 'Haryana',
    'Himachal Pradesh': 'Himachal Pradesh',
    'HIMACHAL PRADESH': 'Himachal Pradesh',
    'Jammu & Kashmir': 'Jammu And Kashmir',
    'Jammu and Kashmir': 'Jammu And Kashmir',
    'JAMMU AND KASHMIR': 'Jammu And Kashmir',
    'Jharkhand': 'Jharkhand',
    'JHARKHAND': 'Jharkhand',
    'Karnataka': 'Karnataka',
    'KARNATAKA': 'Karnataka',
    'Kerala': 'Kerala',
    'KERALA': 'Kerala',
    'Ladakh': 'Ladakh',
    'LADAKH': 'Ladakh',
    'Lakshadweep': 'Lakshadweep',
    'LAKSHADWEEP': 'Lakshadweep',
    'Madhya Pradesh': 'Madhya Pradesh',
    'MADHYA PRADESH': 'Madhya Pradesh',
    'Maharashtra': 'Maharashtra',
    'MAHARASHTRA': 'Maharashtra',
    'Manipur': 'Manipur',
    'MANIPUR': 'Manipur',
    'Meghalaya': 'Meghalaya',
    'MEGHALAYA': 'Meghalaya',
    'Mizoram': 'Mizoram',
    'MIZORAM': 'Mizoram',
    'Nagaland': 'Nagaland',
    'NAGALAND': 'Nagaland',
    'Odisha': 'Odisha',
    'ODISHA': 'Odisha',
    'Orissa': 'Odisha',
    'Puducherry': 'Puducherry',
    'PUDUCHERRY': 'Puducherry',
    'Pondicherry': 'Puducherry',
    'Punjab': 'Punjab',
    'PUNJAB': 'Punjab',
    'Rajasthan': 'Rajasthan',
    'RAJASTHAN': 'Rajasthan',
    'Sikkim': 'Sikkim',
    'SIKKIM': 'Sikkim',
    'Tamil Nadu': 'Tamil Nadu',
    'TAMIL NADU': 'Tamil Nadu',
    'Telangana': 'Telangana',
    'TELANGANA': 'Telangana',
    'Tripura': 'Tripura',
    'TRIPURA': 'Tripura',
    'Uttar Pradesh': 'Uttar Pradesh',
    'UTTAR PRADESH': 'Uttar Pradesh',
    'Uttarakhand': 'Uttarakhand',
    'UTTARAKHAND': 'Uttarakhand',
    'Uttaranchal': 'Uttarakhand',
    'West Bengal': 'West Bengal',
    'WEST BENGAL': 'West Bengal'
}

STATE_CODE_MAP = {
    'Uttar Pradesh': 'UP', 'Gujarat': 'GJ', 'Madhya Pradesh': 'MP', 'Bihar': 'BR',
    'Tamil Nadu': 'TN', 'West Bengal': 'WB', 'Odisha': 'OD', 'Jharkhand': 'JH',
    'Punjab': 'PB', 'Telangana': 'TS', 'Kerala': 'KL', 'Karnataka': 'KA',
    'Andhra Pradesh': 'AP', 'Rajasthan': 'RJ', 'Maharashtra': 'MH', 'Assam': 'AS',
    'Haryana': 'HR', 'Chhattisgarh': 'CG', 'Himachal Pradesh': 'HP', 'Uttarakhand': 'UK',
    'Jammu And Kashmir': 'JK', 'Delhi': 'DL', 'Goa': 'GA', 'Tripura': 'TR',
    'Meghalaya': 'ML', 'Manipur': 'MN', 'Nagaland': 'NL', 'Arunachal Pradesh': 'AR',
    'Mizoram': 'MZ', 'Sikkim': 'SK', 'Puducherry': 'PY', 'Chandigarh': 'CH',
    'Ladakh': 'LA', 'Andaman And Nicobar Islands': 'AN',
    'Dadra And Nagar Haveli And Daman And Diu': 'DN', 'Lakshadweep': 'LD'
}

def simplify_coords(coords, precision=4):
    """Recursively round coordinates to 4 decimal places (~11 meters) to reduce payload size while keeping crisp coastlines"""
    if isinstance(coords, (int, float)):
        return round(coords, precision)
    if isinstance(coords, list):
        return [simplify_coords(c, precision) for c in coords]
    return coords

def calc_centroid(coords):
    flat = []
    def extract_pts(c):
        if len(c) == 2 and isinstance(c[0], (int, float)) and isinstance(c[1], (int, float)):
            flat.append(c)
        else:
            for item in c:
                extract_pts(item)
    extract_pts(coords)
    if not flat:
        return [0, 0]
    avg_lng = sum(p[0] for p in flat) / len(flat)
    avg_lat = sum(p[1] for p in flat) / len(flat)
    return [round(avg_lat, 4), round(avg_lng, 4)] # lat, lng

# 2. Fetch Authoritative States GeoJSON (Survey of India 36 States/UTs)
states_url = 'https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson'
req_states = urllib.request.Request(states_url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req_states, timeout=30) as resp:
    raw_states = json.loads(resp.read().decode('utf-8'))

cleaned_states = []
seen_states = set()

for feat in raw_states.get('features', []):
    props = feat.get('properties', {})
    raw_name = props.get('ST_NM') or props.get('state_name') or props.get('NAME_1') or ''
    norm_name = STATE_NAME_MAP.get(raw_name.strip(), raw_name.strip())
    state_code = STATE_CODE_MAP.get(norm_name, norm_name[:2].upper())

    cleaned_feat = {
        'type': 'Feature',
        'properties': {
            'stateName': norm_name,
            'stateCode': state_code,
            'originalName': raw_name
        },
        'geometry': {
            'type': feat['geometry']['type'],
            'coordinates': simplify_coords(feat['geometry']['coordinates'], 4)
        }
    }
    cleaned_states.append(cleaned_feat)
    seen_states.add(norm_name)

output_states_path = 'frontend/src/data/india_states_geo.json'
with open(output_states_path, 'w', encoding='utf-8') as f:
    json.dump({
        'type': 'FeatureCollection',
        'features': cleaned_states
    }, f, separators=(',', ':'))

print(f"Generated {output_states_path}: {len(cleaned_states)} features across {len(seen_states)} states/UTs.")

# 3. Fetch Authoritative Districts GeoJSON
dist_url = 'https://raw.githubusercontent.com/datta07/INDIAN-SHAPEFILES/master/INDIA/INDIA_DISTRICTS.geojson'
req_dist = urllib.request.Request(dist_url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req_dist, timeout=35) as resp:
    raw_dist = json.loads(resp.read().decode('utf-8'))

cleaned_districts = []
districts_by_state = {}

for feat in raw_dist.get('features', []):
    props = feat.get('properties', {})
    raw_state = props.get('state') or props.get('stname') or props.get('NAME_1') or ''
    raw_dist_name = props.get('district') or props.get('dtname') or props.get('NAME_2') or ''
    
    norm_state = STATE_NAME_MAP.get(raw_state.strip(), raw_state.strip())
    dist_name = raw_dist_name.strip().title()
    state_code = STATE_CODE_MAP.get(norm_state, norm_state[:2].upper())

    centroid = calc_centroid(feat['geometry']['coordinates'])

    cleaned_feat = {
        'type': 'Feature',
        'properties': {
            'stateName': norm_state,
            'stateCode': state_code,
            'districtName': dist_name,
            'districtCode': str(props.get('dist_code') or props.get('dtcode11') or ''),
            'centroid': centroid
        },
        'geometry': {
            'type': feat['geometry']['type'],
            'coordinates': simplify_coords(feat['geometry']['coordinates'], 4)
        }
    }
    cleaned_districts.append(cleaned_feat)
    
    if state_code not in districts_by_state:
        districts_by_state[state_code] = {
            'type': 'FeatureCollection',
            'stateName': norm_state,
            'stateCode': state_code,
            'features': []
        }
    districts_by_state[state_code]['features'].append(cleaned_feat)

os.makedirs('frontend/public/data/districts', exist_ok=True)
for code, col in districts_by_state.items():
    p = f'frontend/public/data/districts/{code}.json'
    with open(p, 'w', encoding='utf-8') as out:
        json.dump(col, out, separators=(',', ':'))

print(f"Partitioned district GeoJSONs into frontend/public/data/districts/ across {len(districts_by_state)} states/UTs.")
