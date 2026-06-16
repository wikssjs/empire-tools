#!/usr/bin/env python3
"""
Analyse leads soumissionrenovation.ca — source=jb
Période: 2026-01-30 → 2026-06-01
Revenue = prix du lead (votre commission = revenue × 0.40)
"""
import json
from collections import defaultdict

# Records non-nuls : [date, service, revenue_lead]
RECORDS = [
    # FÉVRIER 2026
    ["2026-02-02", "Climatisation", 74.78],
    ["2026-02-04", "Climatisation", 27.03],
    ["2026-02-13", "Climatisation", 56.23],
    ["2026-02-14", "Extermination", 10.50],
    ["2026-02-19", "Climatisation", 76.02],
    # MARS 2026
    ["2026-03-02", "Climatisation", 92.24],
    ["2026-03-02", "Climatisation", 83.13],
    ["2026-03-06", "Calfeutrage", 75.99],
    ["2026-03-09", "Climatisation", 67.13],
    ["2026-03-10", "Fondation - Fissures", 92.90],
    ["2026-03-10", "Climatisation", 73.32],
    ["2026-03-13", "Revêtement extérieur", 100.27],
    ["2026-03-14", "Extermination", 10.53],
    ["2026-03-15", "Portes & Fenêtres - Fournir et installer", 361.32],
    ["2026-03-21", "Portes & Fenêtres - Fournir et installer", 39.78],
    ["2026-03-23", "Plancher - Vernissage", 10.65],
    ["2026-03-24", "Fondation - Excavation", 73.78],
    ["2026-03-25", "Peinture - Intérieur", 78.77],
    ["2026-03-26", "Portes & Fenêtres - Fournir et installer", 75.68],
    ["2026-03-27", "Climatisation", 17.50],
    ["2026-03-28", "Aménagement Paysager - Pavage", 66.80],
    ["2026-03-31", "Fondation - Fissures", 33.38],
    ["2026-03-31", "Portes & Fenêtres - Fournir et installer", 10.42],
    # AVRIL 2026
    ["2026-04-03", "Vitrerie", 79.06],
    ["2026-04-06", "Fondation - Fissures", 18.33],
    ["2026-04-07", "Peinture - Intérieur", 39.00],
    ["2026-04-08", "Portes & Fenêtres - Fournir et installer", 20.13],
    ["2026-04-08", "Gouttières", 50.26],
    ["2026-04-08", "Peinture - Intérieur", 46.06],
    ["2026-04-08", "Gypse & Joint & Peinture", 73.93],
    ["2026-04-12", "Isolation - Sous-sol", 36.94],
    ["2026-04-12", "Portes & Fenêtres - Fournir et installer", 53.35],
    ["2026-04-12", "Climatisation", 19.50],
    ["2026-04-12", "Fondation - Fissures", 15.00],
    ["2026-04-13", "Aménagement Paysager - Excavation", 16.67],
    ["2026-04-14", "Toiture - Toit plat", 286.44],
    ["2026-04-14", "Fondation - Fissures", 53.12],
    ["2026-04-15", "Toiture - Non-métallique (ex-Bardeaux)", 41.89],
    ["2026-04-16", "Climatisation", 22.00],
    ["2026-04-16", "Gouttières", 24.53],
    ["2026-04-16", "Drain Français", 132.53],
    ["2026-04-17", "Portes & Fenêtres - Fournir et installer", 92.69],
    ["2026-04-17", "Aménagement Paysager - Pavage", 28.00],
    ["2026-04-18", "Aménagement Paysager - Horticulture/Jardinage", 15.00],
    ["2026-04-19", "Aménagement Paysager - Complet", 26.30],
    ["2026-04-20", "Fondation - Fissures", 94.22],
    ["2026-04-20", "Aménagement Paysager - Pavage", 33.80],
    ["2026-04-21", "Climatisation", 28.26],
    ["2026-04-21", "Rénovations - Salle de bain (avec électricité / plomberie)", 86.01],
    ["2026-04-21", "Aménagement Paysager - Pavage", 27.55],
    ["2026-04-22", "Aménagement Paysager - Pavage", 26.38],
    ["2026-04-22", "Toiture - Non-métallique (ex-Bardeaux)", 44.44],
    ["2026-04-23", "Fondation - Fissures", 24.34],
    ["2026-04-23", "Fondation - Fissures", 52.18],
    ["2026-04-24", "Fondation - Fissures", 101.22],
    ["2026-04-24", "Climatisation", 39.78],
    ["2026-04-25", "Aménagement Paysager - Piscine", 25.34],
    ["2026-04-26", "Aménagement Paysager - Pavage", 19.00],
    ["2026-04-27", "Extermination", 10.26],
    ["2026-04-27", "Fondation - Fissures", 38.16],
    ["2026-04-27", "Fondation - Fissures", 49.45],
    ["2026-04-27", "Électricien", 29.66],
    ["2026-04-27", "Aménagement Paysager - Pavage", 105.42],
    ["2026-04-28", "Aménagement Paysager - Pavage", 66.74],
    ["2026-04-28", "Isolation - Entre-toît", 109.86],
    ["2026-04-29", "Aménagement Paysager - Béton", 46.15],
    ["2026-04-29", "Plancher - Installation", 16.02],
    ["2026-04-30", "Gouttières", 10.27],
    ["2026-04-30", "Gouttières", 5.00],
    ["2026-04-30", "Portes & Fenêtres - Fournir et installer", 44.75],
    # MAI 2026
    ["2026-05-02", "Extermination", 19.96],
    ["2026-05-02", "Portes & Fenêtres - Fournir seulement", 18.48],
    ["2026-05-03", "Maçonnerie extérieure", 43.63],
    ["2026-05-04", "Aménagement Paysager - Pavage", 40.67],
    ["2026-05-04", "Clôture", 139.64],
    ["2026-05-04", "Ébénisterie (cuisine)", 30.00],
    ["2026-05-04", "Toiture - Toit plat", 121.78],
    ["2026-05-05", "Calfeutrage", 104.40],
    ["2026-05-06", "Homme à tout faire", 5.38],
    ["2026-05-06", "Peinture - Intérieur", 18.00],
    ["2026-05-06", "Aménagement Paysager - Pavage", 110.07],
    ["2026-05-10", "Fondation - Fissures", 51.42],
    ["2026-05-10", "Peinture - Intérieur", 38.90],
    ["2026-05-11", "Climatisation", 71.15],
    ["2026-05-11", "Climatisation", 132.60],
    ["2026-05-11", "Gouttières", 28.37],
    ["2026-05-12", "Portes & Fenêtres - Fournir et installer", 32.99],
    ["2026-05-12", "Rénovations - Salle de bain (avec électricité / plomberie)", 291.09],
    ["2026-05-13", "Clôture", 37.37],
    ["2026-05-13", "Portes & Fenêtres - Fournir et installer", 136.09],
    ["2026-05-14", "Gouttières", 11.16],
    ["2026-05-14", "Drain Français", 110.17],
    ["2026-05-15", "Décontamination", 50.32],
    ["2026-05-15", "Revêtement extérieur", 60.00],
    ["2026-05-16", "Rénovations - Salle de bain", 75.69],
    ["2026-05-16", "Ébénisterie (cuisine)", 23.74],
    ["2026-05-19", "Électricien", 48.48],
    ["2026-05-19", "Gouttières", 10.42],
    ["2026-05-19", "Aménagement Paysager - Excavation", 25.88],
    ["2026-05-19", "Fondation - Fissures", 24.78],
    ["2026-05-19", "Aménagement Paysager - Excavation", 74.39],
    ["2026-05-20", "Clôture", 54.96],
    ["2026-05-20", "Calfeutrage", 10.41],
    ["2026-05-20", "Peinture - Intérieur", 18.00],
    ["2026-05-20", "Isolation - Sous-sol", 72.66],
    ["2026-05-20", "Clôture", 7.51],
    ["2026-05-21", "Aménagement Paysager - Pavage", 35.45],
    ["2026-05-21", "Clôture", 10.00],
    ["2026-05-22", "Aménagement Paysager - Pavage", 40.67],
    ["2026-05-22", "Électricien", 16.16],
    ["2026-05-22", "Aménagement Paysager - Pavage", 76.46],
    ["2026-05-23", "Clôture", 64.86],
    ["2026-05-23", "Fondation - Complet", 42.79],
    ["2026-05-23", "Peinture - Extérieur", 36.00],
    ["2026-05-24", "Aménagement Paysager - Pavage", 71.59],
    ["2026-05-24", "Fosse septique - Installation", 16.71],
    ["2026-05-24", "Rénovations - Salle de bain", 156.31],
    ["2026-05-25", "Clôture", 53.02],
    ["2026-05-25", "Fondation - Imperméabilisation", 49.91],
    ["2026-05-25", "Clôture", 36.17],
    ["2026-05-28", "Peinture - Extérieur", 38.71],
    ["2026-05-28", "Portes & Fenêtres - Fournir et installer", 82.08],
    ["2026-05-28", "Fosse septique - Installation", 226.27],
    ["2026-05-28", "Gouttières", 31.74],
    ["2026-05-31", "Climatisation", 23.85],
    ["2026-05-31", "Portes & Fenêtres - Fournir et installer", 87.91],
    # JUIN 2026
    ["2026-06-01", "Revêtement extérieur", 15.83],
    ["2026-06-01", "Calfeutrage", 45.00],
    ["2026-06-01", "Designer Intérieur", 81.83],
    ["2026-06-01", "Électricien", 15.19],
    ["2026-06-02", "Électricien", 19.00],
    ["2026-06-02", "Peinture - Intérieur", 38.83],
    ["2026-06-02", "Gouttières", 24.10],
    ["2026-06-04", "Climatisation", 44.46],
    ["2026-06-04", "Gouttières", 10.38],
    ["2026-06-04", "Calfeutrage", 18.00],
    ["2026-06-05", "Fondation - Fissures", 19.27],
    ["2026-06-06", "Gouttières", 51.97],
    ["2026-06-06", "Aménagement Paysager - Pavage", 37.45],
]

NICHE_MAP = {
    "Climatisation": "thermopompe",
    "Fondation - Fissures": "fissure",
    "Fondation - Complet": "fissure",
    "Fondation - Imperméabilisation": "fissure",
    "Fondation - Excavation": "excavation",
    "Aménagement Paysager - Excavation": "excavation",
    "Portes & Fenêtres - Fournir et installer": "fenetres",
    "Portes & Fenêtres - Fournir seulement": "fenetres",
    "Gouttières": "gouttieres",
    "Drain Français": "drain",
    "Toiture - Non-métallique (ex-Bardeaux)": "toiture",
    "Toiture - Non-métallique": "toiture",
    "Toiture - Tôle": "toiture",
    "Toiture - Toit plat": "toiture_plate",
    "Revêtement extérieur": "revetement",
    "Soffites/Fascias": "revetement",
    "Aménagement Paysager - Pavage": "pavage",
    "Aménagement Paysager - Pavé-uni": "pavage",
    "Aménagement Paysager - Béton": "beton",
    "Béton - Escalier/Dalle": "beton",
    "Aménagement Paysager - Piscine": "piscine",
    "Aménagement Paysager - Horticulture/Jardinage": "paysagement",
    "Aménagement Paysager - Complet": "paysagement",
    "Aménagement paysager - Entretien": "paysagement",
    "Extermination": "extermination",
    "Calfeutrage": "calfeutrage",
    "Peinture - Intérieur": "peinture",
    "Peinture - Extérieur": "peinture",
    "Gypse & Joint & Peinture": "peinture",
    "Isolation - Sous-sol": "isolation",
    "Isolation - Entre-toît": "isolation",
    "Fosse septique - Installation": "fosseseptique",
    "Fosse septique - Entretien": "fosseseptique",
    "Décontamination": "decontamination",
    "Électricien": "electricien",
    "Maçonnerie extérieure": "maconnerie",
    "Vitrerie": "ceramique",
    "Carrelage": "ceramique",
    "Rénovations - Salle de bain (avec électricité / plomberie)": "salledebain",
    "Rénovations - Salle de bain": "salledebain",
    "Rénovations - Cuisine (avec électricité / plomberie)": "cuisine",
    "Rénovations - Cuisine": "cuisine",
    "Ébénisterie (cuisine)": "cuisine",
    "Plancher - Vernissage": "plancher",
    "Plancher - Installation": "plancher",
    "Clôture": "cloture",
    "Homme à tout faire": "autres",
    "Plombier": "autres",
    "Arpenteur": "autres",
    "Insonorisation": "autres",
    "Scellant d'entrée": "autres",
    "Designer Intérieur": "autres",
    "Nettoyage conduit aération / climatiseur": "autres",
    "Agrandissement de maison": "autres",
    "Balcon & Patio Multi-Matériaux": "terrasse",
    "Patio - Au sol": "terrasse",
}

NICHE_SITES = {
    "thermopompe": "prix-thermopompe.ca",
    "fissure": "prix-fissure.ca",
    "excavation": "experts-excavation.ca",
    "fenetres": "soumission-fenetres.ca",
    "gouttieres": "prix-gouttieres.ca",
    "drain": "prix-drain.ca",
    "toiture": "prix-toiture.ca",
    "toiture_plate": "experts-toiture-plate.ca",
    "revetement": "prix-revetement.ca",
    "pavage": "prixpavage.ca",
    "extermination": "prixextermination.ca",
    "calfeutrage": "expertcalfeutrage.ca",
    "peinture": "prix-peinture.ca",
    "isolation": "prix-isolation.ca",
    "fosseseptique": "experts-fosseseptique.ca",
    "decontamination": "experts-decontamination.ca",
    "electricien": "prix-electricien.ca",
    "maconnerie": "experts-maconnerie.ca",
    "ceramique": "experts-ceramique.ca",
    "salledebain": "soumission-salledebain.ca",
    "cuisine": "prix-cuisine.ca",
    "plancher": "soumission-plancher.ca",
    "cloture": "soumission-cloture.ca",
    "beton": "experts-beton.ca",
    "piscine": "(no site)",
    "paysagement": "prix-paysagement.ca",
    "autres": "(divers)",
}

COMMISSION_RATE = 0.40

def get_niche(service):
    return NICHE_MAP.get(service, "autres")

by_month_niche = defaultdict(lambda: defaultdict(float))
by_month_niche_leads = defaultdict(lambda: defaultdict(int))
by_niche_total = defaultdict(float)
by_niche_leads = defaultdict(int)
by_month_total = defaultdict(float)

for date, service, revenue in RECORDS:
    month = date[:7]
    niche = get_niche(service)
    by_month_niche[month][niche] += revenue
    by_month_niche_leads[month][niche] += 1
    by_niche_total[niche] += revenue
    by_niche_leads[niche] += 1
    by_month_total[month] += revenue

total_revenue = sum(by_niche_total.values())

result = {
    "generated": "2026-06-07",
    "period": "2026-01-30 → 2026-06-06",
    "note": "Revenue = prix brut du lead. Commission vous revenant = revenue × 0.40. ~80-85% des leads capturés (some records may be missing from page limits).",
    "commission_rate": COMMISSION_RATE,
    "total": {
        "revenue_leads": round(total_revenue, 2),
        "your_commission": round(total_revenue * COMMISSION_RATE, 2),
        "leads_with_revenue": len(RECORDS)
    },
    "actual_payments_received": {
        "2026-03-04": 97.82,
        "2026-04-01": 623.13,
        "2026-05-06": 1124.00,
        "total_paid": 1844.95
    },
    "by_niche": {
        niche: {
            "site": NICHE_SITES.get(niche, niche),
            "leads": by_niche_leads[niche],
            "revenue_leads": round(rev, 2),
            "your_commission": round(rev * COMMISSION_RATE, 2),
            "pct_of_total": round(rev / total_revenue * 100, 1)
        }
        for niche, rev in sorted(by_niche_total.items(), key=lambda x: -x[1])
    },
    "by_month": {
        month: {
            "total_revenue": round(total, 2),
            "total_commission": round(total * COMMISSION_RATE, 2),
            "by_niche": {
                niche: {
                    "revenue": round(by_month_niche[month][niche], 2),
                    "leads": by_month_niche_leads[month][niche]
                }
                for niche in sorted(by_month_niche[month], key=lambda n: -by_month_niche[month][n])
            }
        }
        for month, total in sorted(by_month_total.items())
    }
}

output_path = "leads_revenue_2026.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"JSON sauvegarde: {output_path}")
print(f"\nTotal revenue leads: ${result['total']['revenue_leads']:,.2f}")
print(f"Total commission calculée: ${result['total']['your_commission']:,.2f}")
print(f"Total paiements reçus: $1,844.95")
print(f"\n{'Niche':<16} {'Site':<32} {'Leads':>5} {'Revenue':>10} {'Commission':>12} {'%':>6}")
print("-" * 85)
for niche, data in result["by_niche"].items():
    print(f"{niche:<16} {data['site']:<32} {data['leads']:>5} ${data['revenue_leads']:>9,.2f} ${data['your_commission']:>11,.2f} {data['pct_of_total']:>5.1f}%")
print("-" * 85)
print(f"\n{'TOTAL':<49} {len(RECORDS):>5} ${total_revenue:>9,.2f} ${total_revenue*COMMISSION_RATE:>11,.2f} 100.0%")
