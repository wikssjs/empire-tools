#!/usr/bin/env python3
"""
batch_generate.py - Lance le pipeline PSEO pour plusieurs villes × services.

Usage:
    python batch_generate.py                    # Top villes, tous les services
    python batch_generate.py --dry-run          # Affiche les combos sans générer
    python batch_generate.py --ville montreal   # Tous les services pour une ville
    python batch_generate.py --service toiture  # Toutes les villes pour un service
    python batch_generate.py --tier 1           # Seulement les grandes villes (tier 1)
    python batch_generate.py --limit 10         # Max N pages (teste sans tout générer)
"""

import subprocess
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

# ─── Villes par tier (priorité décroissante) ──────────────────────────────────
VILLES = {
    1: [  # Grandes villes — fort trafic SEO
        'montreal',
        'quebec',
        'gatineau',
        'longueuil',
        'sherbrooke',
        'saguenay',
        'trois-rivieres',
        'levis',
    ],
    2: [  # Couronne de Montréal — fort volume rénovation résidentielle
        'terrebonne',
        'repentigny',
        'brossard',
        'saint-jerome',
        'blainville',
        'mirabel',
        'vaudreuil-dorion',
        'mascouche',
        'saint-eustache',
        'granby',
        'saint-jean-sur-richelieu',
        'saint-hyacinthe',
    ],
    3: [  # Villes moyennes
        'chateauguay',
        'chambly',
        'beloeil',
        'varennes',
        'sainte-julie',
        'candiac',
        'saint-constant',
        'la-prairie',
        'boisbriand',
        'saint-therese',
        'rosemere',
        'deux-montagnes',
        'saint-lazare',
        'sainte-marthe-sur-le-lac',
        'magog',
        'sorel-tracy',
        'joliette',
        'shawinigan',
    ],
    4: [  # Petites villes
        'saint-lin-laurentides',
        'prevost',
        'saint-colomban',
        'sainte-sophie',
        'saint-sauveur',
        'lachute',
        'bois-des-filion',
        'lorraine',
        'rawdon',
        'saint-amable',
        'sainte-catherine',
        'beauharnois',
        'coaticook',
        'mont-laurier',
        'rouyn-noranda',
        'rimouski',
        'riviere-du-loup',
        'thetford-mines',
        'saint-georges',
        'saint-augustin-de-desmaures',
        'saint-nicolas',
        'l-ancienne-lorette',
    ],
}

# Laval déjà générée — exclue du batch par défaut
DONE = {'laval'}

# Services dans l'ordre de priorité (ROI / trafic)
SERVICES = [
    'toiture',
    'thermopompe',
    'fenetres',
    'pavage',
    'drain',
    'revetement',
    'isolation',
    'peinture',
]

PIPELINE = Path(__file__).parent / 'pipeline_pseo.py'


def run_pair(service: str, ville: str, dry_run: bool) -> bool:
    """Lance le pipeline pour une paire service×ville. Retourne True si succès."""
    cmd = [sys.executable, str(PIPELINE), '--service', service, '--ville', ville]
    if dry_run:
        print(f'  [dry-run] {service} × {ville}')
        return True
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, encoding='utf-8')
        if result.returncode == 0:
            # Cherche la ligne de confirmation dans stdout
            for line in result.stdout.splitlines():
                if 'PSV' in line or 'id:' in line or '✓' in line or 'published' in line.lower():
                    print(f'  ✓ {service} × {ville} — {line.strip()}')
                    break
            else:
                print(f'  ✓ {service} × {ville}')
            return True
        else:
            err = result.stderr.splitlines()[-1] if result.stderr else 'unknown error'
            print(f'  ✗ {service} × {ville} — {err[:100]}')
            return False
    except subprocess.TimeoutExpired:
        print(f'  ✗ {service} × {ville} — TIMEOUT (>5 min)')
        return False
    except Exception as e:
        print(f'  ✗ {service} × {ville} — {e}')
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Affiche les combos sans générer')
    parser.add_argument('--ville', help='Génère tous les services pour cette ville seulement')
    parser.add_argument('--service', help='Génère toutes les villes pour ce service seulement')
    parser.add_argument('--tier', type=int, choices=[1, 2, 3, 4], help='Tier de villes seulement')
    parser.add_argument('--limit', type=int, help='Nombre max de pages à générer')
    parser.add_argument('--include-done', action='store_true', help='Inclut les villes déjà générées (ex: laval)')
    args = parser.parse_args()

    # Construire la liste de villes
    if args.ville:
        villes = [args.ville]
    elif args.tier:
        villes = VILLES[args.tier]
    else:
        villes = VILLES[1] + VILLES[2] + VILLES[3] + VILLES[4]

    if not args.include_done:
        villes = [v for v in villes if v not in DONE]

    services = [args.service] if args.service else SERVICES

    # Construire la liste complète des paires
    pairs = [(s, v) for v in villes for s in services]

    if args.limit:
        pairs = pairs[:args.limit]

    total = len(pairs)
    print(f'\n🚀 fokuz.ca batch PSEO — {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print(f'   {total} pages à générer ({len(services)} services × {len(villes)} villes)\n')

    if args.dry_run:
        for s, v in pairs:
            print(f'  [dry-run] {s} × {v}')
        print(f'\n→ {total} combos au total (aucune génération)')
        return

    ok = 0
    fail = 0
    start = time.time()

    for i, (service, ville) in enumerate(pairs, 1):
        print(f'\n[{i}/{total}] {service} × {ville}')
        success = run_pair(service, ville, dry_run=False)
        if success:
            ok += 1
        else:
            fail += 1
        # Petite pause pour ne pas saturer les APIs
        if i < total:
            time.sleep(2)

    elapsed = int(time.time() - start)
    mins, secs = divmod(elapsed, 60)
    print(f'\n{"─"*50}')
    print(f'✓ {ok} pages générées   ✗ {fail} erreurs   ⏱ {mins}m{secs:02d}s')
    print(f'{"─"*50}\n')


if __name__ == '__main__':
    main()
