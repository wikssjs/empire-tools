#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_gemini_vs_haiku.py — Compare Gemini Flash 2.0 vs Claude Haiku for chauffage city content
Génère 5 villes avec chaque modèle et produit un HTML de comparaison.

Usage: python tools/test_gemini_vs_haiku.py
Output: tools/comparison_output.html
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import json, os, re, csv, time, urllib.request, urllib.error
from pathlib import Path
import anthropic

BASE = Path(__file__).parent.parent

GEMINI_KEY = "AIzaSyCSTSlGdpD9wLN93_fe2GYVRFnluJ4uoz8"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")

# 5 villes variées (grande / moyenne / petite / village + une insulaire)
TEST_CITIES = [
    {"ville": "Montréal",    "region": "Montréal",         "population": 1762949},
    {"ville": "Sherbrooke",  "region": "Estrie",           "population": 172950},
    {"ville": "Drummondville","region": "Centre-du-Québec", "population": 82500},
    {"ville": "Coaticook",   "region": "Estrie",           "population": 9500},
    {"ville": "Sainte-Anne-des-Monts", "region": "Gaspésie", "population": 7000},
]

def slugify(s):
    import unicodedata
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower().replace(" ", "-").replace("'", "-").replace("'", "-")
    s = re.sub(r"[^a-z0-9-]", "", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s

def load_regional_context():
    path = BASE / "engine_qc" / "regional_context_chauffage.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}

def build_prices(pop):
    if pop >= 50000:
        return {"service1_min": 4500, "service1_max": 16000, "service2_min": 3000, "service2_max": 12000,
                "service3_min": 2500, "service3_max": 9000,  "service4_min": 1800, "service4_max": 7000}
    elif pop >= 15000:
        return {"service1_min": 3690, "service1_max": 13120, "service2_min": 2460, "service2_max": 9840,
                "service3_min": 2050, "service3_max": 7380,  "service4_min": 1476, "service4_max": 5740}
    elif pop >= 5000:
        return {"service1_min": 3150, "service1_max": 11200, "service2_min": 2100, "service2_max": 8400,
                "service3_min": 1750, "service3_max": 6300,  "service4_min": 1260, "service4_max": 4900}
    else:
        return {"service1_min": 2610, "service1_max": 9280, "service2_min": 1739, "service2_max": 6959,
                "service3_min": 1450, "service3_max": 5220,  "service4_min": 1044, "service4_max": 4059}

SYSTEM_PROMPT = (
    "Tu es un rédacteur web spécialisé en chauffage résidentiel au Québec. "
    "Tu écris des textes HTML complets, précis et convaincants pour des pages locales de chauffage. "
    "Tu maîtrises les systèmes (thermopompes, fournaises, chauffage radiant), les programmes de subvention "
    "(Rénoclimat, LogisVert, RCEE) et les spécificités régionales québécoises."
)

USER_PROMPT_TEMPLATE = """\
Écris un bloc de contenu HTML pour la page "chauffage à {ville}" ({region}, Québec).

Contexte régional : {context}

Prix de référence pour {ville} :
- Thermopompe murale (installation complète, mural ou mini-split) : {service1_min}$ – {service1_max}$
- Remplacement fournaise (gaz, propane ou électrique, installation incluse) : {service2_min}$ – {service2_max}$
- Chauffage radiant (plancher chauffant, eau ou électrique, par pièce) : {service3_min}$ – {service3_max}$
- Entretien annuel système de chauffage (contrat, nettoyage, vérification) : {service4_min}$ – {service4_max}$

STRUCTURE OBLIGATOIRE — génère ces 6 sections dans l'ordre exact :

---
SECTION 1 — Tableau comparatif des systèmes de chauffage à {ville}
<h2 class="text-3xl font-bold mb-4">[Titre accrocheur sur le choix de chauffage à {ville}]</h2>
Suivi d'un <p> de 180-220 mots sur le profil de chauffage de {region} : mix énergétique, rigueur des hivers, tendance vers les thermopompes, proportion de maisons avec fournaise centrale vs plinthes. Intègre les données chiffrées du contexte régional.
Suivi d'un tableau HTML COMPLET : Système | Prix à {ville} | Coût annuel moyen | Durée de vie | Subvention dispo | Idéal pour
Lignes : Thermopompe murale (mini-split) / Thermopompe centrale (sur conduits) / Fournaise au gaz naturel / Fournaise électrique / Chauffage radiant plancher / Plinthes électriques
Classes tableau : <table class="w-full text-sm border-collapse mt-6 mb-2"> <thead style="background:#ea580c;color:#fff"> <th class="px-4 py-3 text-left font-semibold"> <tbody> <tr class="border-b border-gray-200 hover:bg-gray-50"> <td class="px-4 py-3">

---
SECTION 2 — Facteurs qui font varier le prix du chauffage à {ville}
<h2> accrocheur ancré dans {ville} ou {region}
<p> de 180-220 mots : superficie, isolation, type de distribution, marque et efficacité (SEER, HSPF), coût main-d'oeuvre dans {region}, coût mise à niveau électrique. Pour les chiffres clés, utilise <strong class="text-orange-600">X $</strong>.
Suivi d'un tableau (thead style="background:#ea580c;color:#fff") : Facteur | Impact sur le prix | Détail pour {ville}
Lignes : Superficie (pi²) / Isolation de l'enveloppe / Maison avec conduits existants / Mise à niveau électrique requise / Urgence vs planifié / Haute saison (sept-nov) / Marque et efficacité SEER/HSPF

---
SECTION 3 — Thermopompe vs Fournaise : quel système choisir à {ville}
<h2> original mentionnant {region} ou le climat de {ville}
<p> de 200-250 mots : thermopompe air-air, fournaise électrique, fournaise gaz/propane, thermopompe centrale. Mets les prix en <strong class="text-orange-600">X $</strong>.
Suivi d'un tableau (thead style="background:#ea580c;color:#fff") : Critère | Thermopompe murale | Thermopompe centrale | Fournaise électrique | Fournaise gaz/propane
Lignes : Prix à {ville} | Coût annuel moyen | Subvention disponible | Double usage clim/chauffage | Nécessite conduits | Performance sous -20°C | Durée de vie | Entretien annuel

---
SECTION 4 — Subventions et programmes d'aide au chauffage à {ville}
<h2> direct et rassurant
<p> de 200-250 mots : Rénoclimat, LogisVert Hydro-Québec, RCEE fédéral, crédits d'impôt, cumul maximal possible. Pour les montants, utilise <strong class="text-orange-600">X $</strong>.
Suivi d'un tableau (thead style="background:#ea580c;color:#fff") : Programme | Montant disponible | Conditions | Cumulable avec
Lignes : Rénoclimat — thermopompe centrale / Rénoclimat — thermopompe murale / LogisVert Hydro-Québec / RCEE fédéral / Crédit d'impôt provincial / Programme municipal (si applicable)

---
SECTION 5 — Choisir son entrepreneur en chauffage à {ville}
<h2> pratique et local
<p> de 200-250 mots : certification RBQ, calcul de charge thermique, ce que le devis doit inclure, délais dans {region}, comparaison 3 soumissions, garanties.
Suivi d'un tableau (thead style="background:#ea580c;color:#fff") : Critère | Ce qu'il faut vérifier | Pourquoi c'est important
Lignes : Licence RBQ 15.10 ou 16 / Calcul de charge BTU fourni / Retrait ancien équipement inclus / Raccordement électrique inclus / Garantie main-d'oeuvre / Délai de livraison confirmé / Références locales à {ville}

---
SECTION 6 — FAQ : Chauffage à {ville}
<h2 class="text-3xl font-bold mb-8">Questions fréquentes sur le chauffage à {ville}</h2>
Génère 6 questions-réponses en accordéon HTML avec ces classes exactes :
<details class="group bg-white rounded-xl border border-gray-200 overflow-hidden mb-3">
<summary class="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50">
<span class="font-semibold text-gray-900 pr-4">QUESTION ICI</span>
<svg class="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
</summary>
<div class="px-6 pb-6 text-gray-600 leading-relaxed">RÉPONSE ICI (100-130 mots, précise, avec données locales)</div>
</details>

Questions : 1) Coût thermopompe installée à {ville} 2) Thermopompe ou fournaise pour le climat de {region} 3) Subventions pour remplacer le système de chauffage 4) Quand remplacer sa fournaise/thermopompe 5) Coût urgence chauffage en hiver 6) Permis requis pour installation

---

RÈGLES ABSOLUES :
- Réponds UNIQUEMENT avec le HTML brut, aucun commentaire avant ou après
- NE génère PAS de wrapper extérieur <div> ou <section> global
- Pour le texte courant utilise text-gray-900 (titres/spans), text-gray-600 (corps FAQ) — pour les prix utilise <strong class="text-orange-600">X $</strong>
- Mentionne {ville} et {region} naturellement dans chaque section
- Aucune liste à puces <ul><li> — uniquement <p>, tableaux et accordéons
"""

def call_haiku(system, user_prompt):
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=16000,
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return msg.content[0].text.strip()

def call_gemini_flash(system, user_prompt):
    payload = json.dumps({
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {"maxOutputTokens": 16000, "temperature": 0.7}
    }).encode("utf-8")
    req = urllib.request.Request(
        GEMINI_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()

def clean_html(text):
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()

def count_chars(text):
    return len(text)

def count_tables(text):
    return text.lower().count("<table")

def count_sections(text):
    return text.lower().count("<h2")

def build_comparison_html(results):
    rows = ""
    for entry in results:
        city_name, haiku_html, gemini_html, gpt_html, gpt55_html = entry
        stats = {
            "Haiku": (count_chars(haiku_html), count_tables(haiku_html), count_sections(haiku_html)),
            "Gemini": (count_chars(gemini_html), count_tables(gemini_html), count_sections(gemini_html)),
            "GPT-4.1m": (count_chars(gpt_html), count_tables(gpt_html), count_sections(gpt_html)),
            "GPT-5.5": (count_chars(gpt55_html), count_tables(gpt55_html), count_sections(gpt55_html)),
        }
        stat_str = " &nbsp;|&nbsp; ".join(f"{k}: {v[0]:,}c·{v[1]}t·{v[2]}h2" for k, v in stats.items())
        rows += f"""
        <tr style="background:#f8fafc">
            <td colspan="4" style="padding:12px 16px;font-weight:700;font-size:16px;border-top:3px solid #ea580c">
                {city_name}
                <span style="font-weight:400;font-size:11px;color:#64748b;margin-left:12px">{stat_str}</span>
            </td>
        </tr>
        <tr>
            <td style="width:25%;padding:10px;vertical-align:top;border-right:2px solid #e2e8f0">
                <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;font-weight:600;margin-bottom:6px">Claude Haiku 4.5</div>
                <div style="font-size:11px;line-height:1.6;max-height:600px;overflow-y:auto;border:1px solid #e2e8f0;padding:8px;border-radius:6px;background:#fff">
                    {haiku_html}
                </div>
            </td>
            <td style="width:25%;padding:10px;vertical-align:top;border-right:2px solid #e2e8f0">
                <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;font-weight:600;margin-bottom:6px">Gemini 2.5 Flash</div>
                <div style="font-size:11px;line-height:1.6;max-height:600px;overflow-y:auto;border:1px solid #e2e8f0;padding:8px;border-radius:6px;background:#fff">
                    {gemini_html}
                </div>
            </td>
            <td style="width:25%;padding:10px;vertical-align:top;border-right:2px solid #e2e8f0">
                <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;font-weight:600;margin-bottom:6px">GPT-4.1 mini</div>
                <div style="font-size:11px;line-height:1.6;max-height:600px;overflow-y:auto;border:1px solid #e2e8f0;padding:8px;border-radius:6px;background:#fff">
                    {gpt_html}
                </div>
            </td>
            <td style="width:25%;padding:10px;vertical-align:top">
                <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;font-weight:600;margin-bottom:6px">GPT-5.4 nano</div>
                <div style="font-size:11px;line-height:1.6;max-height:600px;overflow-y:auto;border:1px solid #e2e8f0;padding:8px;border-radius:6px;background:#fff">
                    {gpt55_html}
                </div>
            </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Comparaison Haiku vs Gemini Flash — Chauffage</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 0; padding: 20px; background: #f1f5f9; }}
  h1 {{ font-size: 24px; margin-bottom: 4px; }}
  .subtitle {{ color: #64748b; font-size: 14px; margin-bottom: 24px; }}
  table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,.1); margin-bottom: 8px; }}
  td {{ border: 1px solid #e2e8f0; }}
  .header-row td {{ padding: 12px 16px; background: #0f172a; color: white; font-weight: 600; font-size: 15px; }}
  /* Render table classes from the content */
  .w-full {{ width: 100%; }}
  .text-sm {{ font-size: 12px; }}
  .border-collapse {{ border-collapse: collapse; }}
  .mt-6 {{ margin-top: 16px; }}
  .mb-2 {{ margin-bottom: 6px; }}
  .px-4 {{ padding-left: 12px; padding-right: 12px; }}
  .py-3 {{ padding-top: 8px; padding-bottom: 8px; }}
  .text-left {{ text-align: left; }}
  .font-semibold {{ font-weight: 600; }}
  .border-b {{ border-bottom: 1px solid #e2e8f0; }}
  .text-orange-600 {{ color: #ea580c; }}
  .text-gray-900 {{ color: #111827; }}
  .text-gray-600 {{ color: #4b5563; }}
  .text-gray-500 {{ color: #6b7280; }}
  .font-bold {{ font-weight: 700; }}
  .leading-relaxed {{ line-height: 1.6; }}
  .rounded-xl {{ border-radius: 12px; }}
  .bg-white {{ background: white; }}
  .overflow-hidden {{ overflow: hidden; }}
  .mb-3 {{ margin-bottom: 8px; }}
  .p-6 {{ padding: 20px; }}
  .cursor-pointer {{ cursor: pointer; }}
  .px-6 {{ padding-left: 20px; padding-right: 20px; }}
  .pb-6 {{ padding-bottom: 20px; }}
  .pr-4 {{ padding-right: 12px; }}
  .items-center {{ align-items: center; }}
  .justify-between {{ justify-content: space-between; }}
  .flex {{ display: flex; }}
  details summary {{ list-style: none; }}
  details[open] .group-open\\:rotate-180 {{ transform: rotate(180deg); }}
  .transition-transform {{ transition: transform 0.2s; }}
  h2 {{ font-size: 18px; font-weight: 700; margin: 20px 0 8px; color: #0f172a; }}
  p {{ margin: 8px 0; color: #374151; }}
  strong {{ font-weight: 600; }}
</style>
</head>
<body>
<h1>Comparaison Haiku 4.5 vs Gemini Flash 2.0</h1>
<p class="subtitle">Niche : chauffage · 5 villes de test · {__import__('datetime').date.today()}</p>
<table>
  <tr class="header-row">
    <td>Claude Haiku 4.5</td>
    <td>Gemini 2.5 Flash</td>
    <td>GPT-4.1 mini</td>
    <td>GPT-5.4 nano</td>
  </tr>
  {rows}
</table>
</body>
</html>"""

def call_gpt(system, user_prompt, model="gpt-4.1-mini"):
    tokens_key = "max_completion_tokens" if model.startswith("gpt-5.4") or model.startswith("gpt-5.5") else "max_tokens"
    payload = json.dumps({
        "model": model,
        tokens_key: 16000,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt}
        ]
    }).encode("utf-8")
    req = urllib.request.Request(
        OPENAI_URL,
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_KEY}"},
        method="POST"
    )
    timeout = 300 if model.startswith("gpt-5.5") else 120
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        raise Exception(f"HTTP {e.code}: {body[:300]}")

CACHE_PATH = BASE / "tools" / "comparison_cache.json"

def load_cache():
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}

def save_cache(cache):
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

def main():
    regional_context = load_regional_context()
    cache = load_cache()
    results = []

    for city in TEST_CITIES:
        ville = city["ville"]
        region = city["region"]
        pop = city["population"]
        context = regional_context.get(region, "Région du Québec.")
        context = context.split("---PRIX---", 1)[0].strip() if "---PRIX---" in context else context
        prices = build_prices(pop)

        user_prompt = USER_PROMPT_TEMPLATE.format(
            ville=ville, region=region, context=context, **prices
        )

        # Haiku — charge depuis cache si dispo
        if ville in cache and "haiku" in cache[ville]:
            haiku_out = cache[ville]["haiku"]
            print(f"\n[{ville}] → Haiku: cache ✓ ({len(haiku_out):,} chars)")
        else:
            print(f"\n[{ville}] → Haiku...", end=" ", flush=True)
            try:
                haiku_out = clean_html(call_haiku(SYSTEM_PROMPT, user_prompt))
                print(f"{len(haiku_out):,} chars ✓")
                cache.setdefault(ville, {})["haiku"] = haiku_out
                save_cache(cache)
            except Exception as e:
                haiku_out = f"<p>ERREUR Haiku: {e}</p>"
                print(f"ERREUR: {e}")
            time.sleep(1)

        # Gemini — charge depuis cache si dispo
        if ville in cache and "gemini" in cache[ville]:
            gemini_out = cache[ville]["gemini"]
            print(f"[{ville}] → Gemini: cache ✓ ({len(gemini_out):,} chars)")
        else:
            print(f"[{ville}] → Gemini Flash...", end=" ", flush=True)
            try:
                gemini_out = clean_html(call_gemini_flash(SYSTEM_PROMPT, user_prompt))
                print(f"{len(gemini_out):,} chars ✓")
                cache.setdefault(ville, {})["gemini"] = gemini_out
                save_cache(cache)
            except Exception as e:
                gemini_out = f"<p>ERREUR Gemini: {e}</p>"
                print(f"ERREUR: {e}")
            time.sleep(1)

        # GPT-4.1 mini
        if ville in cache and "gpt" in cache[ville]:
            gpt_out = cache[ville]["gpt"]
            print(f"[{ville}] → GPT-4.1 mini: cache ✓ ({len(gpt_out):,} chars)")
        else:
            print(f"[{ville}] → GPT-4.1 mini...", end=" ", flush=True)
            try:
                gpt_out = clean_html(call_gpt(SYSTEM_PROMPT, user_prompt, "gpt-4.1-mini"))
                print(f"{len(gpt_out):,} chars ✓")
                cache.setdefault(ville, {})["gpt"] = gpt_out
                save_cache(cache)
            except Exception as e:
                gpt_out = f"<p>ERREUR GPT: {e}</p>"
                print(f"ERREUR: {e}")
            time.sleep(1)

        # GPT-5.4 nano
        if ville in cache and "gpt54nano" in cache[ville]:
            gpt55_out = cache[ville]["gpt54nano"]
            print(f"[{ville}] → GPT-5.4 nano: cache ✓ ({len(gpt55_out):,} chars)")
        else:
            print(f"[{ville}] → GPT-5.4 nano...", end=" ", flush=True)
            try:
                gpt55_out = clean_html(call_gpt(SYSTEM_PROMPT, user_prompt, "gpt-5.4-nano"))
                print(f"{len(gpt55_out):,} chars ✓")
                cache.setdefault(ville, {})["gpt54nano"] = gpt55_out
                save_cache(cache)
            except Exception as e:
                gpt55_out = f"<p>ERREUR GPT-5.4-nano: {e}</p>"
                print(f"ERREUR: {e}")
            time.sleep(1)

        results.append((ville, haiku_out, gemini_out, gpt_out, gpt55_out))
        time.sleep(1)

    out_path = BASE / "tools" / "comparison_output.html"
    out_path.write_text(build_comparison_html(results), encoding="utf-8")
    print(f"\n✓ Comparaison sauvegardée : {out_path}")

if __name__ == "__main__":
    main()
