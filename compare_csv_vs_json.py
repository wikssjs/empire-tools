#!/usr/bin/env python3
"""
Compare Liste_des_projets CSV vs leads_revenue_2026.json
Trouve les leads du CSV absents de notre JSON et calcule la difference de revenu.
Usage: python tools/compare_csv_vs_json.py
"""
import csv, json, os

CSV_PATH  = 'Liste_des_projets_1780973986207.csv'
JSON_PATH = 'leads_revenue_2026.json'

NICHE_MAP = {
    'Toiture - Non-métallique (ex-Bardeaux)': 'toiture',
    'Toiture - Non-métallique (ex-Bardeaux) ': 'toiture',
    'Toiture - Toit plat':    'toiture_plate',
    'Toiture - Tôle':         'toiture',
    'Gouttières':              'gouttieres',
    'Fondation - Fissures':   'fissure',
    'Fondation - Complet':    'fissure',
    'Thermopompe':             'thermopompe',
    'Climatisation':           'thermopompe',
    'Fenêtres':                'fenetres',
    'Portes & Fenêtres  - Fournir et installer': 'fenetres',
    'Portes & Fenêtres - Fournir et installer':  'fenetres',
    'Isolation':               'isolation',
    'Peinture':                'peinture',
    'Pavage':                  'pavage',
    'Aménagement Paysager - Pavage': 'pavage',
    'Électricien':             'electricien',
    'Excavation':              'excavation',
    'Décontamination':         'decontamination',
    'Ébénisterie (cuisine)':   'cuisine',
    'Rénovations - Salle de bain (avec électricité / plomberie)': 'salledebain',
    'Salle de bain':           'salledebain',
    'Revêtement extérieur':    'revetement',
    'Drain':                   'drain',
    'Calfeutrage':             'calfeutrage',
    'Fosse septique':          'fosseseptique',
    'Clôture':                 'cloture',
    'Agrandissement de maison':'agrandissement',
    'Déménagement':            'demenagement',
    'Émondage':                'emondage',
    'Plancher':                'plancher',
    'Porte de garage':         'porte_garage',
    'Maçonnerie':              'maconnerie',
    'Béton':                   'beton',
    'Céramique':               'ceramique',
    'Extermination':           'extermination',
    'Chauffage':               'chauffage',
    'Nettoyage conduit aération / climatiseur': 'autres',
    'Soffites/Fascias':        'autres',
}

COMMISSION = 0.40

# ── Lire le CSV ───────────────────────────────────────────────────────────────
csv_rows = []
with open(CSV_PATH, encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    cols = reader.fieldnames
    date_col    = cols[0]   # 'Date reçu'
    rev_col     = cols[2]   # 'Revenu'
    proj_col    = cols[6]   # 'Projet ID'
    service_col = cols[7]   # 'Service'
    region_col  = cols[11]  # 'Région'
    for row in reader:
        csv_rows.append(row)

# Garder seulement les lignes avec revenu
csv_with_rev = []
for r in csv_rows:
    rev_str = r[rev_col].strip()
    if rev_str:
        try:
            rev = float(rev_str)
            month = r[date_col][:7]  # 'YYYY-MM'
            niche = NICHE_MAP.get(r[service_col].strip(), 'autres')
            csv_with_rev.append({
                'projet_id': r[proj_col],
                'date':      r[date_col],
                'month':     month,
                'service':   r[service_col].strip(),
                'niche':     niche,
                'revenu':    rev,
                'commission': round(rev * COMMISSION, 2),
                'region':    r[region_col],
            })
        except ValueError:
            pass

# ── Lire le JSON ──────────────────────────────────────────────────────────────
with open(JSON_PATH, encoding='utf-8') as f:
    json_data = json.load(f)

# Projet IDs dans le JSON (analyse_leads.py les embed en dur)
# Puisque le JSON est agrégé (pas d'IDs), on compare par mois+niche+revenu
# On reconstruit les transactions connues par mois/niche
json_by_month = {}
for month, mdata in json_data['by_month'].items():
    json_by_month[month] = mdata.get('total_revenue', 0)

# ── Trouver les absents ───────────────────────────────────────────────────────
# Le CSV couvre une période — on vérifie quels mois/montants dépassent le JSON
csv_by_month = {}
for r in csv_with_rev:
    m = r['month']
    csv_by_month[m] = csv_by_month.get(m, 0) + r['revenu']

# ── Affichage ─────────────────────────────────────────────────────────────────
print()
print('=' * 80)
print('  COMPARAISON CSV vs leads_revenue_2026.json')
print('=' * 80)

print(f'\n  CSV: {os.path.basename(CSV_PATH)}')
print(f'  Periode: {csv_rows[-1][date_col][:10]} -> {csv_rows[0][date_col][:10]}')
print(f'  Total lignes CSV: {len(csv_rows)}')
print(f'  Lignes avec revenu: {len(csv_with_rev)}')

print(f'\n{"Projet ID":>10}  {"Date":>10}  {"Service":<40}  {"Niche":<20}  {"Revenu":>8}  {"Comm":>7}  Region')
print(f'  {"-"*110}')

total_csv_rev  = 0
total_csv_comm = 0
for r in sorted(csv_with_rev, key=lambda x: x['date']):
    print(f'  {r["projet_id"]:>8}  {r["date"][:10]:>10}  {r["service"]:<40}  {r["niche"]:<20}  ${r["revenu"]:>7.2f}  ${r["commission"]:>6.2f}  {r["region"]}')
    total_csv_rev  += r['revenu']
    total_csv_comm += r['commission']

print(f'\n{"":>10}  {"":>10}  {"TOTAL CSV":>40}  {"":>20}  ${total_csv_rev:>7.2f}  ${total_csv_comm:>6.2f}')

print(f'\n{"="*80}')
print(f'  DIFFERENCE PAR MOIS (CSV vs JSON)')
print(f'{"="*80}')
print(f'  {"Mois":<10}  {"CSV Revenu":>12}  {"JSON Revenu":>12}  {"Diff":>10}  {"Diff Comm":>10}')
print(f'  {"-"*60}')

total_diff = 0
for month in sorted(set(list(csv_by_month.keys()) + list(json_by_month.keys()))):
    csv_r  = csv_by_month.get(month, 0)
    json_r = json_by_month.get(month, 0)
    diff   = csv_r - json_r
    total_diff += diff
    marker = ' <-- MANQUANT' if diff > 5 else ''
    print(f'  {month:<10}  ${csv_r:>11.2f}  ${json_r:>11.2f}  ${diff:>9.2f}  ${diff*COMMISSION:>9.2f}{marker}')

print(f'  {"-"*60}')
print(f'  {"TOTAL":<10}  ${total_csv_rev:>11.2f}  ${sum(json_by_month.values()):>11.2f}  ${total_diff:>9.2f}  ${total_diff*COMMISSION:>9.2f}')
print(f'\n  => Revenu manquant dans le JSON : ${total_diff:.2f}')
print(f'  => Commission manquante         : ${total_diff * COMMISSION:.2f}')
print('=' * 80)
