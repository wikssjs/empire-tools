#!/usr/bin/env python3
"""
Compare Liste_des_projets CSV vs dashboard soumissionrenovation.ca (live fetch).
Trouve les leads du CSV absents du dashboard et les ecarts de montants.
Usage: python tools/compare_csv_vs_dashboard.py
"""
import csv, json, urllib.request, urllib.parse, re, os
from datetime import date

CSV_PATH     = 'Liste_des_projets_1781117948584.csv'
COMMISSION   = 0.40
BASE_URL     = 'https://client.soumissionrenovation.ca/fr/referrals_reporting'

# ── Session cookie (copier depuis navigateur : F12 → Network → cookie header) ─
# Ouvrir https://client.soumissionrenovation.ca, F12, onglet Network,
# cliquer n'importe quelle requete → Headers → Request Headers → cookie
COOKIE = os.environ.get('SR_COOKIE', '')

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
        'Cookie': COOKIE,
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
        if len(cells) >= 7:
            try:
                proj_id = int(cells[6]) if cells[6].isdigit() else None
                if not proj_id:
                    continue
                rev_str = cells[2].replace('$', '').replace(',', '').strip()
                rev = float(rev_str) if rev_str else 0.0
                result[proj_id] = {
                    'date':    cells[0][:10],
                    'service': cells[7] if len(cells) > 7 else '',
                    'revenu':  rev,
                    'region':  cells[11] if len(cells) > 11 else '',
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

    # ── Fetch dashboard ───────────────────────────────────────────────────────
    if not COOKIE:
        print('\n  [!] COOKIE manquant — utilise les donnees embarquees (voir note ci-dessous)')
        print('  Pour activer le fetch live: set SR_COOKIE="ton_cookie" avant de lancer')
        dashboard_data = {}
    else:
        print(f'  Fetching dashboard {date_min} -> {date_max}...')
        # Fetcher par blocs de 7 jours pour eviter la troncature
        from datetime import datetime, timedelta
        dashboard_data = {}
        d = datetime.strptime(date_min, '%Y-%m-%d')
        end_d = datetime.strptime(date_max, '%Y-%m-%d')
        while d <= end_d:
            chunk_end = min(d + timedelta(days=6), end_d)
            chunk = fetch_dashboard(
                d.strftime('%Y/%m/%d'),
                chunk_end.strftime('%Y/%m/%d')
            )
            dashboard_data.update(chunk)
            d = chunk_end + timedelta(days=1)
        print(f'  Dashboard: {len(dashboard_data)} projets fetches')

    # ── Donnees dashboard embedees (fallback si pas de cookie) ───────────────
    # Generees par WebFetch le 2026-06-08
    # Fetche le 2026-06-09 — montants mis a jour
    EMBEDDED_DASHBOARD = {
        # Juin 1
        1012145: {'date':'2026-06-01','service':'Revêtement extérieur','revenu':15.83,'region':'Lanaudière'},
        1012375: {'date':'2026-06-01','service':'Calfeutrage','revenu':70.10,'region':'Laurentides'},
        1012447: {'date':'2026-06-01','service':'Designer Intérieur','revenu':81.83,'region':'Pincourt'},
        1012507: {'date':'2026-06-01','service':'Gouttières','revenu':5.03,'region':'Saint-Hyacinthe Est'},
        1012653: {'date':'2026-06-01','service':'Électricien','revenu':15.19,'region':'Repentigny'},
        # Juin 2
        1013011: {'date':'2026-06-02','service':'Électricien','revenu':19.00,'region':'Saint-Didace'},
        1013055: {'date':'2026-06-02','service':'Peinture - Intérieur','revenu':38.83,'region':'Capitale-Nationale'},
        1013378: {'date':'2026-06-02','service':'Gouttières','revenu':72.30,'region':'Lanaudière'},
        # Juin 4
        1014598: {'date':'2026-06-04','service':'Isolation - Entre-toît','revenu':111.86,'region':'Québec'},
        1014603: {'date':'2026-06-04','service':'Climatisation','revenu':73.94,'region':'Saint-Donat'},
        1014827: {'date':'2026-06-04','service':'Gouttières','revenu':10.38,'region':'Estrie'},
        1015169: {'date':'2026-06-04','service':'Calfeutrage','revenu':18.00,'region':'Lanaudière'},
        # Juin 5
        1015674: {'date':'2026-06-05','service':'Fondation - Fissures','revenu':19.27,'region':'Montérégie'},
        # Juin 6
        1016028: {'date':'2026-06-06','service':'Gouttières','revenu':51.97,'region':'Laurentides'},
        1016067: {'date':'2026-06-06','service':'Aménagement Paysager - Pavage','revenu':37.45,'region':'Capitale-Nationale'},
        1016110: {'date':'2026-06-06','service':'Fondation - Fissures','revenu':77.84,'region':'Montérégie'},
        # Juin 7
        1016601: {'date':'2026-06-07','service':'Décontamination','revenu':25.10,'region':'Estrie'},
        # Juin 8
        1016873: {'date':'2026-06-08','service':'Calfeutrage','revenu':18.00,'region':'Saint-Jean-sur-Richelieu Est'},
        1017139: {'date':'2026-06-08','service':'Gouttières','revenu':10.98,'region':'Wotton'},
        1017162: {'date':'2026-06-08','service':'Gouttières','revenu':13.26,'region':'Sainte-Foy-Sillery-Cap-Rouge'},
    }

    if not dashboard_data:
        dashboard_data = EMBEDDED_DASHBOARD

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
