#!/usr/bin/env python3
"""
Compare Liste_des_projets CSV vs dashboard soumissionrenovation.ca (live fetch).
Trouve les leads du CSV absents du dashboard et les ecarts de montants.
Usage: python tools/compare_csv_vs_dashboard.py
"""
import csv, json, urllib.request, urllib.parse, re, os
from datetime import date

CSV_PATH     = 'Liste_des_projets_1782340049268.csv'
COMMISSION   = 0.40
BASE_URL     = 'https://client.soumissionrenovation.ca/fr/referrals_reporting'

NICHE_MAP = {
    'Toiture - Non-métallique (ex-Bardeaux)': 'toiture',
    'Toiture - Non-métallique (ex-Bardeaux) ': 'toiture',
    'Toiture - Toit plat':     'toiture_plate',
    'Toiture - Tôle':          'toiture',
    'Gouttières':               'gouttieres',
    'Fondation - Fissures':    'fissure',
    'Fondation - Complet':     'fissure',
    'Fondation - Imperméabilisation': 'fissure',
    'Thermopompe':              'thermopompe',
    'Climatisation':            'thermopompe',
    'Fenêtres':                 'fenetres',
    'Portes & Fenêtres  - Fournir et installer': 'fenetres',
    'Portes & Fenêtres - Fournir et installer':  'fenetres',
    'Portes & Fenêtres - Fournir seulement':     'fenetres',
    'Isolation':                'isolation',
    'Isolation - Entre-toît ':  'isolation',
    'Peinture - Intérieur':     'peinture',
    'Peinture - Extérieur':     'peinture',
    'Aménagement Paysager - Pavage':    'pavage',
    'Aménagement Paysager - Pavé-uni':  'pavage',
    'Électricien':              'electricien',
    'Aménagement Paysager - Excavation':'excavation',
    'Décontamination':          'decontamination',
    'Ébénisterie (cuisine)':    'cuisine',
    'Rénovations - Cuisine (avec électricité / plomberie)': 'cuisine',
    'Rénovations - Salle de bain (avec électricité / plomberie)': 'salledebain',
    'Revêtement extérieur':     'revetement',
    'Drain Français':           'drain',
    'Calfeutrage':              'calfeutrage',
    'Fosse septique - Entretien':   'fosseseptique',
    'Fosse septique - Installation':'fosseseptique',
    'Clôture':                  'cloture',
    'Agrandissement de maison': 'agrandissement',
    'Déménagement':             'demenagement',
    'Aménagement Paysager - Émondeur':'emondage',
    'Plancher':                 'plancher',
    'Porte de garage':          'porte_garage',
    'Maçonnerie':               'maconnerie',
    'Béton - Escalier/Dalle':   'beton',
    'Céramique':                'ceramique',
    'Extermination':            'extermination',
    'Chauffage':                'chauffage',
    'Nettoyage conduit aération / climatiseur': 'autres',
    'Soffites/Fascias':         'autres',
    'Designer Intérieur':       'autres',
    'Balcons - Bois':           'autres',
    'Aménagement paysager - Entretien Paysager': 'autres',
    'Patio - Au sol':           'autres',
}


def fetch_dashboard(start: str, end: str) -> dict:
    """Fetch dashboard for date range, returns {projet_id: {service, revenu, date, region}}"""
    params = urllib.parse.urlencode({
        'source': 'jb', 'report': 'yes',
        'start_date': start, 'end_date': end
    })
    url = f'{BASE_URL}?{params}'
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'text/html',
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f'  [WARN] Fetch {start}: {e}')
        return {}

    # Parse table rows — format: <td>valeur</td>
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)
    result = {}
    for row in rows:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
        cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
        if len(cells) >= 12:
            try:
                proj_id = int(cells[1]) if cells[1].isdigit() else None
                if not proj_id:
                    continue
                rev_str = cells[7].replace('$', '').replace(',', '.').replace('\xa0', '').strip()
                rev = float(rev_str) if rev_str else 0.0
                result[proj_id] = {
                    'date':    cells[0][:10],
                    'service': cells[11],
                    'revenu':  rev,
                    'region':  cells[5],
                }
            except (ValueError, IndexError):
                continue
    return result


def read_csv() -> dict:
    """Read CSV, returns {projet_id: {service, revenu, date, region}}"""
    result = {}
    with open(CSV_PATH, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        date_col, rev_col, proj_col, service_col, region_col = cols[0], cols[2], cols[6], cols[7], cols[11]
        for row in reader:
            try:
                pid = int(row[proj_col])
                rev_str = row[rev_col].strip()
                rev = float(rev_str) if rev_str else 0.0
                result[pid] = {
                    'date':    row[date_col][:10],
                    'service': row[service_col].strip(),
                    'revenu':  rev,
                    'region':  row[region_col],
                }
            except (ValueError, KeyError):
                continue
    return result


def main():
    # ── Lire le CSV ───────────────────────────────────────────────────────────
    csv_data = read_csv()
    csv_dates = sorted(set(v['date'] for v in csv_data.values()))
    date_min, date_max = csv_dates[0], csv_dates[-1]

    # Inclure aujourd'hui si pas dans le CSV
    today = str(date.today())
    if today > date_max:
        date_max = today

    print(f'\n{"="*90}')
    print(f'  COMPARAISON CSV vs DASHBOARD — {date_min} -> {date_max}')
    print(f'{"="*90}')
    print(f'  CSV: {len(csv_data)} projets total')

    # ── Fetch dashboard jour par jour ────────────────────────────────────────
    from datetime import datetime, timedelta
    dashboard_data = {}
    d = datetime.strptime(date_min, '%Y-%m-%d')
    end_d = datetime.strptime('2026-06-24', '%Y-%m-%d')
    while d <= end_d:
        day_str = d.strftime('%Y-%m-%d')
        chunk = fetch_dashboard(d.strftime('%Y/%m/%d'), d.strftime('%Y/%m/%d'))
        if chunk:
            print(f'  {day_str}: {len(chunk)} projets')
        dashboard_data.update(chunk)
        d += timedelta(days=1)
    print(f'  Dashboard total: {len(dashboard_data)} projets fetches')

    # ── Comparaison ───────────────────────────────────────────────────────────
    csv_ids   = set(csv_data.keys())
    dash_ids  = set(dashboard_data.keys())

    # Ce qui est dans CSV avec revenu > 0 mais absent du dashboard
    only_in_csv = []
    for pid in csv_ids:
        if pid not in dash_ids and csv_data[pid]['revenu'] > 0:
            only_in_csv.append(pid)

    # Ce qui est dans dashboard avec revenu > 0 mais absent du CSV
    only_in_dash = []
    for pid in dash_ids:
        if pid not in csv_ids and dashboard_data[pid]['revenu'] > 0:
            only_in_dash.append(pid)

    # Ecarts de montants (meme projet ID, revenu different)
    discrepancies = []
    for pid in csv_ids & dash_ids:
        csv_rev  = csv_data[pid]['revenu']
        dash_rev = dashboard_data[pid]['revenu']
        if abs(csv_rev - dash_rev) > 0.05:
            discrepancies.append((pid, csv_rev, dash_rev))

    # ── Affichage ─────────────────────────────────────────────────────────────
    total_csv  = sum(v['revenu'] for v in csv_data.values())
    total_dash = sum(v['revenu'] for v in dashboard_data.values())

    print(f'\n  Total revenu CSV      : ${total_csv:>8.2f}  (commission: ${total_csv*COMMISSION:.2f})')
    print(f'  Total revenu Dashboard: ${total_dash:>8.2f}  (commission: ${total_dash*COMMISSION:.2f})')
    print(f'  Difference            : ${total_csv - total_dash:>8.2f}  (commission: ${(total_csv-total_dash)*COMMISSION:.2f})')

    if only_in_csv:
        total_unique = sum(csv_data[p]['revenu'] for p in only_in_csv)
        print(f'\n{"="*90}')
        print(f'  DANS CSV SEULEMENT ({len(only_in_csv)} projets — ${total_unique:.2f})')
        print(f'{"="*90}')
        print(f'  {"ID":>9}  {"Date":>10}  {"Service":<40}  {"Revenu":>8}  {"Comm":>7}  Region')
        print(f'  {"-"*85}')
        for pid in sorted(only_in_csv, key=lambda p: csv_data[p]['date']):
            r = csv_data[pid]
            niche = NICHE_MAP.get(r['service'], 'autres')
            print(f'  {pid:>9}  {r["date"]:>10}  {r["service"]:<40}  ${r["revenu"]:>7.2f}  ${r["revenu"]*COMMISSION:>6.2f}  {r["region"]}')
        print(f'  {"-"*85}')
        print(f'  {"TOTAL":<55}  ${total_unique:>7.2f}  ${total_unique*COMMISSION:>6.2f}')

    if only_in_dash:
        total_unique_d = sum(dashboard_data[p]['revenu'] for p in only_in_dash)
        print(f'\n{"="*90}')
        print(f'  DANS DASHBOARD SEULEMENT ({len(only_in_dash)} projets — ${total_unique_d:.2f})')
        print(f'{"="*90}')
        for pid in sorted(only_in_dash, key=lambda p: dashboard_data[p]['date']):
            r = dashboard_data[pid]
            print(f'  {pid:>9}  {r["date"]:>10}  {r["service"]:<40}  ${r["revenu"]:>7.2f}')

    if discrepancies:
        print(f'\n{"="*90}')
        print(f'  ECARTS DE MONTANT ({len(discrepancies)} projets)')
        print(f'{"="*90}')
        print(f'  {"ID":>9}  {"Date":>10}  {"Service":<40}  {"CSV":>8}  {"Dashboard":>10}  {"Diff":>8}')
        print(f'  {"-"*90}')
        for pid, csv_r, dash_r in sorted(discrepancies):
            r = csv_data[pid]
            print(f'  {pid:>9}  {r["date"]:>10}  {r["service"]:<40}  ${csv_r:>7.2f}  ${dash_r:>9.2f}  ${dash_r-csv_r:>7.2f}')

    # ── Par niche (CSV uniquement) ────────────────────────────────────────────
    print(f'\n{"="*90}')
    print(f'  TOTAL CSV PAR NICHE (tous projets avec revenu)')
    print(f'{"="*90}')
    by_niche = {}
    for pid, r in csv_data.items():
        if r['revenu'] > 0:
            niche = NICHE_MAP.get(r['service'], 'autres')
            by_niche.setdefault(niche, {'rev': 0, 'count': 0})
            by_niche[niche]['rev']   += r['revenu']
            by_niche[niche]['count'] += 1
    print(f'  {"Niche":<25}  {"Leads":>6}  {"Revenu":>9}  {"Commission":>11}')
    print(f'  {"-"*55}')
    for niche, d in sorted(by_niche.items(), key=lambda x: -x[1]['rev']):
        print(f'  {niche:<25}  {d["count"]:>6}  ${d["rev"]:>8.2f}  ${d["rev"]*COMMISSION:>10.2f}')
    print(f'  {"-"*55}')
    print(f'  {"TOTAL":<25}  {sum(d["count"] for d in by_niche.values()):>6}  ${total_csv:>8.2f}  ${total_csv*COMMISSION:>10.2f}')
    print(f'{"="*90}')


if __name__ == '__main__':
    main()
