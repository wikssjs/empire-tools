#!/usr/bin/env python3
"""
generate_city_content_foyer.py — Génère city_content_foyer.json via OpenAI API
Usage:
  python tools/generate_city_content_foyer.py              # toutes les 324 villes
  python tools/generate_city_content_foyer.py --limit 5   # test 5 villes
  python tools/generate_city_content_foyer.py --resume     # reprendre après interruption
  python tools/generate_city_content_foyer.py --city montreal

Requires: OPENAI_API_KEY env var (ou --key)
Output:   engine_qc/city_content_foyer.json
"""
import argparse
import concurrent.futures
import csv
import hashlib
import json
import os
import random
import re
import threading
import time
from pathlib import Path

from openai import OpenAI

BASE          = Path(__file__).parent.parent
CSV_PATH      = BASE / "engine_qc" / "MUN_foyer_classified.csv"
CONTEXT_PATH  = BASE / "engine_qc" / "regional_context_foyer.json"
RESEARCH_PATH = BASE / "engine_qc" / "niche_research_foyer.json"
OUTPUT_PATH   = BASE / "engine_qc" / "city_content_foyer.json"

# ---------------------------------------------------------------------------
# Réglementations municipales connues (sources vérifiables)
# ---------------------------------------------------------------------------
REGLEMENTATIONS_CONNUES = {
    "montréal": (
        "La Ville de Montréal interdit depuis 2018 l'utilisation d'appareils à bois "
        "non certifiés. Seuls les appareils émettant moins de 2,5 g/h de particules "
        "fines (certification EPA ou CSA B415.1) sont autorisés. Tout appareil non "
        "conforme doit être mis hors service ou remplacé."
    ),
    "laval": (
        "La Ville de Laval encadre le chauffage au bois via le règlement L-12792 : "
        "seuls les appareils certifiés EPA ou CSA B415.1 (seuil ≤ 2,5 g/h de particules) "
        "sont autorisés. Tout appareil de chauffage au bois doit être déclaré auprès "
        "de la Ville de Laval sous peine d'infraction."
    ),
    "québec": (
        "La Ville de Québec interdit depuis 2023 l'installation de nouveaux foyers "
        "d'ambiance au bois (foyers décoratifs non performants). Les poêles à bois "
        "et foyers encastrables certifiés EPA ou CSA B415.1 demeurent autorisés "
        "sous conditions d'installation conformes."
    ),
    "gatineau": (
        "La Ville de Gatineau encadre l'utilisation des appareils à bois : les appareils "
        "non certifiés sont limités et des restrictions d'usage s'appliquent lors des "
        "épisodes de mauvaise qualité de l'air. Les nouvelles installations doivent "
        "obligatoirement respecter les normes EPA ou CSA B415.1."
    ),
}

FALLBACK_REGLEMENTATION = (
    "Aucun règlement municipal spécifique au chauffage au bois n'a été identifié "
    "pour {ville}. Le cadre provincial s'applique : tout nouvel appareil doit être "
    "certifié EPA ou conforme à la norme CSA B415.1, installé selon les normes du "
    "Code de construction du Québec (dégagements réglementaires, conduits conformes). "
    "Le ramonage annuel est fortement recommandé et généralement exigé par les assureurs "
    "habitation. Consultez la Municipalité de {ville} ou votre MRC pour confirmer "
    "l'absence de règlement local spécifique."
)


def get_reglementation(ville: str) -> str:
    key = ville.lower().strip()
    return REGLEMENTATIONS_CONNUES.get(key, FALLBACK_REGLEMENTATION.replace("{ville}", ville))


# ---------------------------------------------------------------------------
# Parsing CSV
# ---------------------------------------------------------------------------
def read_csv(csv_path: Path) -> list:
    encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            with open(csv_path, encoding=enc) as f:
                reader = csv.DictReader(f)
                rows = []
                for row in reader:
                    clean = {k.lower().strip(): v.strip() for k, v in row.items()}
                    if clean.get("page_type", "").strip() == "dediee":
                        rows.append(clean)
            print(f"✅ CSV ({enc}) — {len(rows)} villes dediee")
            return rows
        except (UnicodeDecodeError, KeyError):
            continue
    raise RuntimeError(f"Impossible de lire : {csv_path}")


# ---------------------------------------------------------------------------
# Parsing prix depuis ---PRIX---
# ---------------------------------------------------------------------------
def parse_prices(context_text: str, fallback: dict) -> dict:
    match = re.search(r'---PRIX---\s*\n(\{[^\n]+\})', context_text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return fallback


def price_tier_key(pop: int) -> str:
    if pop >= 50000:
        return "grande_ville"
    elif pop >= 15000:
        return "moyenne_ville"
    elif pop >= 5000:
        return "petite_ville"
    return "village"


# ---------------------------------------------------------------------------
# Construction du prompt
# ---------------------------------------------------------------------------
def select_faq(slug: str, pool: list, n: int = 6) -> str:
    """Sélectionne n questions du pool de façon déterministe selon le slug."""
    if not pool or len(pool) < n:
        return ""
    seed = int(hashlib.md5(slug.encode()).hexdigest(), 16)
    rng = random.Random(seed)
    selected = rng.sample(pool, n)
    return "\n".join(f"{i + 1}. {q}" for i, q in enumerate(selected))


def build_prompt(row: dict, ctx_text: str, prices: dict, template: str, faq_pool: list) -> str:
    ville    = row.get("munnom", "")
    slug     = row.get("slug", "")
    region   = row.get("regadm", "")
    mrc      = row.get("mrc", "")
    pop      = row.get("pop2021", "0") or "0"
    nb_prop  = row.get("nb_proprietaires", "")
    pct_uf   = row.get("pct_maisons_unifam", "")
    pct_vx   = row.get("pct_logements_vieux", "")

    # Nettoyer le champ mrc : supprimer code interne "(780)" et préfixe "MRC " déjà présent
    mrc_clean = re.sub(r'\s*\(\d+\)$', '', mrc).strip()          # enlève (780)
    mrc_clean = re.sub(r'^MRC\s+', '', mrc_clean, flags=re.I)    # enlève "MRC " initial

    # Profil local explicite (forcer le modèle à l'utiliser)
    profil_parts = [f"MRC {mrc_clean}"]
    if pct_uf:
        profil_parts.append(f"{pct_uf}% de maisons unifamiliales")
    if pct_vx:
        profil_parts.append(f"{pct_vx}% de logements construits avant 1981")
    if nb_prop:
        profil_parts.append(f"{nb_prop} propriétaires résidentiels")
    profil_local = ", ".join(profil_parts)
    mrc = mrc_clean  # version nettoyée

    # FAQ déterministe par slug
    faq_questions_raw = select_faq(slug, faq_pool)
    faq_questions = faq_questions_raw.replace("{ville}", ville)

    # Nettoyer le contexte régional
    ctx_clean = re.sub(r'\n---PRIX---\n.*$', '', ctx_text, flags=re.DOTALL).strip()
    ctx_clean = re.sub(r'\[\d+\]', '', ctx_clean)          # refs [1][9]
    ctx_clean = ctx_clean.replace('**', '')                  # markdown gras
    ctx_clean = re.sub(r'\\\(.*?\\\)', '', ctx_clean)        # LaTeX \(-18\ ^\circ\)

    return (
        template
        .replace("{ville}",               ville)
        .replace("{region}",              region)
        .replace("{population}",          pop)
        .replace("{profil_local}",        profil_local)
        .replace("{faq_questions}",       faq_questions)
        .replace("{context}",             ctx_clean)
        .replace("{service1_min}",        str(prices.get("service1_min", 2700)))
        .replace("{service1_max}",        str(prices.get("service1_max", 6500)))
        .replace("{service2_min}",        str(prices.get("service2_min", 3800)))
        .replace("{service2_max}",        str(prices.get("service2_max", 9500)))
        .replace("{service3_min}",        str(prices.get("service3_min", 160)))
        .replace("{service3_max}",        str(prices.get("service3_max", 350)))
        .replace("{service4_min}",        str(prices.get("service4_min", 120)))
        .replace("{service4_max}",        str(prices.get("service4_max", 270)))
        .replace("{reglementation_bois}", get_reglementation(ville))
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit",  type=int,      help="Limiter à N villes (test)")
    parser.add_argument("--resume", action="store_true", help="Reprendre depuis save")
    parser.add_argument("--city",   default=None,  help="Générer une seule ville (slug ou nom)")
    parser.add_argument("--model",   default="gpt-5.4-mini",
                        help="Modèle OpenAI (défaut: gpt-5.4-mini)")
    parser.add_argument("--workers", type=int, default=60,
                        help="Nombre de workers parallèles (défaut: 60)")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("ERROR: variable d'environnement OPENAI_API_KEY non définie")

    client = OpenAI(api_key=api_key)

    # Chargement des données
    rows            = read_csv(CSV_PATH)
    regional_ctx    = json.loads(CONTEXT_PATH.read_text(encoding="utf-8"))
    research        = json.loads(RESEARCH_PATH.read_text(encoding="utf-8"))
    system_prompt   = research["system_prompt"]
    user_template   = research["user_prompt_template"]
    price_tiers     = research.get("price_tiers", {})
    faq_pool        = research.get("faq_pool", [])

    # Charger le fichier existant si présent (--resume ou --city)
    output = {}
    if OUTPUT_PATH.exists() and (args.resume or args.city):
        try:
            content = OUTPUT_PATH.read_text(encoding="utf-8").strip()
            if content:
                output = json.loads(content)
                print(f"📂 {len(output)} villes déjà dans le fichier")
            else:
                print("📂 Fichier existant vide — démarrage à zéro")
        except json.JSONDecodeError:
            print("⚠️  Fichier existant invalide — démarrage à zéro")

    # Filtre --city
    if args.city:
        slug_or_nom = args.city.lower()
        rows = [r for r in rows if
                r.get("slug", "").lower() == slug_or_nom or
                r.get("munnom", "").lower() == slug_or_nom]
        if not rows:
            raise SystemExit(f"Ville non trouvée : {args.city}")

    # Limiter
    if args.limit:
        rows = rows[:args.limit]

    # Filtrer les villes déjà faites si --resume
    if args.resume:
        rows = [r for r in rows if not output.get(r.get("slug", ""))]

    total      = len(rows)
    lock       = threading.Lock()
    done_count = 0
    err_count  = 0

    print(f"🏗️  {total} villes à générer — modèle : {args.model} — {args.workers} workers")
    print("-" * 60)

    def process(row):
        nonlocal done_count, err_count
        slug   = row.get("slug", "")
        ville  = row.get("munnom", "")
        region = row.get("regadm", "")

        ctx_text   = regional_ctx.get(region, "")
        pop        = int(row.get("pop2021", 0) or 0)
        fallback_p = price_tiers.get(price_tier_key(pop), {})
        prices     = parse_prices(ctx_text, fallback_p)
        prompt     = build_prompt(row, ctx_text, prices, user_template, faq_pool)

        try:
            response = client.chat.completions.create(
                model=args.model,
                max_completion_tokens=16000,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": prompt},
                ],
            )
            html = response.choices[0].message.content.strip()
            html = re.sub(r'^```html?\s*', '', html)
            html = re.sub(r'\s*```$', '', html).strip()

            with lock:
                output[slug] = html
                done_count  += 1
                n = done_count
                print(f"✅ [{n:3d}/{total}] {ville:<28} {len(html):,} chars")
                if n % 20 == 0:
                    OUTPUT_PATH.write_text(
                        json.dumps(output, ensure_ascii=False, indent=2),
                        encoding="utf-8"
                    )
                    print(f"  💾 Sauvegarde intermédiaire ({n}/{total})")

        except Exception as e:
            with lock:
                err_count += 1
                output.setdefault(slug, "")
                print(f"❌ [{slug}] {e}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        executor.map(process, rows)

    # Sauvegarde finale
    OUTPUT_PATH.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print("-" * 60)
    print(f"✅ Terminé — {done_count} générées, {err_count} erreurs")
    print(f"📁 {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
