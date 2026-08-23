import json
import os

input_path = 'frontend/src/data/india_states.geojson'
output_path = 'frontend/src/data/india_states_geo.json'

if not os.path.exists(input_path):
    print("Input GeoJSON not found, fetching...")
    import requests
    url = 'https://raw.githubusercontent.com/Subhash9325/GeoJson-Data-of-Indian-States/master/Indian_States'
    r = requests.get(url, timeout=30)
    with open(input_path, 'w', encoding='utf-8') as f:
        f.write(r.text)

with open(input_path, 'r', encoding='utf-8') as f:
    geojson_data = json.load(f)

# Name normalization map
NAME_MAP = {
    'Andaman & Nicobar Island': 'Andaman And Nicobar Islands',
    'Andaman & Nicobar Islands': 'Andaman And Nicobar Islands',
    'Andaman and Nicobar Islands': 'Andaman And Nicobar Islands',
    'Andhra Pradesh': 'Andhra Pradesh',
    'Arunanchal Pradesh': 'Arunachal Pradesh',
    'Arunachal Pradesh': 'Arunachal Pradesh',
    'Assam': 'Assam',
    'Bihar': 'Bihar',
    'Chandigarh': 'Chandigarh',
    'Chhattisgarh': 'Chhattisgarh',
    'Dadara & Nagar Havelli': 'Dadra And Nagar Haveli And Daman And Diu',
    'Dadra and Nagar Haveli and Daman and Diu': 'Dadra And Nagar Haveli And Daman And Diu',
    'Daman & Diu': 'Dadra And Nagar Haveli And Daman And Diu',
    'NCT of Delhi': 'Delhi',
    'Delhi': 'Delhi',
    'Goa': 'Goa',
    'Gujarat': 'Gujarat',
    'Haryana': 'Haryana',
    'Himachal Pradesh': 'Himachal Pradesh',
    'Jammu & Kashmir': 'Jammu And Kashmir',
    'Jammu and Kashmir': 'Jammu And Kashmir',
    'Jharkhand': 'Jharkhand',
    'Karnataka': 'Karnataka',
    'Kerala': 'Kerala',
    'Lakshadweep': 'Lakshadweep',
    'Madhya Pradesh': 'Madhya Pradesh',
    'Maharashtra': 'Maharashtra',
    'Manipur': 'Manipur',
    'Meghalaya': 'Meghalaya',
    'Mizoram': 'Mizoram',
    'Nagaland': 'Nagaland',
    'Odisha': 'Odisha',
    'Orissa': 'Odisha',
    'Puducherry': 'Puducherry',
    'Pondicherry': 'Puducherry',
    'Punjab': 'Punjab',
    'Rajasthan': 'Rajasthan',
    'Sikkim': 'Sikkim',
    'Tamil Nadu': 'Tamil Nadu',
    'Telangana': 'Telangana',
    'Tripura': 'Tripura',
    'Uttar Pradesh': 'Uttar Pradesh',
    'Uttarakhand': 'Uttarakhand',
    'Uttaranchal': 'Uttarakhand',
    'West Bengal': 'West Bengal',
    'Ladakh': 'Ladakh'
}

def simplify_coords(coords, precision=4):
    """Recursively round coordinates to 4 decimal places (~11 meters) to reduce size by 70% while keeping exact shape"""
    if isinstance(coords, (int, float)):
        return round(coords, precision)
    if isinstance(coords, list):
        return [simplify_coords(c, precision) for c in coords]
    return coords

cleaned_features = []
seen_states = set()

for feat in geojson_data.get('features', []):
    props = feat.get('properties', {})
    raw_name = props.get('NAME_1') or props.get('ST_NM') or props.get('st_nm') or props.get('State_Name') or props.get('NAME') or props.get('state_name') or list(props.values())[0]
    
    norm_name = NAME_MAP.get(raw_name, raw_name)
    
    # Clean properties
    new_props = {
        'stateName': norm_name,
        'originalName': raw_name
    }
    
    # Simplify geometry coordinates
    geom = feat.get('geometry', {})
    new_geom = {
        'type': geom.get('type'),
        'coordinates': simplify_coords(geom.get('coordinates', []))
    }
    
    cleaned_features.append({
        'type': 'Feature',
        'properties': new_props,
        'geometry': new_geom
    })
    seen_states.add(norm_name)

cleaned_geojson = {
    'type': 'FeatureCollection',
    'features': cleaned_features
}

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(cleaned_geojson, f)

print(f"Generated clean GeoJSON with {len(cleaned_features)} features across {len(seen_states)} states/UTs.")
print(f"File saved to {output_path} (Size: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB)")
