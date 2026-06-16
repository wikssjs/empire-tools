#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
"""
migrate_city_content_keys.py
Migre city_content_{niche}.json de cles {slug} vers {slug}|{region_slug}.
Usage: python tools/migrate_city_content_keys.py --niche couvreur
"""
import argparse, csv, json, re, unicodedata
from pathlib import Path


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--niche", required=True)
    parser.add_argument("--csv", default=None)
    args = parser.parse_args()

    base = Path(__file__).parent.parent
    csv_path = Path(args.csv) if args.csv else base / "MUN.csv"
    content_path = base / "engine_qc" / f"city_content_{args.niche}.json"

    # Charge le contenu existant
    existing = json.loads(content_path.read_text(encoding="utf-8"))
    print(f"Entrées existantes : {len(existing)}")

    # Construit slug → première région rencontrée dans le CSV
    slug_to_region = {}
    encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            with open(csv_path, encoding=enc) as f:
                for row in csv.DictReader(f):
                    ville = row.get("munnom", "").strip()
                    region = row.get("regadm", "").strip()
                    if ville and region:
                        s = slugify(ville)
                        if s not in slug_to_region:
                            slug_to_region[s] = slugify(region)
            break
        except (UnicodeDecodeError, KeyError):
            continue

    # Migration
    migrated = {}
    skipped = 0
    for slug, content in existing.items():
        if "|" in slug:
            # Déjà migré
            migrated[slug] = content
            continue
        region_slug = slug_to_region.get(slug)
        if not region_slug:
            print(f"  WARN: slug '{slug}' introuvable dans MUN.csv — conservé tel quel")
            migrated[slug] = content
            skipped += 1
            continue
        new_key = f"{slug}|{region_slug}"
        migrated[new_key] = content

    content_path.write_text(json.dumps(migrated, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Migration terminee : {len(migrated)} entrees -> {content_path}")
    if skipped:
        print(f"  {skipped} slugs non trouves dans CSV (conserves tels quels)")
    print(f"  Nouvelles entrees a generer : ~{1283 - len(migrated)}")


if __name__ == "__main__":
    main()
