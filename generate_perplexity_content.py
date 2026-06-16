#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
"""
generate_perplexity_content.py — Enrichit les grandes villes (>10k hab) avec des données
locales vérifiables sur la toiture via l'API Perplexity (permis, règlements, etc.)

Usage:
  python tools/generate_perplexity_content.py --niche prix-toiture
  python tools/generate_perplexity_content.py --niche prix-toiture --resume
  python tools/generate_perplexity_content.py --niche prix-toiture --limit 5

Requires: PERPLEXITY_API_KEY env var
Output:   Sites_relateds/city_perplexity_<niche>.json
"""

import argparse
import csv
import json
import os
import re
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT       = Path(__file__).parent.parent
SITES_DIR  = ROOT / "standalone_qc"
MIN_POP    = 10_000
MODEL      = "sonar-pro"

PROMPT_TEMPLATE = """\
Pour la ville de {VILLE}, Québec, trouve des données locales sur la toiture résidentielle.

Retourne un objet JSON valide avec exactement ces champs :
{{
  "permit_required": true/false/null,
  "permit_cost": "montant ou formule de calcul du permis, ou null",
  "municipal_rule": "règle municipale spécifique utile pour la toiture, ou null",
  "copy_short": "1-2 phrases factuelles en français sur la réglementation toiture à {VILLE}, ou null",
  "copy_html": "<p>Version de 2-3 phrases prête pour injection HTML, ou null</p>",
  "source_url": "URL de la source principale, ou null",
  "source_publisher": "nom de l'organisme source, ou null",
  "source_type": "official/municipal_proxy/third_party/none",
  "evidence_level": "official/semi-official/inferred/none"
}}

Règles :
- Priorité aux sources officielles : site municipal de {VILLE}, rbq.gouv.qc.ca, statcan.gc.ca
- source_type : "official" = site municipal ou gouvernemental direct | "municipal_proxy" = organisme quasi-officiel | "third_party" = site privé, contracteur, directory | "none" = aucune source
- Si une info n'est pas trouvable, retourne null pour CE champ uniquement
- Si permit_cost ou municipal_rule est trouvé, inclure l'info même si partielle
- Retourne UNIQUEMENT le JSON, sans texte ni markdown\
"""


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def load_cities(csv_path: Path, min_pop: int) -> list:
    cities = []
    encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            with open(csv_path, encoding=enc) as f:
                for row in csv.DictReader(f):
                    pop = int(row.get("mpopul", 0) or 0)
                    ville = row.get("munnom", "").strip()
                    region = row.get("regadm", "").strip()
                    if pop >= min_pop and ville:
                        cities.append({
                            "nom":    ville,
                            "slug":   slugify(ville),
                            "region": region,
                            "pop":    pop,
                        })
            break
        except (UnicodeDecodeError, KeyError):
            continue
    return sorted(cities, key=lambda x: -x["pop"])


def parse_json_response(text: str) -> dict:
    text = text.strip()
    # Strip markdown code fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text.strip())


def call_perplexity(client, ville: str) -> dict:
    from openai import OpenAI  # imported here so missing lib gives a clear error
    prompt = PROMPT_TEMPLATE.replace("{VILLE}", ville)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Tu es un assistant qui retourne uniquement du JSON valide. "
                    "Aucun texte explicatif, aucun markdown. Uniquement le JSON demandé."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )
    raw = response.choices[0].message.content
    return parse_json_response(raw)


def main():
    parser = argparse.ArgumentParser(description="Enrichit les grandes villes via Perplexity")
    parser.add_argument("--niche",    required=True, help="Niche slug (ex: prix-toiture)")
    parser.add_argument("--min-pop",  type=int, default=MIN_POP, help="Population minimale (défaut: 10000)")
    parser.add_argument("--workers",  type=int, default=3,       help="Workers parallèles (défaut: 3)")
    parser.add_argument("--resume",   action="store_true",        help="Reprendre une génération interrompue")
    parser.add_argument("--limit",    type=int, default=0,        help="Limiter à N villes (0 = toutes, pour test)")
    parser.add_argument("--output",   default=None,               help="Chemin de sortie JSON (optionnel)")
    parser.add_argument("--csv",      default=None,               help="Chemin vers MUN.csv (optionnel)")
    args = parser.parse_args()

    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        sys.exit("❌  Définir la variable d'environnement PERPLEXITY_API_KEY")

    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")

    csv_path = Path(args.csv) if args.csv else ROOT / "MUN.csv"
    if not csv_path.exists():
        sys.exit(f"❌  MUN.csv introuvable : {csv_path}")

    # Output path — par défaut dans Sites_relateds/ pour les scripts standalone
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = ROOT / "standalone_qc" / f"city_perplexity_{args.niche}.json"

    cities = load_cities(csv_path, args.min_pop)
    print(f"✓  {len(cities)} villes ≥ {args.min_pop:,} hab dans MUN.csv")

    # Resume
    existing: dict = {}
    if args.resume and output_path.exists():
        existing = json.loads(output_path.read_text(encoding="utf-8"))
        ok  = sum(1 for v in existing.values() if "error" not in v)
        err = sum(1 for v in existing.values() if "error" in v)
        print(f"   Reprise : {ok} OK, {err} erreurs — {len(existing)} entrées existantes")

    to_process = [c for c in cities if c["slug"] not in existing]
    if args.limit:
        to_process = to_process[: args.limit]
    print(f"→  {len(to_process)} villes à traiter\n")

    if not to_process:
        print("Rien à faire.")
        return

    results = dict(existing)
    lock = __import__("threading").Lock()

    def process(city):
        try:
            data = call_perplexity(client, city["nom"])
            data["_ville"] = city["nom"]
            data["_pop"]   = city["pop"]
            return city["slug"], data, None
        except Exception as e:
            return city["slug"], None, str(e)

    def save():
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    done_count = 0
    total = len(to_process)

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(process, c): c for c in to_process}
        for fut in as_completed(futures):
            slug, data, err = fut.result()
            done_count += 1
            with lock:
                if err:
                    print(f"[{done_count}/{total}] ✗  {slug}: {err}")
                    results[slug] = {"error": err, "_ville": futures[fut]["nom"]}
                else:
                    ev = data.get("evidence_level", "?")
                    has_copy = "✓" if data.get("short_copy") else "∅"
                    print(f"[{done_count}/{total}] {has_copy}  {slug} [{ev}]")
                    results[slug] = data
                save()

    ok  = sum(1 for v in results.values() if "error" not in v)
    err = sum(1 for v in results.values() if "error" in v)
    print(f"\n✓  Terminé — {ok} succès, {err} erreurs")
    print(f"   Fichier : {output_path}")


if __name__ == "__main__":
    main()
