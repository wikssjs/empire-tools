#!/usr/bin/env python3
"""
pipeline_pseo.py - Generate fokuz.ca PSEO content for a service*ville pair
and POST to Strapi as a page-service-ville draft.

Usage:
    python pipeline_pseo.py --service toiture --ville laval
    python pipeline_pseo.py --service toiture --ville laval --force-refresh
    python pipeline_pseo.py --pilot laval   # genere les 5 services pilotes pour Laval
    python pipeline_pseo.py --dry-run --service toiture --ville laval
"""

import os
import sys
import json
import argparse
import hashlib
import time
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
from openai import OpenAI
import urllib.request
import urllib.error

load_dotenv(Path(__file__).parent / ".env", override=True)

# Models
NANO_MODEL = "gpt-5.4-nano"
MINI_MODEL = "gpt-5.4-mini"
HERO_MODEL = "gpt-5.4"
PPLX_MODEL = "sonar-pro"

HERO_PAIRS = {('toiture', 'laval')}

gpt  = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pplx = OpenAI(
    api_key=os.getenv("PERPLEXITY_API_KEY"),
    base_url="https://api.perplexity.ai"
)

STRAPI_URL   = os.getenv("STRAPI_URL", "http://localhost:1337")
STRAPI_TOKEN = os.getenv("STRAPI_TOKEN", "")

CACHE_DIR = Path(__file__).parent / "cache"

# Layout variants (anti-footprint)
LAYOUTS = {
    'A': ['intro', 'contexte_local', 'prix_section', 'processus_section', 'facteurs_locaux'],
    'B': ['intro', 'prix_section', 'contexte_local', 'processus_section', 'facteurs_locaux'],
    'C': ['intro', 'contexte_local', 'processus_section', 'prix_section', 'facteurs_locaux'],
}

def layout_for(service_slug: str, ville_slug: str) -> str:
    h = hashlib.md5(f"{service_slug}-{ville_slug}".encode()).hexdigest()
    return ['A', 'B', 'C'][int(h[0], 16) % 3]

# Cache helpers
def cache_path(kind: str, service: str, ville: str) -> Path:
    p = CACHE_DIR / kind
    p.mkdir(parents=True, exist_ok=True)
    return p / f"{service}-{ville}.json"

def load_cache(kind: str, service: str, ville: str):
    p = cache_path(kind, service, ville)
    if p.exists():
        return json.loads(p.read_text(encoding='utf-8'))
    return None

def save_cache(kind: str, service: str, ville: str, data: dict):
    p = cache_path(kind, service, ville)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

# Strapi helpers
def strapi_get(path: str) -> dict:
    url = f"{STRAPI_URL}/api/{path}"
    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {STRAPI_TOKEN}',
        'Content-Type': 'application/json',
    })
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read())

def strapi_post(path: str, data: dict) -> dict:
    url = f"{STRAPI_URL}/api/{path}"
    body = json.dumps({'data': data}).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers={
        'Authorization': f'Bearer {STRAPI_TOKEN}',
        'Content-Type': 'application/json',
    }, method='POST')
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"Strapi POST /api/{path} -> {e.code}: {body[:300]}")

def strapi_put(path: str, data: dict) -> dict:
    url = f"{STRAPI_URL}/api/{path}"
    body = json.dumps({'data': data}).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers={
        'Authorization': f'Bearer {STRAPI_TOKEN}',
        'Content-Type': 'application/json',
    }, method='PUT')
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"Strapi PUT /api/{path} -> {e.code}: {body[:300]}")

def get_service_data(slug: str) -> dict:
    res = strapi_get(f"services?filters[slug][$eq]={slug}&pagination[limit]=1")
    items = res.get('data', [])
    if not items:
        raise RuntimeError(f"Service '{slug}' not found in Strapi. Run seed first.")
    s = items[0]
    return {
        'id': s['id'],
        'nom': s['nom'],
        'slug': s['slug'],
        'nom_pluriel': s.get('nom_pluriel', s['nom']),
        'saisonnalite': s.get('saisonnalite', ''),
        'permis_requis': s.get('permis_requis_par_defaut', False),
        'prix_min': s.get('prix_indicatif_min'),
        'prix_max': s.get('prix_indicatif_max'),
        'unite_prix': s.get('unite_prix', 'par projet'),
    }

def get_ville_data(slug: str) -> dict:
    res = strapi_get(f"villes?filters[slug][$eq]={slug}&pagination[limit]=1&populate[0]=region&populate[1]=villes_voisines")
    items = res.get('data', [])
    if not items:
        raise RuntimeError(f"Ville '{slug}' not found in Strapi.")
    v = items[0]
    return {
        'id': v['id'],
        'nom': v['nom'],
        'slug': v['slug'],
        'population': v.get('population', 0),
        'quartiers': v.get('quartiers') or [],
        'region_nom': (v.get('region') or {}).get('nom', ''),
        'villes_voisines': [(vv.get('nom', '')) for vv in (v.get('villes_voisines') or [])],
    }

def find_existing_psv(service_slug: str, ville_slug: str):
    slug_complet = f"{service_slug}-{ville_slug}"
    res = strapi_get(f"page-service-villes?filters[slug_complet][$eq]={slug_complet}&pagination[limit]=1")
    items = res.get('data', [])
    return items[0] if items else None

# Phase 1: Research (Perplexity)
PERPLEXITY_PROMPTS = [
    "Quels sont les prix moyens pour {service} a {ville} (Quebec) en 2026 ? Inclure min/max/median selon le type de projet. Source des donnees.",
    "Quel est le climat de {ville} (Quebec) et son impact sur {service} residentiel ? Hivers, precipitations, gel-degel, particularites regionales.",
    "Quels permis municipaux sont requis a {ville} (Quebec) pour des travaux de {service} residentiel ? Source : site municipal officiel si possible.",
    "Quels types de {service} sont les plus courants dans le marche residentiel de {ville} et sa region au Quebec ? Materiaux, techniques, tendances.",
    "Quels organismes quebecois encadrent les entrepreneurs en {service} ? RBQ, CCQ, APCHQ, associations sectorielles pertinentes.",
]

def phase1_research(service_nom: str, ville_nom: str, force: bool, service_slug: str, ville_slug: str) -> list:
    cached = load_cache('perplexity', service_slug, ville_slug)
    if cached and not force:
        print(f"  [Phase 1] Cache hit -> {service_slug}-{ville_slug}.json")
        return cached

    print(f"  [Phase 1] Perplexity research ({len(PERPLEXITY_PROMPTS)} requetes)...")
    results = []
    for i, prompt_tpl in enumerate(PERPLEXITY_PROMPTS, 1):
        prompt = prompt_tpl.format(service=service_nom, ville=ville_nom)
        t0 = time.time()
        res = pplx.chat.completions.create(
            model="sonar-pro",
            messages=[
                {"role": "system", "content": "Tu es un assistant expert en renovation residentielle au Quebec. Reponds en francais, de facon precise et sourcee."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
        )
        text = res.choices[0].message.content
        results.append({'question': prompt, 'answer': text})
        print(f"    Q{i}/5 OK ({time.time()-t0:.1f}s)")

    save_cache('perplexity', service_slug, ville_slug, results)
    print(f"  [Phase 1] Sauvegarde -> cache/perplexity/{service_slug}-{ville_slug}.json")
    return results

# Phase 2: Extract (GPT-4o-mini -> structured JSON)
EXTRACT_SYSTEM = """Tu extrais des donnees structurees depuis des reponses de recherche.
Retourne UNIQUEMENT du JSON valide, sans markdown ni texte explicatif."""

def phase2_extract(research: list, service_nom: str, ville_nom: str) -> dict:
    combined = "\n\n".join([f"Q: {r['question']}\nA: {r['answer']}" for r in research])
    prompt = f"""Depuis ces recherches sur "{service_nom} a {ville_nom}", extrait:

{combined}

Retourne ce JSON exact:
{{
  "prix_min": <int ou null>,
  "prix_max": <int ou null>,
  "prix_median": <int ou null>,
  "unite": "<par projet/par pied carre/etc>",
  "materiaux_principaux": ["<materiau 1>", "<materiau 2>"],
  "permis_requis": <true/false/null>,
  "permis_details": "<details ou null>",
  "organismes": ["<organisme 1>"],
  "faits_climatiques": ["<fait 1>", "<fait 2>"],
  "types_courants": ["<type 1>", "<type 2>"]
}}"""

    res = gpt.chat.completions.create(
        model=NANO_MODEL,
        messages=[
            {"role": "system", "content": EXTRACT_SYSTEM},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    return json.loads(res.choices[0].message.content)

# Phase 3: Write content (GPT-5.4 Mini / Standard for hero)
WRITE_SYSTEM = """Tu es un expert en services residentiels au Quebec, redigeant pour fokuz.ca,
un comparateur de soumissions local. Tu ecris en francais quebecois, ton chaleureux et professionnel,
tutoiement. Public cible : proprietaires quebecois cherchant a comparer des entrepreneurs.

Regles absolues :
- Sentence case dans tous les titres (pas de majuscule a chaque mot)
- 1500-2000 mots total
- Pas de phrases bateau ("A l'ere du numerique...", "N'hesitez pas a...")
- Integre les donnees de prix de facon naturelle dans le texte
- Mentionne des quartiers et villes voisines specifiques
- Inclure 1 tableau Markdown (prix ou materiaux) dans la section prix
- Output : JSON structure avec les cles demandees"""

def phase3_write(service: dict, ville: dict, research: list, extracted: dict, layout: str, hero: bool = False) -> dict:
    voisines = ', '.join(ville['villes_voisines'][:3]) if ville['villes_voisines'] else 'les villes voisines'
    quartiers = ', '.join(ville['quartiers'][:5]) if ville['quartiers'] else ''
    combined_research = "\n\n---\n\n".join([f"Q: {r['question']}\n{r['answer']}" for r in research])

    prompt = f"""Genere le contenu PSEO pour :
Service : {service['nom']} ({service['nom_pluriel']})
Ville : {ville['nom']} ({ville['region_nom']})
Population : {ville['population']:,} hab.
Quartiers : {quartiers}
Villes voisines : {voisines}
Layout : {layout} (ordre sections: {' -> '.join(LAYOUTS[layout])})

Donnees extraites :
Prix min/max : {extracted.get('prix_min')}-{extracted.get('prix_max')} $ ({extracted.get('unite', service['unite_prix'])})
Materiaux : {', '.join(extracted.get('materiaux_principaux', []))}
Permis : {extracted.get('permis_requis')} - {extracted.get('permis_details', '')}
Organismes : {', '.join(extracted.get('organismes', []))}
Faits climatiques : {' | '.join(extracted.get('faits_climatiques', []))}
Types courants : {', '.join(extracted.get('types_courants', []))}

Recherche complete :
{combined_research[:6000]}

Retourne ce JSON exact (toutes les valeurs en Markdown/texte, PAS de HTML):
{{
  "titre_h1": "...",
  "meta_title": "...",
  "meta_description": "...",
  "intro": "...",
  "contexte_local": "...",
  "prix_section": "... (inclure tableau Markdown avec prix) ...",
  "processus_section": "...",
  "facteurs_locaux": "...",
  "tableau_prix": [
    {{"type": "...", "prix_min": 0, "prix_max": 0, "detail": "..."}}
  ]
}}"""

    model = HERO_MODEL if hero else MINI_MODEL
    label = "Standard (hero)" if hero else "Mini"
    print(f"  [Phase 3] Writing content (GPT-5.4 {label})...")
    res = gpt.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": WRITE_SYSTEM},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        max_completion_tokens=4096,
    )
    raw = res.choices[0].message.content.strip()
    start = raw.find('{')
    end = raw.rfind('}')
    if start != -1 and end != -1:
        raw = raw[start:end+1]
    return json.loads(raw)

# Phase 4: POST to Strapi
def markdown_to_blocks(text: str) -> list:
    if not text:
        return []
    blocks = []
    for para in text.split('\n\n'):
        para = para.strip()
        if not para:
            continue
        if para.startswith('## '):
            blocks.append({
                'type': 'heading',
                'level': 2,
                'children': [{'type': 'text', 'text': para[3:].strip()}]
            })
        elif para.startswith('### '):
            blocks.append({
                'type': 'heading',
                'level': 3,
                'children': [{'type': 'text', 'text': para[4:].strip()}]
            })
        elif para.startswith('| '):
            blocks.append({
                'type': 'paragraph',
                'children': [{'type': 'text', 'text': para}]
            })
        elif para.startswith('- ') or para.startswith('* '):
            items = [l.lstrip('- *').strip() for l in para.split('\n') if l.strip()]
            blocks.append({
                'type': 'list',
                'format': 'unordered',
                'children': [{'type': 'list-item', 'children': [{'type': 'text', 'text': item}]} for item in items]
            })
        else:
            blocks.append({
                'type': 'paragraph',
                'children': [{'type': 'text', 'text': para}]
            })
    return blocks

def phase4_strapi(content: dict, service: dict, ville: dict, research: list, extracted: dict, layout: str, dry_run: bool):
    slug_complet = f"{service['slug']}-{ville['slug']}"
    payload = {
        'slug_complet': slug_complet,
        'service': service['id'],
        'ville': ville['id'],
        'titre_h1': content['titre_h1'],
        'meta_title': content['meta_title'],
        'meta_description': content['meta_description'],
        'intro': markdown_to_blocks(content['intro']),
        'contexte_local': markdown_to_blocks(content['contexte_local']),
        'prix_section': markdown_to_blocks(content['prix_section']),
        'processus_section': markdown_to_blocks(content['processus_section']),
        'facteurs_locaux': markdown_to_blocks(content['facteurs_locaux']),
        'tableau_prix': content.get('tableau_prix', []),
        'sources_perplexity': research,
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'generated_by': 'mini',
        'layout_variant': layout,
    }

    if dry_run:
        print(f"  [Phase 4] DRY RUN - would POST to Strapi:")
        print(f"    slug_complet: {slug_complet}")
        print(f"    titre_h1: {content['titre_h1']}")
        print(f"    layout: {layout}")
        return None

    existing = find_existing_psv(service['slug'], ville['slug'])
    if existing:
        print(f"  [Phase 4] Updating existing entry (id: {existing['id']})...")
        res = strapi_put(f"page-service-villes/{existing['id']}", payload)
    else:
        print(f"  [Phase 4] Creating new entry in Strapi (draft)...")
        res = strapi_post('page-service-villes', payload)

    entry_id = res.get('data', {}).get('id', '?')
    print(f"  [Phase 4] Saved as draft (Strapi id: {entry_id})")
    return res

# Main orchestrator
PILOT_SERVICES = ['toiture', 'fenetres', 'thermopompe', 'pavage', 'drain']

def run_pair(service_slug: str, ville_slug: str, force: bool, dry_run: bool):
    print(f"\n{'='*60}")
    print(f"  {service_slug} x {ville_slug}")
    print(f"{'='*60}")
    t_start = time.time()

    print("  Fetching Strapi metadata...")
    service = get_service_data(service_slug)
    ville = get_ville_data(ville_slug)
    layout = layout_for(service_slug, ville_slug)
    hero = (service_slug, ville_slug) in HERO_PAIRS
    print(f"  Service: {service['nom']} | Ville: {ville['nom']} ({ville['region_nom']}) | Layout: {layout} | Hero: {hero}")

    research = phase1_research(service['nom'], ville['nom'], force, service_slug, ville_slug)

    print("  [Phase 2] Extracting structured data (GPT-5.4 Nano)...")
    extracted = phase2_extract(research, service['nom'], ville['nom'])
    print(f"    Prix: {extracted.get('prix_min')}-{extracted.get('prix_max')} $ | Permis: {extracted.get('permis_requis')}")

    cached_content = load_cache('generated', service_slug, ville_slug)
    if cached_content and not force:
        print(f"  [Phase 3] Cache hit -> using cached generated content")
        content = cached_content
    else:
        content = phase3_write(service, ville, research, extracted, layout, hero)
        save_cache('generated', service_slug, ville_slug, content)
        words = sum(len(v.split()) for v in content.values() if isinstance(v, str))
        print(f"    ~{words} mots | titre_h1: {content.get('titre_h1', '')[:60]}")

    phase4_strapi(content, service, ville, research, extracted, layout, dry_run)

    elapsed = time.time() - t_start
    print(f"\n  Done in {elapsed:.1f}s")

def main():
    parser = argparse.ArgumentParser(description='Generate fokuz.ca PSEO content for service x ville')
    parser.add_argument('--service', help='Service slug (e.g. toiture)')
    parser.add_argument('--ville', help='Ville slug (e.g. laval)')
    parser.add_argument('--pilot', metavar='VILLE', help='Run all 5 pilot services for a ville (e.g. --pilot laval)')
    parser.add_argument('--force-refresh', action='store_true', help='Ignore cache, re-fetch everything')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without calling Strapi')
    args = parser.parse_args()

    if not STRAPI_TOKEN:
        sys.exit("Set STRAPI_TOKEN in .env")

    missing = [k for k in ['OPENAI_API_KEY', 'PERPLEXITY_API_KEY'] if not os.getenv(k)]
    if missing:
        sys.exit(f"Missing env vars: {', '.join(missing)}")

    if args.pilot:
        print(f"\nPilot run: {len(PILOT_SERVICES)} services x {args.pilot}")
        for service_slug in PILOT_SERVICES:
            run_pair(service_slug, args.pilot, args.force_refresh, args.dry_run)
        print(f"\n{'='*60}")
        print(f"Pilot complete - {len(PILOT_SERVICES)} drafts in Strapi")
    elif args.service and args.ville:
        run_pair(args.service, args.ville, args.force_refresh, args.dry_run)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
