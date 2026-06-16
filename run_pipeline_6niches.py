#!/usr/bin/env python3
"""
run_pipeline_6niches.py — Pipeline complet pour les 6 nouvelles niches engine_qc.

Étapes par niche :
  1. fetch_regional_context.py  → engine_qc/regional_context_<niche>.json
  2. generate_city_content.py   → engine_qc/city_content_<niche>.json
  3. EmpireGenerator.py         → engine_qc/dist_<niche>/

Usage :
  # Toutes les niches, toutes les étapes
  python tools/run_pipeline_6niches.py

  # Une seule niche
  python tools/run_pipeline_6niches.py --niche paysagement

  # Reprendre generate (skip fetch déjà fait)
  python tools/run_pipeline_6niches.py --skip-fetch

  # Build seulement (fetch + generate déjà faits)
  python tools/run_pipeline_6niches.py --only-build

  # Tester generate sur 5 villes seulement
  python tools/run_pipeline_6niches.py --limit 5

IMPORTANT: Le push git est délibérément absent — vérifier dans le navigateur avant de pusher.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent  # Empire-PSEO/

NICHES = [
    {
        "niche":      "paysagement",
        "config":     "engine_qc/config_paysagement.json",
        "dist":       "dist_paysagement",
        "site":       "prix-paysagement.ca",
    },
    {
        "niche":      "electricien",
        "config":     "engine_qc/config_electricien.json",
        "dist":       "dist_electricien",
        "site":       "prix-electricien.ca",
    },
    {
        "niche":      "portes-fenetres",
        "config":     "engine_qc/config_portes-fenetres.json",
        "dist":       "dist_portes-fenetres",
        "site":       "experts-fenetres.ca",
    },
    {
        "niche":      "fosseseptique",
        "config":     "engine_qc/config_fosseseptique.json",
        "dist":       "dist_fosseseptique",
        "site":       "experts-fosseseptique.ca",
    },
    {
        "niche":      "nettoyage-conduits",
        "config":     "engine_qc/config_nettoyage-conduits.json",
        "dist":       "dist_nettoyage-conduits",
        "site":       "experts-conduits.ca",
    },
    {
        "niche":      "calfeutrage",
        "config":     "engine_qc/config_calfeutrage.json",
        "dist":       "dist_calfeutrage",
        "site":       "expertcalfeutrage.ca",
    },
]

DIVIDER = "=" * 70


def run(cmd, cwd=None, timeout=3600):
    """Run command, stream output, return True on success."""
    label = " ".join(str(c) for c in cmd)
    print(f"\n  $ {label}")
    start = time.time()
    proc = subprocess.run(
        cmd,
        cwd=str(cwd or ROOT),
        encoding="utf-8",
        errors="replace",
    )
    elapsed = time.time() - start
    ok = proc.returncode == 0
    status = "OK" if ok else f"FAIL (exit {proc.returncode})"
    print(f"  → {status}  [{elapsed:.0f}s]")
    return ok


def main():
    parser = argparse.ArgumentParser(description="Pipeline 6 niches engine_qc")
    parser.add_argument("--niche", default=None,
                        help="Niche unique à traiter (ex: paysagement)")
    parser.add_argument("--skip-fetch", action="store_true",
                        help="Sauter l'étape fetch_regional_context")
    parser.add_argument("--skip-generate", action="store_true",
                        help="Sauter l'étape generate_city_content")
    parser.add_argument("--only-build", action="store_true",
                        help="Build EmpireGenerator seulement (skip fetch + generate)")
    parser.add_argument("--limit", type=int, default=0,
                        help="Limiter generate à N villes (0 = toutes, pour tests)")
    parser.add_argument("--resume", action="store_true",
                        help="Passer --resume à generate_city_content (reprendre)")
    args = parser.parse_args()

    if args.only_build:
        args.skip_fetch = True
        args.skip_generate = True

    niches = NICHES
    if args.niche:
        niches = [n for n in NICHES if n["niche"] == args.niche]
        if not niches:
            print(f"ERROR: niche '{args.niche}' inconnue. Options: {[n['niche'] for n in NICHES]}")
            sys.exit(1)

    results = {}

    for entry in niches:
        niche   = entry["niche"]
        config  = entry["config"]
        site    = entry["site"]

        print(f"\n{DIVIDER}")
        print(f"  NICHE: {niche}  ({site})")
        print(DIVIDER)

        ok_fetch    = True
        ok_generate = True
        ok_build    = True

        # ── Étape 1 : fetch_regional_context ────────────────────────────────
        if not args.skip_fetch:
            context_file = ROOT / "engine_qc" / f"regional_context_{niche}.json"
            if context_file.exists():
                print(f"\n[1/3] fetch  — {context_file.name} EXISTE déjà, on skip.")
                print("      (Supprimez-le manuellement pour refetcher.)")
            else:
                print(f"\n[1/3] fetch_regional_context → regional_context_{niche}.json")
                ok_fetch = run([
                    sys.executable,
                    str(ROOT / "tools" / "fetch_regional_context.py"),
                    "--niche", niche,
                ], cwd=ROOT)
        else:
            print(f"\n[1/3] fetch  — SKIP (--skip-fetch)")

        if not ok_fetch:
            print(f"  ✗ fetch échoué pour {niche} — on skip generate + build")
            results[niche] = "FAIL-fetch"
            continue

        # ── Étape 2 : generate_city_content ─────────────────────────────────
        if not args.skip_generate:
            print(f"\n[2/3] generate_city_content → city_content_{niche}.json")
            gen_cmd = [
                sys.executable,
                str(ROOT / "tools" / "generate_city_content.py"),
                "--niche", niche,
                "--workers", "60",
            ]
            if args.resume:
                gen_cmd.append("--resume")
            if args.limit > 0:
                gen_cmd += ["--limit", str(args.limit)]
            ok_generate = run(gen_cmd, cwd=ROOT)
        else:
            print(f"\n[2/3] generate — SKIP (--skip-generate ou --only-build)")

        if not ok_generate:
            print(f"  ✗ generate échoué pour {niche} — on skip build")
            results[niche] = "FAIL-generate"
            continue

        # ── Étape 3 : EmpireGenerator build ─────────────────────────────────
        print(f"\n[3/3] EmpireGenerator → dist_{niche}/")
        ok_build = run([
            sys.executable,
            str(ROOT / "engine_qc" / "EmpireGenerator.py"),
            "--config", str(ROOT / config),
        ], cwd=ROOT)

        results[niche] = "OK" if ok_build else "FAIL-build"

    # ── Résumé final ─────────────────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("  RÉSUMÉ PIPELINE")
    print(DIVIDER)
    all_ok = True
    for niche, status in results.items():
        icon = "✅" if status == "OK" else "❌"
        entry = next(n for n in NICHES if n["niche"] == niche)
        print(f"  {icon}  {niche:<22}  {status:<15}  {entry['dist']}")
        if status != "OK":
            all_ok = False

    if all_ok:
        print(f"\n  Tout OK — vérifier dans le navigateur avant de pusher.")
        print(f"  Push manuel pour chaque niche :")
        for entry in niches:
            dist = ROOT / entry["dist"]
            print(f"    cd \"{dist}\" && git add -A && git commit -m \"city content\" && git push")
    else:
        print(f"\n  Des erreurs sont survenues — corriger avant de rebuild.")

    print()


if __name__ == "__main__":
    main()
