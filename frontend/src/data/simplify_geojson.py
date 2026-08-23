import json
import os

input_file = 'frontend/src/data/india_states_geo.json'
output_file = 'frontend/src/data/india_states_geo.json'

with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

def simplify_poly(pts, tolerance=0.015):
    """Simple radial distance point reduction for map rendering speed"""
    if not pts or len(pts) <= 4:
        return pts
    res = [pts[0]]
    for p in pts[1:-1]:
        dx = p[0] - res[-1][0]
        dy = p[1] - res[-1][1]
        if (dx*dx + dy*dy) > (tolerance * tolerance):
            res.append([round(p[0], 3), round(p[1], 3)])
    res.append([round(pts[-1][0], 3), round(pts[-1][1], 3)])
    return res

def process_geom(geom):
    gtype = geom['type']
    coords = geom['coordinates']
    if gtype == 'Polygon':
        new_coords = [simplify_poly(ring) for ring in coords]
        return {'type': gtype, 'coordinates': new_coords}
    elif gtype == 'MultiPolygon':
        new_coords = [[simplify_poly(ring) for ring in poly] for poly in coords]
        return {'type': gtype, 'coordinates': new_coords}
    return geom

for feat in data['features']:
    feat['geometry'] = process_geom(feat['geometry'])

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, separators=(',', ':'))

print(f"Simplified GeoJSON saved to {output_file}. New size: {os.path.getsize(output_file) / 1024 / 1024:.2f} MB")
