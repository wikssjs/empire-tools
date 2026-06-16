#!/usr/bin/env python3
"""
fetch_niche_research.py — Comprehensive niche research via Perplexity + Claude synthesis.

Outputs:
  engine_qc/niche_research_<niche>.json   — Full research + generated prompts
  engine_qc/config_<niche>.json           — Draft config (review before using)

Usage:
  python tools/fetch_niche_research.py --niche porte-garage \
    --description "Installation et remplacement de portes de garage résidentielles au Québec" \
    --domain "soumission-porte-garage.ca" \
    --css-prefix "pg-"
"""

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path

import anthropic
import requests

BASE = Path(__file__).parent.parent
ENGINE_QC = BASE / "engine_qc"

PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "")


def call_perplexity(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "sonar-pro",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2500,
        "temperature": 0.2,
    }
    resp = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers=headers,
        json=payload,
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def call_claude(system: str, user: str, max_tokens: int = 12000) -> str:
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--niche", required=True, help="Niche slug (ex: porte-garage)")
    parser.add_argument("--description", required=True, help="Description courte de la niche")
    parser.add_argument("--domain", default="", help="Domaine cible (ex: soumission-porte-garage.ca)")
    parser.add_argument("--css-prefix", default="", help="Prefixe CSS (ex: pg-)")
    args = parser.parse_args()

    niche = args.niche
    description = args.description
    domain = args.domain or f"soumission-{niche}.ca"
    css_prefix = args.css_prefix or (niche.replace("-", "")[:3] + "-")

    print(f"\n=== Niche Research: {niche} ===")
    print(f"Description : {description}")
    print(f"Domaine     : {domain}")
    print(f"CSS prefix  : {css_prefix}\n")

    # =========================================================================
    # PERPLEXITY 1 — Marche & Services
    # =========================================================================
    print("[1/3] Perplexity — Marche & Services...")
    p1 = (
        f"Tu es un expert du marche de la renovation residentielle au Quebec. "
        f"Analyse en profondeur le marche de : {description}\n\n"
        f"Couvre ces 4 points avec des donnees precises et propres au Quebec :\n"
        f"(1) SERVICES EXACTS : liste exhaustive des services offerts dans ce secteur au Quebec. "
        f"Pour chaque service : nom exact en francais quebecois, description 1 phrase, cas d'usage typique.\n"
        f"(2) TYPES DE PRODUITS/MATERIAUX : tous les types disponibles au QC avec leurs caracteristiques "
        f"et ce qui se vend le plus dans chaque region.\n"
        f"(3) MARQUES & FOURNISSEURS AU QC : les marques les plus vendues au Quebec, "
        f"distributeurs locaux connus, certifications requises (RBQ, etc.).\n"
        f"(4) MARCHE ET SAISONNALITE : taille du marche, quand les gens achevent, "
        f"profil typique du client, ce qui declenche l'achat.\n\n"
        f"Reponds en francais, donnees factuelles, 400-500 mots."
    )
    market_data = call_perplexity(p1)
    print("  OK")
    time.sleep(2)

    # =========================================================================
    # PERPLEXITY 2 — Prix & Facteurs de cout
    # =========================================================================
    print("[2/3] Perplexity — Prix & Facteurs de cout...")
    p2 = (
        f"Tu es un expert des prix du marche de la renovation au Quebec. "
        f"Analyse les prix du marche pour : {description}\n\n"
        f"(1) FOURCHETTES DE PRIX PAR SERVICE : pour chaque service principal, "
        f"donne les fourchettes de prix reelles au Quebec en 2024-2025 (main-d'oeuvre + materiaux inclus). "
        f"Distingue grande ville (Montreal/Quebec) vs region.\n"
        f"(2) FACTEURS QUI FONT VARIER LE PRIX : liste exhaustive avec impact chiffre.\n"
        f"(3) PRIX PAR CATEGORIE DE VILLE : "
        f"grande ville 50k+ | ville moyenne 15-50k | petite ville 5-15k | village <5k\n"
        f"(4) MAIN-D'OEUVRE vs MATERIAUX : ratio typique, cout horaire dans ce secteur.\n\n"
        f"TERMINE PAR CE BLOC JSON EXACT (entiers seulement) :\n"
        f"---PRIX-NATIONAL---\n"
        '{{"s1_label": "NOM SERVICE 1", "s1_min": XXXXX, "s1_max": XXXXX, '
        '"s2_label": "NOM SERVICE 2", "s2_min": XXXXX, "s2_max": XXXXX, '
        '"s3_label": "NOM SERVICE 3", "s3_min": XXXXX, "s3_max": XXXXX, '
        '"s4_label": "NOM SERVICE 4", "s4_min": XXXXX, "s4_max": XXXXX}}'
    )
    price_data = call_perplexity(p2)
    print("  OK")

    # Parse national prices from Perplexity
    national_prices = {}
    if "---PRIX-NATIONAL---" in price_data:
        try:
            bloc = price_data.split("---PRIX-NATIONAL---", 1)[1].strip()
            for line in bloc.splitlines():
                line = line.strip()
                if line.startswith("{"):
                    national_prices = json.loads(line)
                    break
        except Exception:
            pass

    time.sleep(2)

    # =========================================================================
    # PERPLEXITY 3 — SEO & Intentions
    # =========================================================================
    print("[3/3] Perplexity — SEO & Intentions de recherche...")
    p3 = (
        f"Tu es un expert SEO specialise dans la renovation residentielle au Quebec. "
        f"Analyse les intentions de recherche pour : {description}\n\n"
        f"(1) MOTS-CLES PRINCIPAUX : 15 requetes reelles que les Quebecois tapent dans Google. "
        f"Format : 'mot-cle | intention (informationnelle/commerciale/urgence)'\n"
        f"(2) QUESTIONS FAQ : 10 vraies questions que les consommateurs se posent avant d'acheter. "
        f"Questions precises, ancrees dans la realite quebecoise.\n"
        f"(3) 6 ANGLES DE CONTENU QUI CONVERTISSENT : les sections les plus efficaces pour un site "
        f"de generation de leads local. Chaque angle = titre de section + ce qu'il doit contenir "
        f"+ pourquoi ca convertit.\n"
        f"(4) OBJECTIONS TYPIQUES : les 5 raisons pour lesquelles un prospect hesite "
        f"et comment les adresser dans le contenu.\n\n"
        f"Reponds en francais, oriente conversion et SEO local quebecois."
    )
    seo_data = call_perplexity(p3)
    print("  OK\n")

    # =========================================================================
    # CLAUDE — Synthese complete
    # =========================================================================
    print("[Claude] Synthese et generation config + prompts...")

    synthesis_system = (
        "Tu es un architecte de sites SEO programmatiques specialise dans la generation de leads "
        "pour la renovation residentielle au Quebec. "
        "Tu generes des configs JSON precis et des prompts de generation de contenu optimises pour la conversion. "
        "Tu reponds UNIQUEMENT avec du JSON valide, aucun texte avant ou apres."
    )

    # Build price tier hints from national prices
    price_hint = ""
    if national_prices:
        price_hint = (
            f"\nPrix nationaux detectes par Perplexity :\n"
            f"  service1 ({national_prices.get('s1_label','')}) : "
            f"{national_prices.get('s1_min',0)}-{national_prices.get('s1_max',0)}$\n"
            f"  service2 ({national_prices.get('s2_label','')}) : "
            f"{national_prices.get('s2_min',0)}-{national_prices.get('s2_max',0)}$\n"
            f"  service3 ({national_prices.get('s3_label','')}) : "
            f"{national_prices.get('s3_min',0)}-{national_prices.get('s3_max',0)}$\n"
            f"  service4 ({national_prices.get('s4_label','')}) : "
            f"{national_prices.get('s4_min',0)}-{national_prices.get('s4_max',0)}$\n"
        )

    synthesis_user = f"""
Donnees de recherche Perplexity pour la niche : {niche}
Description : {description}
Domaine cible : {domain}
{price_hint}

=== MARCHE & SERVICES ===
{market_data}

=== PRIX & COUTS ===
{price_data}

=== SEO & INTENTIONS ===
{seo_data}

---

Genere un JSON avec exactement cette structure. TOUTES les valeurs doivent etre remplies avec les vraies donnees :

{{
  "research_summary": {{
    "services": [
      {{"id": "service1", "label_fr": "VRAI NOM SERVICE 1", "description": "description 1 phrase", "price_min_gv": 0, "price_max_gv": 0}},
      {{"id": "service2", "label_fr": "VRAI NOM SERVICE 2", "description": "description 1 phrase", "price_min_gv": 0, "price_max_gv": 0}},
      {{"id": "service3", "label_fr": "VRAI NOM SERVICE 3", "description": "description 1 phrase", "price_min_gv": 0, "price_max_gv": 0}},
      {{"id": "service4", "label_fr": "VRAI NOM SERVICE 4", "description": "description 1 phrase", "price_min_gv": 0, "price_max_gv": 0}}
    ],
    "brands": ["marque1", "marque2", "marque3", "marque4"],
    "product_types": ["type1", "type2", "type3", "type4"],
    "key_cost_factors": ["facteur1", "facteur2", "facteur3", "facteur4", "facteur5"],
    "top_keywords": ["kw1", "kw2", "kw3", "kw4", "kw5", "kw6", "kw7", "kw8"],
    "faq_questions": ["question complete 1 ?", "question complete 2 ?", "question complete 3 ?", "question complete 4 ?", "question complete 5 ?", "question complete 6 ?"]
  }},
  "price_tiers": {{
    "grande_ville":  {{"seuil": 50000, "service1_min": 0, "service1_max": 0, "service2_min": 0, "service2_max": 0, "service3_min": 0, "service3_max": 0, "service4_min": 0, "service4_max": 0}},
    "moyenne_ville": {{"seuil": 15000, "service1_min": 0, "service1_max": 0, "service2_min": 0, "service2_max": 0, "service3_min": 0, "service3_max": 0, "service4_min": 0, "service4_max": 0}},
    "petite_ville":  {{"seuil":  5000, "service1_min": 0, "service1_max": 0, "service2_min": 0, "service2_max": 0, "service3_min": 0, "service3_max": 0, "service4_min": 0, "service4_max": 0}},
    "village":       {{"seuil":     0, "service1_min": 0, "service1_max": 0, "service2_min": 0, "service2_max": 0, "service3_min": 0, "service3_max": 0, "service4_min": 0, "service4_max": 0}}
  }},
  "system_prompt": "Tu es un redacteur web expert en [NICHE COMPLETE avec marques, certifications, types de produits specifiques]. Tu maitrises [DETAILS SPECIFIQUES]. Tu generes du HTML structure avec des tableaux propres, des sections riches en donnees chiffrees, et un contenu unique par ville qui aide le proprietaire a comprendre, budgeter et choisir un entrepreneur fiable.",
  "user_prompt_template": "Genere un bloc de contenu HTML COMPLET et RICHE pour la page \\"prix {niche} a {{ville}}\\" ({{region}}, Quebec).\\nPopulation : {{population}} habitants.\\n\\nContexte regional reel : {{context}}\\n\\nPrix locaux fournis (utilise ces donnees dans le contenu) :\\n- [SERVICE 1] : {{service1_min}}$ -- {{service1_max}}$\\n- [SERVICE 2] : {{service2_min}}$ -- {{service2_max}}$\\n- [SERVICE 3] : {{service3_min}}$ -- {{service3_max}}$\\n- [SERVICE 4] : {{service4_min}}$ -- {{service4_max}}$\\n\\nSTRUCTURE OBLIGATOIRE -- genere ces 6 sections dans l'ordre exact :\\n\\n---\\nSECTION 1 -- [TITRE SECTION 1 base sur angle 1]\\n<h2 class=\\"text-3xl font-bold text-gray-900 mb-4\\">[TITRE H2 avec {{ville}}]</h2>\\n[Description precise de ce que cette section doit contenir : 180-220 mots + tableau HTML]\\nClasses tableau : <table class=\\"w-full text-sm border-collapse mt-6 mb-2\\"> <thead class=\\"bg-gray-900 text-white\\"> <th class=\\"px-4 py-3 text-left font-semibold\\"> <tbody> <tr class=\\"border-b border-gray-200 hover:bg-gray-50\\"> <td class=\\"px-4 py-3\\">\\n\\n---\\nSECTION 2 -- [TITRE SECTION 2]\\n<h2> accrocheur ancre dans {{ville}}\\n[Description precise du contenu : 180-220 mots + tableau]\\n\\n---\\nSECTION 3 -- [TITRE SECTION 3]\\n<h2> original mentionnant {{region}} ou {{ville}}\\n[Description precise du contenu : 200-250 mots + tableau]\\n\\n---\\nSECTION 4 -- [TITRE SECTION 4]\\n<h2> direct et pratique\\n[Description precise du contenu : 200-250 mots + tableau]\\n\\n---\\nSECTION 5 -- Comment choisir son entrepreneur a {{ville}}\\n<h2> rassurant et local\\n[Description precise : licence RBQ, assurances, devis detaille, garanties, delais dans {{region}}]\\nTableau : Critere | Ce qu'il faut verifier | Pourquoi c'est important\\n\\n---\\nSECTION 6 -- FAQ : [NICHE] a {{ville}}\\n<h2 class=\\"text-3xl font-bold text-gray-900 mb-8\\">Questions frequentes sur [NICHE] a {{ville}}</h2>\\nGenere 6 questions-reponses en accordeon HTML avec ces classes exactes :\\n<details class=\\"group bg-white rounded-xl border border-gray-200 overflow-hidden mb-3\\">\\n<summary class=\\"flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50\\">\\n<span class=\\"font-semibold text-gray-900 pr-4\\">QUESTION ICI</span>\\n<svg class=\\"w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform\\" fill=\\"none\\" stroke=\\"currentColor\\" viewBox=\\"0 0 24 24\\"><path stroke-linecap=\\"round\\" stroke-linejoin=\\"round\\" stroke-width=\\"2\\" d=\\"M19 9l-7 7-7-7\\"/></svg>\\n</summary>\\n<div class=\\"px-6 pb-6 text-gray-600 leading-relaxed\\">REPONSE ICI (80-120 mots, precise, avec donnees locales)</div>\\n</details>\\nQuestions : [FAQ 1] | [FAQ 2] | [FAQ 3] | [FAQ 4] | [FAQ 5] | [FAQ 6]\\n\\n---\\n\\nREGLES ABSOLUES :\\n- Reponds UNIQUEMENT avec le HTML brut, aucun commentaire avant ou apres\\n- NE genere PAS de wrapper exterieur <div> ou <section> global\\n- Utilise les classes Tailwind deja definies (text-gray-900, text-gray-600, font-bold, etc.)\\n- Integre les prix fournis directement dans les tableaux et le texte\\n- Mentionne {{ville}} et {{region}} naturellement dans chaque section\\n- Aucune liste a puces <ul><li> -- uniquement <p>, tableaux et accordeons\\n- Chaque section doit apporter une valeur distincte, pas de repetition",
  "regional_context_prompt": "Tu es un expert en [NICHE] au Quebec. Ta mission : produire un contexte regional PRECIS sur [NICHE] dans la region administrative {{region}} au Quebec. Couvre : (1) MARCHE LOCAL : types de proprietes, demande specifique a {{region}}, entreprises actives. (2) PRODUITS POPULAIRES : ce que les clients de {{region}} choisissent le plus. (3) MARQUES ET FOURNISSEURS LOCAUX : disponibilite dans {{region}}. (4) FACTEURS DE COUT SPECIFIQUES : cout main-d'oeuvre, accessibilite, sol/terrain, saisonnalite dans {{region}}. (5) REGLEMENTATIONS : permis et normes specifiques aux municipalites de {{region}}. Reponds en 280-320 mots, francais, factuel, specifique a {{region}}. PRIX DU MARCHE DANS {{region}} : fourchettes reelles 2024-2025 pour les 4 services. Calibration nationale : [SERVICE1] [MIN1]-[MAX1]$ | [SERVICE2] [MIN2]-[MAX2]$ | [SERVICE3] [MIN3]-[MAX3]$ | [SERVICE4] [MIN4]-[MAX4]$. TERMINE PAR :\\n---PRIX---\\n{{service1_min: XXXXX, service1_max: XXXXX, service2_min: XXXXX, service2_max: XXXXX, service3_min: XXXXX, service3_max: XXXXX, service4_min: XXXXX, service4_max: XXXXX}}"
}}

REGLES DE GENERATION :
- Tous les prix sont des entiers
- Les labels de services sont en francais quebecois naturel
- Le system_prompt doit mentionner les vraies marques et certifications trouvees dans la recherche
- Le user_prompt_template doit avoir les 6 sections COMPLETES et DETAILLEES avec le vrai contenu de chaque section (pas de placeholder generique)
- Le regional_context_prompt doit remplacer [SERVICE1/2/3/4] et [MIN/MAX] par les vraies valeurs des prix nationaux
- Les content_sections doivent refleter les vrais angles de conversion decouverts dans la recherche SEO
- Reponds UNIQUEMENT avec le JSON, aucun texte avant ou apres
"""

    raw = call_claude(synthesis_system, synthesis_user, max_tokens=14000)

    # Clean up markdown fences if present
    synthesis = raw.strip()
    if synthesis.startswith("```"):
        parts = synthesis.split("```")
        synthesis = parts[1]
        if synthesis.startswith("json"):
            synthesis = synthesis[4:]
    synthesis = synthesis.strip()

    try:
        research = json.loads(synthesis)
        print("  Synthese OK")
    except json.JSONDecodeError as e:
        print(f"  Erreur JSON synthese: {e}")
        print("  Sauvegarde raw output...")
        research = {"error": str(e), "raw_synthesis": raw}

    # =========================================================================
    # SAVE niche_research JSON
    # =========================================================================
    output = {
        "niche": niche,
        "description": description,
        "domain": domain,
        "research_date": datetime.now().strftime("%Y-%m-%d"),
        "national_prices": national_prices,
        "raw_perplexity": {
            "market_services": market_data,
            "prices": price_data,
            "seo_intent": seo_data,
        },
        **{k: v for k, v in research.items() if k != "raw_synthesis"},
    }

    research_path = ENGINE_QC / f"niche_research_{niche}.json"
    research_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Sauvegarde : {research_path.name}")

    # =========================================================================
    # AUTO-GENERATE CONFIG
    # =========================================================================
    if "price_tiers" in research and "research_summary" in research:
        print("[Config] Generation du config draft...")
        rs = research["research_summary"]
        pt = research["price_tiers"]
        services = rs.get("services", [])

        def svc(i): return services[i] if i < len(services) else {"label_fr": f"Service {i+1}", "description": ""}

        config = {
            "_comment": f"config_{niche}.json — AUTO-GENERE par fetch_niche_research.py — A REVISER avant utilisation",
            "_generated_from": f"niche_research_{niche}.json",
            "site": {
                "name": " ".join(w.capitalize() for w in niche.split("-")),
                "niche": niche,
                "domain": f"https://{domain}",
                "phone": "",
                "service_label": svc(0)["label_fr"],
                "schema_type": "HomeAndConstructionBusiness",
                "schema_description": (
                    f"{description} a {{ville}}. "
                    + ", ".join(rs.get("product_types", [])[:3])
                    + ". Entrepreneurs certifies RBQ."
                ),
                "price_range": "$$-$$$",
                "ga_id": "G-XXXXXXXXXX",
                "logo": "logo.svg",
                "form_name": f"soumission-{niche}",
                "lead_system": "external_link",
            },
            "affiliate": {
                "url": f"https://{domain}/soumission",
                "cta_label": "Obtenir mes soumissions",
                "redirect_param": "ville",
            },
            "seo": {
                "title_template": f"Prix {niche.replace('-', ' ').title()} {{ville}} {{year}} — Soumissions gratuites",
                "meta_description_template": (
                    f"{description} a {{ville}}. "
                    f"Comparez les prix et obtenez des soumissions gratuites d'entrepreneurs certifies RBQ."
                ),
                "h1_template": f"Prix {niche.replace('-', ' ').title()} a {{ville}} — Soumissions gratuites {{year}}",
            },
            "prices": {tier: {**vals} for tier, vals in pt.items()},
            "design": {
                "css_prefix": css_prefix,
                "templates_dir": "templates_v3",
                "city_content_file": f"city_content_{niche}.json",
                "colors": {
                    "50":  "#fafafa",
                    "100": "#f4f4f5",
                    "200": "#e4e4e7",
                    "300": "#d4d4d8",
                    "400": "#a1a1aa",
                    "500": "#71717a",
                    "600": "#52525b",
                    "700": "#3f3f46",
                    "800": "#27272a",
                    "900": "#18181b",
                    "shadow": "rgba(82,82,91,0.30)",
                    "shadow_hover": "rgba(82,82,91,0.45)",
                },
                "section_order": [
                    ["reassurance", "prices", "services", "faq"],
                    ["prices", "reassurance", "services", "faq"],
                    ["reassurance", "services", "faq", "prices"],
                    ["services", "reassurance", "prices", "faq"],
                ],
            },
            "content": {
                "intro_spintax": (
                    f"{{Besoin d'un {svc(0)['label_fr'].lower()} a {{ville}} ?|"
                    f"Vous cherchez un entrepreneur pour {svc(0)['label_fr'].lower()} a {{ville}} ?|"
                    f"Comparez les prix de {svc(0)['label_fr'].lower()} a {{ville}} avec des soumissions gratuites.}}"
                ),
                "services": [
                    {
                        "icon": ["home", "star", "tool", "shield", "check", "bolt"][i % 6],
                        "title": svc(i)["label_fr"],
                        "description": svc(i)["description"],
                    }
                    for i in range(min(6, len(services)))
                ],
                "prices_display": {
                    "intro": f"Prix {niche.replace('-', ' ')} a {{ville}} en {{year}}",
                    "main_cards": [
                        {"label": svc(0)["label_fr"], "key_min": "service1_min", "key_max": "service1_max", "icon": "home", "popular": True},
                        {"label": svc(1)["label_fr"], "key_min": "service2_min", "key_max": "service2_max", "icon": "star"},
                        {"label": svc(2)["label_fr"], "key_min": "service3_min", "key_max": "service3_max", "icon": "tool"},
                    ],
                    "secondary_cards": [
                        {"label": svc(3)["label_fr"], "key_min": "service4_min", "key_max": "service4_max", "icon": "shield"},
                    ],
                },
                "faq": [
                    {"q": q, "a": ""}
                    for q in rs.get("faq_questions", [])[:6]
                ],
            },
            "form": {
                "title": f"Obtenez vos soumissions {niche.replace('-', ' ')} gratuitement",
                "subtitle": "Comparez 3 entrepreneurs certifies RBQ — gratuit et sans engagement",
                "steps": [],
            },
            "network": {
                "premium_cities": ["montreal", "quebec", "laval", "longueuil", "sherbrooke"],
                "sister_sites": [],
            },
        }

        config_path = ENGINE_QC / f"config_{niche}.json"
        config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  Config draft : {config_path.name}")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print(f"\n{'='*60}")
    print(f"TERMINE : {niche}")
    print(f"  niche_research_{niche}.json — recherche complete + prompts")
    if "price_tiers" in research:
        print(f"  config_{niche}.json        — config draft (a reviser couleurs, SEO, form)")
        if "research_summary" in research:
            rs = research["research_summary"]
            print(f"\nServices detectes :")
            for s in rs.get("services", []):
                print(f"  {s['id']}: {s['label_fr']} ({s.get('price_min_gv',0)}-{s.get('price_max_gv',0)}$)")
            print(f"\nMarques : {', '.join(rs.get('brands', []))}")
            print(f"Top keywords : {', '.join(rs.get('top_keywords', [])[:5])}")

    print(f"\nProchaines etapes :")
    print(f"  1. Reviser engine_qc/config_{niche}.json (couleurs, form, SEO)")
    print(f"  2. python tools/fetch_regional_context.py --niche {niche}")
    print(f"  3. python tools/generate_city_content.py --niche {niche} --workers 5")
    print(f"  4. python engine_qc/EmpireGenerator.py --config engine_qc/config_{niche}.json")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
