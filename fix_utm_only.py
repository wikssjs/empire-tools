#!/usr/bin/env python3
"""Set utm_campaign=jb in affiliate.base_url for all 8 QC V3 configs."""
import json, os, re

BASE = os.path.join(os.path.dirname(__file__), '..', 'engine_qc')

CONFIGS = [
    'config_cloture.json',
    'config_chauffage.json',
    'config_beton.json',
    'config_portes-fenetres.json',
    'config_agrandissement.json',
    'config_ceramique.json',
    'config_toiture-plate.json',
    'config_nettoyage-conduits.json',
]

for filename in CONFIGS:
    path = os.path.join(BASE, filename)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    aff = data.get('affiliate', {})
    url = aff.get('base_url', '')
    # Strip any existing utm params
    url = re.sub(r'&utm_\w+=[^&#]+', '', url)
    # Add utm_campaign=jb before fragment
    if '#' in url:
        base, frag = url.split('#', 1)
        url = f"{base}&utm_campaign=jb#{frag}"
    elif '?' in url:
        url = f"{url}&utm_campaign=jb"
    else:
        url = f"{url}?utm_campaign=jb"
    aff['base_url'] = url
    data['affiliate'] = aff
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'{filename}: ...{url[-50:]}')
