#!/usr/bin/env python3
"""
generate_city_content_douche.py — Génère city_content_douche.json via OpenAI API
Usage:
  python tools/generate_city_content_douche.py              # toutes les villes dediee
  python tools/generate_city_content_douche.py --limit 5   # test 5 villes
  python tools/generate_city_content_douche.py --resume     # reprendre après interruption
  python tools/generate_city_content_douche.py --city montreal

Requires: OPENAI_API_KEY env var (ou --key)
Output:   engine_qc/city_content_douche.json
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
CSV_PATH      = BASE / "engine_qc" / "MUN_douche_classified.csv"
CONTEXT_PATH  = BASE / "engine_qc" / "regional_context_douche.json"
RESEARCH_PATH = BASE / "engine_qc" / "niche_research_douche.json"
OUTPUT_PATH   = BASE / "engine_qc" / "city_content_douche.json"


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
    if not pool or len(pool) < n:
        return ""
    seed = int(hashlib.md5(slug.encode()).hexdigest(), 16)
    rng = random.Random(seed)
    selected = rng.sample(pool, n)
    return "\n".join(f"{i + 1}. {q}" for i, q in enumerate(selected))


def build_prompt(row: dict, ctx_text: str, prices: dict, template: str, faq_pool: list) -> str:
    ville        = row.get("munnom", "")
    slug         = row.get("slug", "")
    region       = row.get("regadm", "")
    mrc          = row.get("mrc", "")
    pop          = row.get("pop2021", "0") or "0"
    nb_prop      = row.get("nb_proprietaires", "")
    pct_prop     = row.get("pct_proprietaires", "")
    pct_uf       = row.get("pct_maisons_unifam", "")
    pct_vx       = row.get("pct_logements_vieux", "")
    rev_median   = row.get("revenu_median", "")
    val_median   = row.get("valeur_mediane_logement", "")

    mrc_clean = re.sub(r'\s*\(\d+\)$', '', mrc).strip()
    mrc_clean = re.sub(r'^MRC\s+', '', mrc_clean, flags=re.I)

    profil_parts = []
    if mrc_clean:
        profil_parts.append(f"MRC {mrc_clean}")
    if pct_prop:
        profil_parts.append(f"{pct_prop}% de propriétaires")
    if pct_uf:
        profil_parts.append(f"{pct_uf}% de maisons unifamiliales")
    if pct_vx:
        profil_parts.append(f"{pct_vx}% de logements construits avant 1981")
    if nb_prop:
        profil_parts.append(f"{nb_prop} propriétaires résidentiels")
    if rev_median:
        try:
            profil_parts.append(f"revenu médian {int(float(rev_median)):,}$".replace(",", " "))
        except ValueError:
            pass
    if val_median:
        try:
            profil_parts.append(f"valeur médiane des propriétés {int(float(val_median)):,}$".replace(",", " "))
        except ValueError:
            pass
    profil_local = ", ".join(profil_parts)

    faq_questions_raw = select_faq(slug, faq_pool)
    faq_questions = faq_questions_raw.replace("{ville}", ville)

    ctx_clean = re.sub(r'\n---PRIX---\n.*$', '', ctx_text, flags=re.DOTALL).strip()
    ctx_clean = re.sub(r'\[\d+\]', '', ctx_clean)
    ctx_clean = ctx_clean.replace('**', '')
    ctx_clean = re.sub(r'\\\(.*?\\\)', '', ctx_clean)

    return (
        template
        .replace("{ville}",        ville)
        .replace("{region}",       region)
        .replace("{population}",   pop)
        .replace("{profil_local}", profil_local)
        .replace("{faq_questions}", faq_questions)
        .replace("{context}",      ctx_clean)
        .replace("{service1_min}", str(prices.get("service1_min", 9500)))
        .replace("{service1_max}", str(prices.get("service1_max", 22000)))
        .replace("{service2_min}", str(prices.get("service2_min", 5200)))
        .replace("{service2_max}", str(prices.get("service2_max", 11500)))
        .replace("{service3_min}", str(prices.get("service3_min", 4000)))
        .replace("{service3_max}", str(prices.get("service3_max", 9500)))
        .replace("{service4_min}", str(prices.get("service4_min", 2500)))
        .replace("{service4_max}", str(prices.get("service4_max", 6800)))
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit",   type=int,  help="Limiter à N villes (test)")
    parser.add_argument("--resume",  action="store_true", help="Reprendre depuis save")
    parser.add_argument("--city",    default=None, help="Générer une seule ville (slug ou nom)")
    parser.add_argument("--model",   default="gpt-5.4-mini",
                        help="Modèle OpenAI (défaut: gpt-5.4-mini)")
    parser.add_argument("--workers", type=int, default=60,
                        help="Nombre de workers parallèles (défaut: 60)")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("ERROR: variable d'environnement OPENAI_API_KEY non définie")

    if not CONTEXT_PATH.exists():
        raise SystemExit(
            f"ERROR: {CONTEXT_PATH} introuvable.\n"
            f"Lance d'abord : python tools/fetch_regional_context.py --niche douche --csv engine_qc/MUN_douche_classified.csv"
        )

    client = OpenAI(api_key=api_key)

    rows          = read_csv(CSV_PATH)
    regional_ctx  = json.loads(CONTEXT_PATH.read_text(encoding="utf-8"))
    research      = json.loads(RESEARCH_PATH.read_text(encoding="utf-8"))
    system_prompt = research["system_prompt"]
    user_template = research["user_prompt_template"]
    price_tiers   = research.get("price_tiers", {})
    faq_pool      = research.get("faq_pool", [])

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

    if args.city:
        slug_or_nom = args.city.lower()
        rows = [r for r in rows if
                r.get("slug", "").lower() == slug_or_nom or
                r.get("munnom", "").lower() == slug_or_nom]
        if not rows:
            raise SystemExit(f"Ville non trouvée : {args.city}")

    if args.limit:
        rows = rows[:args.limit]

    if args.resume:
        rows = [r for r in rows if
                f"{r.get('slug', '')}|{r.get('region_slug', '')}" not in output]

    total      = len(rows)
    lock       = threading.Lock()
    done_count = 0
    err_count  = 0

    print(f"🏗️  {total} villes à générer — modèle : {args.model} — {args.workers} workers")
    print("-" * 60)

    def process(row):
        nonlocal done_count, err_count
        slug        = row.get("slug", "")
        region_slug = row.get("region_slug", "")
        ville       = row.get("munnom", "")
        region      = row.get("regadm", "")
        output_key  = f"{slug}|{region_slug}"

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
                output[output_key] = html
                done_count += 1
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
                output.setdefault(output_key, "")
                print(f"❌ [{slug}] {e}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        executor.map(process, rows)

    OUTPUT_PATH.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print("-" * 60)
    print(f"✅ Terminé — {done_count} générées, {err_count} erreurs")
    print(f"📁 {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
