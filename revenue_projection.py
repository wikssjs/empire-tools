#!/usr/bin/env python3
"""
Projection revenu Empire-PSEO — Juin → Décembre 2026
Données: leads_revenue_2026.json + sites_age.json
Méthode: run rate mai 2026 (scaled) × courbe de maturité SEO par âge domaine
"""
import json
from datetime import date

# ── Charger les données ──────────────────────────────────────────────────────
with open('leads_revenue_2026.json', encoding='utf-8') as f:
    leads = json.load(f)

with open('sites_age.json', encoding='utf-8') as f:
    ages_data = json.load(f)

COMMISSION_RATE = 0.40
TODAY = date(2026, 6, 7)
MONTHS = ['2026-07', '2026-08', '2026-09', '2026-10', '2026-11', '2026-12']
MONTH_LABELS = ['Jul', 'Aou', 'Sep', 'Oct', 'Nov', 'Dec']

# ── Scale factor ─────────────────────────────────────────────────────────────
# Mai confirmé par l'utilisateur: $1,694 commission
# Mes données mai: ~$1,339 → scale = 1.265 (capture 79% des leads)
MAY_CONFIRMED = 1694.0
my_may = leads['by_month'].get('2026-05', {}).get('total_commission', 1339)
SCALE = MAY_CONFIRMED / my_may

# ── Map niche → domaine + âge ────────────────────────────────────────────────
niche_info = {}
for domain, info in ages_data['sites'].items():
    niche_info[info['niche']] = {
        'domain': domain,
        'age_months': info['age_months'],
        'registered': info['registered']
    }

# ── Run rate mensuel par niche (commission en $) ─────────────────────────────
def get_monthly_commission(niche):
    """Run rate juin estimé: priorité juin annualisé > mai > avril > mars."""
    best = 0

    # Juin partiel (7 jours → annualisé 30j)
    jun = leads['by_month'].get('2026-06', {}).get('by_niche', {}).get(niche, {})
    jun_rev = jun.get('revenue', 0) if isinstance(jun, dict) else 0
    if jun_rev > 0:
        best = max(best, jun_rev * COMMISSION_RATE * SCALE * (30 / 7))

    # Mai (mois le plus récent complet)
    may = leads['by_month'].get('2026-05', {}).get('by_niche', {}).get(niche, {})
    may_rev = may.get('revenue', 0) if isinstance(may, dict) else 0
    if may_rev > 0:
        best = max(best, may_rev * COMMISSION_RATE * SCALE)

    # Avril
    apr = leads['by_month'].get('2026-04', {}).get('by_niche', {}).get(niche, {})
    apr_rev = apr.get('revenue', 0) if isinstance(apr, dict) else 0
    if apr_rev > 0 and best == 0:
        best = apr_rev * COMMISSION_RATE * SCALE * 0.85  # légère réduction (old)

    return best

# ── Taux de croissance mensuel par âge ───────────────────────────────────────
# Basé sur courbe SEO typique + données réelles portfolio
def growth_rate(age_months):
    if age_months < 1.5:  return 0.85   # tout nouveau
    elif age_months < 2.5: return 0.50
    elif age_months < 3.5: return 0.30
    elif age_months < 4.5: return 0.20
    elif age_months < 6:   return 0.13
    elif age_months < 9:   return 0.08
    else:                  return 0.05

# Plafonds réalistes par niche (commission/mois max en $)
CEILING = {
    'fenetres':      1100, 'thermopompe':  900, 'fissure':      700,
    'drain':          600, 'pavage':        750, 'salledebain':  800,
    'toiture':       1400, 'toiture_plate': 600, 'revetement':   500,
    'gouttieres':     450, 'calfeutrage':   350, 'fosseseptique':500,
    'cloture':        700, 'peinture':      600, 'isolation':    400,
    'electricien':    400, 'excavation':    600, 'decontamination':350,
    'cuisine':        500, 'ceramique':     400, 'beton':        400,
    'maconnerie':     300, 'extermination': 350, 'chauffage':    500,
    'agrandissement': 500, 'deneigement':   800, 'demenagement': 400,
    'emondage':       250, 'plancher':      350, 'porte_garage': 600,
    # Nouveaux — toiture cluster
    'toiture_residentielle': 700, 'bardeau': 500, 'couvreur': 550,
    # Nouveaux — thermopompe sub-niches
    'climatisation_thermopompe': 600, 'installation_thermopompe': 650,
    'reparation_thermopompe': 500, 'thermopompe_aerothermique': 450,
    # Nouveaux — pavage cluster
    'pavage_asphalte': 400, 'pavage_commercial': 300, 'pave_uni': 300,
}
DEFAULT_CEILING = 300

GROWTH_DECAY = 0.82  # le taux de croissance baisse de 18% chaque mois

# ── Construire les projections ────────────────────────────────────────────────
projections = {}
all_niches = set(niche_info.keys()) - {'piscine'}  # piscine = monétisation non réglée

for niche in sorted(all_niches):
    info = niche_info[niche]
    age = info['age_months']
    ceiling = CEILING.get(niche, DEFAULT_CEILING)

    run_rate = get_monthly_commission(niche)

    # Sites sans données encore → démarrage estimé selon l'âge
    if run_rate < 3:
        if age < 1.5:   run_rate = 8
        elif age < 2.5: run_rate = 20
        elif age < 4:   run_rate = 40
        else:           run_rate = 60

    monthly = {'2026-06': round(run_rate, 2)}
    g = growth_rate(age)
    current = run_rate

    for month in MONTHS:
        current = min(current * (1 + g), ceiling)
        g = g * GROWTH_DECAY
        monthly[month] = round(current, 2)

    projections[niche] = {
        'site': info['domain'],
        'age_months': age,
        'ceiling': ceiling,
        'monthly': monthly
    }

# ── Totaux portfolio ──────────────────────────────────────────────────────────
portfolio = {}
for m in ['2026-06'] + MONTHS:
    portfolio[m] = round(sum(p['monthly'][m] for p in projections.values()), 2)

# ── Sauvegarder JSON ──────────────────────────────────────────────────────────
output = {
    'generated': str(TODAY),
    'method': 'Run rate mai 2026 (scale {:.3f}) x courbe maturite SEO'.format(SCALE),
    'confirmed_commissions': {
        '2026-02': 97.82, '2026-03': 623.13,
        '2026-04': 1124.00, '2026-05': 1694.00
    },
    'scale_factor': round(SCALE, 3),
    'portfolio_monthly': portfolio,
    'by_niche': {
        niche: {
            'site': p['site'],
            'age_months': p['age_months'],
            'ceiling': p['ceiling'],
            'projections': p['monthly']
        }
        for niche, p in sorted(projections.items(), key=lambda x: -x[1]['monthly']['2026-06'])
    }
}

with open('revenue_projection_2026.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

# ── Affichage console ─────────────────────────────────────────────────────────
print()
print(f"{'='*108}")
print(f"  PROJECTION REVENU PORTFOLIO — Juin à Decembre 2026  (commission 40%)")
print(f"{'='*108}")
print(f"\n  Historique confirme:")
print(f"  Feb $97   | Mar $623  | Avr $1,124  | Mai $1,694")
print(f"\n{'Niche':<18} {'Age':>4}  {'Jun':>7} {'Jul':>7} {'Aou':>7} {'Sep':>7} {'Oct':>7} {'Nov':>7} {'Dec':>7}  Site")
print(f"  {'-'*100}")

for niche, p in sorted(projections.items(), key=lambda x: -x[1]['monthly']['2026-06']):
    m = p['monthly']
    print(
        f"  {niche:<16} {p['age_months']:>4.1f}m"
        f"  ${m['2026-06']:>6.0f}"
        f"  ${m['2026-07']:>6.0f}"
        f"  ${m['2026-08']:>6.0f}"
        f"  ${m['2026-09']:>6.0f}"
        f"  ${m['2026-10']:>6.0f}"
        f"  ${m['2026-11']:>6.0f}"
        f"  ${m['2026-12']:>6.0f}"
        f"  {p['site']}"
    )

print(f"  {'-'*100}")
print(
    f"  {'TOTAL PORTFOLIO':<20}"
    f"  ${portfolio['2026-06']:>6.0f}"
    f"  ${portfolio['2026-07']:>6.0f}"
    f"  ${portfolio['2026-08']:>6.0f}"
    f"  ${portfolio['2026-09']:>6.0f}"
    f"  ${portfolio['2026-10']:>6.0f}"
    f"  ${portfolio['2026-11']:>6.0f}"
    f"  ${portfolio['2026-12']:>6.0f}"
)
print(f"\n  JSON sauvegarde: revenue_projection_2026.json")
print(f"{'='*108}")
