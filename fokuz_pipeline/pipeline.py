#!/usr/bin/env python3
"""
Fokuz Content Pipeline — A/B Test Sonnet vs GPT-5.5
5 phases: Research (Perplexity) → Synthesis → Auto-Prompt → Write x2 → Score

Usage:
    python pipeline.py "entretien de toiture"
    python pipeline.py "émondage arbre" --test-models
"""

import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')
import json
import argparse
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
import anthropic
from openai import OpenAI

load_dotenv(Path(__file__).parent / ".env", override=True)

# ─── Model IDs ────────────────────────────────────────────────────────────────
PERPLEXITY_MODEL = "sonar-pro"               # Research web search
SYNTHESIS_MODEL  = "gpt-5.4-nano"            # Phase 2: cheap synthesis
PROMPTGEN_MODEL  = "gpt-5.4-mini"            # Phase 3: prompt generation
WRITE_CLAUDE     = "claude-sonnet-4-6"       # Phase 4A
WRITE_GPT        = "gpt-5.4"                 # Phase 4B (gpt-5.5 = reasoning-only, pas de content generation)
QA_MODEL         = "claude-haiku-4-5-20251001"  # Phase 5: scorer

# ─── Clients ──────────────────────────────────────────────────────────────────
claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
gpt    = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pplx   = OpenAI(
    api_key=os.getenv("PERPLEXITY_API_KEY"),
    base_url="https://api.perplexity.ai"
)

# ─── Money Sites par niche ────────────────────────────────────────────────────
MONEY_SITES = [
    {"keywords": ["toiture", "toit", "bardeau", "couvreur", "toits plats", "toiture plate"],
     "site": "https://prix-toiture.ca", "site_name": "prix-toiture.ca"},
    {"keywords": ["thermopompe", "climatiseur", "climatisation", "chauffage", "pompe à chaleur"],
     "site": "https://prix-thermopompe.ca", "site_name": "prix-thermopompe.ca"},
    {"keywords": ["excavation", "terrassement"],
     "site": "https://experts-excavation.ca", "site_name": "experts-excavation.ca"},
    {"keywords": ["gouttière", "gouttieres", "gouttières"],
     "site": "https://prix-gouttieres.ca", "site_name": "prix-gouttieres.ca"},
    {"keywords": ["fissure", "fondation", "fissures", "sous-oeuvre", "sous-œuvre"],
     "site": "https://prix-fissure.ca", "site_name": "prix-fissure.ca"},
    {"keywords": ["isolation", "isolant", "soufflage"],
     "site": "https://prix-isolation.ca", "site_name": "prix-isolation.ca"},
    {"keywords": ["peinture", "peintres", "peintre"],
     "site": "https://prix-peinture.ca", "site_name": "prix-peinture.ca"},
    {"keywords": ["drain", "drainage", "drain français"],
     "site": "https://prix-drain.ca", "site_name": "prix-drain.ca"},
    {"keywords": ["piscine", "spa", "bain tourbillon"],
     "site": "https://expertpiscine.ca", "site_name": "expertpiscine.ca"},
    {"keywords": ["paysagement", "aménagement paysager", "gazon", "pelouse"],
     "site": "https://prix-paysagement.ca", "site_name": "prix-paysagement.ca"},
    {"keywords": ["déménagement", "demenagement", "déménageurs"],
     "site": "https://comparateur-demenageurs.ca", "site_name": "comparateur-demenageurs.ca"},
    {"keywords": ["plancher", "parquet", "planchers", "revêtement de sol"],
     "site": "https://soumission-plancher.ca", "site_name": "soumission-plancher.ca"},
    {"keywords": ["électricien", "electricien", "électricité", "panneau électrique"],
     "site": "https://prix-electricien.ca", "site_name": "prix-electricien.ca"},
    {"keywords": ["sous-sol", "soussol", "basement"],
     "site": "https://prix-soussol.ca", "site_name": "prix-soussol.ca"},
    {"keywords": ["fenêtre", "fenetres", "fenêtres", "portes et fenêtres"],
     "site": "https://soumission-fenetres.ca", "site_name": "soumission-fenetres.ca"},
    {"keywords": ["cuisine", "armoire", "comptoir", "ilot"],
     "site": "https://prix-cuisine.ca", "site_name": "prix-cuisine.ca"},
    {"keywords": ["salle de bain", "salle de bains", "salledebain", "douche", "bain"],
     "site": "https://soumission-salledebain.ca", "site_name": "soumission-salledebain.ca"},
    {"keywords": ["plombier", "plomberie", "tuyauterie"],
     "site": "https://soumission-plombier.ca", "site_name": "soumission-plombier.ca"},
    {"keywords": ["pavage", "asphalte", "entrée de cour"],
     "site": "https://prixpavage.ca", "site_name": "prixpavage.ca"},
    {"keywords": ["revêtement extérieur", "revetement", "bardeau de vinyle", "aluminium"],
     "site": "https://prix-revetement.ca", "site_name": "prix-revetement.ca"},
    {"keywords": ["émondage", "emondage", "élagage", "arbre", "arbres"],
     "site": "https://prix-emondage.ca", "site_name": "prix-emondage.ca"},
    {"keywords": ["extermination", "parasites", "coquerelles", "souris", "vermines"],
     "site": "https://prixextermination.ca", "site_name": "prixextermination.ca"},
    {"keywords": ["décontamination", "moisissures", "amiante", "pyrite"],
     "site": "https://experts-decontamination.ca", "site_name": "experts-decontamination.ca"},
    {"keywords": ["maçonnerie", "maconnerie", "brique", "pierre", "mortier"],
     "site": "https://experts-maconnerie.ca", "site_name": "experts-maconnerie.ca"},
    {"keywords": ["fosse septique", "fosseseptique", "fosse"],
     "site": "https://experts-fosseseptique.ca", "site_name": "experts-fosseseptique.ca"},
    {"keywords": ["calfeutrage", "calfeutrer", "scellant"],
     "site": "https://expertcalfeutrage.ca", "site_name": "expertcalfeutrage.ca"},
    {"keywords": ["clôture", "cloture", "clôtures"],
     "site": "https://soumission-cloture.ca", "site_name": "soumission-cloture.ca"},
]

def detect_money_site(sujet: str) -> dict | None:
    """Détecte le money site selon les mots-clés du sujet."""
    sujet_lower = sujet.lower()
    for entry in MONEY_SITES:
        for kw in entry["keywords"]:
            if kw.lower() in sujet_lower:
                return entry
    return None


# ─── Style Guide Fokuz ────────────────────────────────────────────────────────
STYLE_GUIDE = """
STYLE GUIDE FOKUZ — Règles absolues

VOIX : Direct, tutoie le lecteur, jamais condescendant.
TON : Journaliste d'enquête bienveillant. Tu as une opinion. Tu la dis.
INTERDIT ABSOLU : "il est important de", "n'hésitez pas", "en conclusion",
                  "en résumé", "il convient de", "cela", commencer par "Il"
OBLIGATOIRE :
  - Une stat ou paradoxe en hook (première phrase)
  - Au moins 2 chiffres avec source entre parenthèses ex: (CCQ, 2026)
  - Un paragraphe qui contredit ce que le lecteur croit déjà
  - Une prise de position tranchée — pas "d'un côté... de l'autre"
  - Varier longueur des phrases: courtes pour l'impact, longues pour l'explication
STRUCTURE : Hook choc → contexte rapide → données réelles → pièges → comment faire → CTA contextuel
LONGUEUR : 1800-2200 mots
LIENS : Le lien vers le money site est DANS le texte, pas en CTA isolé en fin d'article
"""

# ─── Phase 1: Research ────────────────────────────────────────────────────────
def phase1_research(sujet: str) -> tuple[str, list]:
    print(f"\n{'─'*50}")
    print("[Phase 1] Research Perplexity Sonar Pro")
    print(f"{'─'*50}")

    queries = [
        f"{sujet} prix marché Québec 2026 par région données officielles",
        f"{sujet} erreurs courantes propriétaires québécois problèmes fréquents",
        f"{sujet} réglementation RBQ CCQ obligations légales licences",
        f"{sujet} arnaques fraudeurs signes avertissement comment se protéger Québec",
        f"{sujet} comment choisir entrepreneur critères vérifications soumissions",
    ]

    corpus_parts = []
    all_sources = []

    for i, query in enumerate(queries, 1):
        print(f"  [{i}/{len(queries)}] {query[:70]}...")
        try:
            resp = pplx.chat.completions.create(
                model=PERPLEXITY_MODEL,
                messages=[
                    {"role": "system", "content": "Assistant de recherche. Réponds en français avec données précises et sources."},
                    {"role": "user", "content": query}
                ],
                max_tokens=900
            )
            text = resp.choices[0].message.content
            corpus_parts.append(f"### Recherche {i}: {query}\n{text}\n")

            if hasattr(resp, "citations") and resp.citations:
                all_sources.extend(resp.citations)
                print(f"     → {len(resp.citations)} sources trouvées")
            else:
                print(f"     → {len(text.split())} mots")

        except Exception as e:
            print(f"     ✗ Erreur: {e}")

        time.sleep(0.8)

    corpus = "\n".join(corpus_parts)
    print(f"\n  Corpus total: {len(corpus)} chars | {len(all_sources)} sources")
    return corpus, all_sources


# ─── Phase 2: Synthesis ───────────────────────────────────────────────────────
def phase2_synthesis(sujet: str, corpus: str) -> dict:
    print(f"\n{'─'*50}")
    print(f"[Phase 2] Synthesis + Angle ({SYNTHESIS_MODEL})")
    print(f"{'─'*50}")

    # Prompt volontairement court pour éviter JSON tronqué
    prompt = f"""Tu es chef de pupitre. Sujet: "{sujet}"

Recherches (extrait):
{corpus[:3000]}

JSON court et valide UNIQUEMENT (valeurs courtes, max 120 chars chacune):
{{
  "insight_principal": "...",
  "angle_recommande": "...",
  "donnee_choc": "...",
  "idee_contrarienne": "...",
  "prix_reels": "...",
  "pieges_top3": ["...", "...", "..."],
  "sources_autorite": ["url1", "url2"],
  "ton": "journaliste_enquete"
}}"""

    for attempt in range(2):
        try:
            resp = gpt.chat.completions.create(
                model=SYNTHESIS_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=600,
                response_format={"type": "json_object"}
            )
            raw = resp.choices[0].message.content or ""
            # Repair truncated JSON: find last complete field
            if raw and not raw.strip().endswith("}"):
                last_comma = raw.rfind(",")
                if last_comma > 0:
                    raw = raw[:last_comma] + "\n}"
            brief = json.loads(raw)
            print(f"  Angle: {brief.get('angle_recommande', '?')[:80]}")
            print(f"  Insight: {brief.get('insight_principal', '?')[:80]}")
            return brief
        except Exception as e:
            print(f"  Tentative {attempt+1} echouee: {e}")

    print("  Fallback generique")
    return {
        "angle_recommande": f"Ce que personne ne dit sur le {sujet} au Quebec",
        "insight_principal": "Les prix varient du simple au triple selon la region",
        "idee_contrarienne": "Un toit recent n'est pas un toit bien entretenu",
        "ton": "journaliste_enquete"
    }


# ─── Phase 3: Auto-Prompt Generation ─────────────────────────────────────────
def phase3_prompt_gen(sujet: str, brief: dict, corpus: str, sources: list, money_site: dict | None = None) -> str:
    print(f"\n{'─'*50}")
    print(f"[Phase 3] Génération prompt optimal ({PROMPTGEN_MODEL})")
    print(f"{'─'*50}")

    sources_block = "\n".join(f"- {s}" for s in sources[:10]) if sources else "(aucune URL disponible)"

    cta_instruction = ""
    if money_site:
        cta_instruction = f"""
7. CTA naturel obligatoire : dans la section sur "comment obtenir des soumissions" ou "comment choisir un entrepreneur", intégrer UNE mention naturelle de [{money_site['site_name']}]({money_site['site']}) — pas en fin d'article isolée, DANS le texte d'un paragraphe pertinent. L'article doit aussi citer 2-3 sources externes réelles (guides de prix, organismes QC) pour crédibilité."""

    meta = f"""Expert en prompting pour rédaction SEO journalistique québécoise.

Sujet: {sujet}
Brief éditorial: {json.dumps(brief, ensure_ascii=False)}
Données disponibles (extrait): {corpus[:1800]}
URLs sources réelles à citer dans l'article:
{sources_block}

Style guide:
{STYLE_GUIDE}

Génère le prompt parfait pour écrire un article de MINIMUM 2000 mots (idéalement 2100-2300).
L'article doit ressembler à celui d'un rédacteur ayant passé 3-4 semaines de recherches terrain.

Le prompt DOIT inclure:
1. Identité du rédacteur (prénom QC, expertise spécifique, villes visitées ou consultées)
2. Structure section par section (hook, 5-6 H2, opinion finale)
3. Instruction de citer AU MOINS 2 des URLs sources listées ci-dessus avec leur nom de domaine
4. Angle imposé: {brief.get('angle_recommande', '')}
5. 3 choses INTERDITES dans cet article
6. Rappel explicite: "l'article doit faire MINIMUM 2000 mots — ne jamais s'arrêter avant"{cta_instruction}

Retourne UNIQUEMENT le prompt de rédaction, rien d'autre."""

    try:
        resp = gpt.chat.completions.create(
            model=PROMPTGEN_MODEL,
            messages=[{"role": "user", "content": meta}],
            max_completion_tokens=1000
        )
        writing_prompt = resp.choices[0].message.content.strip()
        print(f"  Prompt généré: {len(writing_prompt)} chars")
        return writing_prompt

    except Exception as e:
        print(f"  ✗ Erreur prompt gen ({e}) — fallback basique")
        return f"Écris un article complet et expert sur '{sujet}' au Québec en 2026. {STYLE_GUIDE}"


# ─── Phase 4: A/B Writing ─────────────────────────────────────────────────────
def phase4a_claude(writing_prompt: str, corpus: str, sources: list, money_site: dict | None = None) -> tuple[str, float]:
    print(f"\n{'─'*50}")
    print(f"[Phase 4A] Rédaction Claude Sonnet ({WRITE_CLAUDE})")
    print(f"{'─'*50}")
    t0 = time.time()

    sources_block = "\n".join(f"- {s}" for s in sources[:12]) if sources else ""
    cta_block = ""
    if money_site:
        cta_block = (
            f"\nCTA OBLIGATOIRE : Dans la section sur les soumissions ou le choix d'entrepreneur, "
            f"intègre naturellement ce lien dans le texte (pas en fin d'article isolé) : "
            f"[{money_site['site_name']}]({money_site['site']})\n"
        )
    full = (
        f"{writing_prompt}\n\n"
        f"RAPPEL LONGUEUR : minimum 2000 mots, ne t'arrête pas avant.\n"
        f"{cta_block}"
        f"---\nSOURCES RÉELLES À CITER (utilise au moins 2 URLs):\n{sources_block}\n\n"
        f"DONNÉES DE RECHERCHE:\n{corpus[:4000]}"
    )

    try:
        resp = claude.messages.create(
            model=WRITE_CLAUDE,
            max_tokens=16000,
            system=STYLE_GUIDE,
            messages=[{"role": "user", "content": full}]
        )
        text = resp.content[0].text
        elapsed = time.time() - t0
        words = len(text.split())
        print(f"  OK {words} mots en {elapsed:.1f}s")
        return text, elapsed

    except Exception as e:
        elapsed = time.time() - t0
        print(f"  FAIL Erreur Claude: {e}")
        return f"[ERREUR Claude: {e}]", elapsed


def phase4b_gpt(writing_prompt: str, corpus: str, sources: list, money_site: dict | None = None) -> tuple[str, float]:
    print(f"\n{'─'*50}")
    print(f"[Phase 4B] Redaction GPT-5.4 ({WRITE_GPT})")
    print(f"{'─'*50}")
    t0 = time.time()

    sources_block = "\n".join(f"- {s}" for s in sources[:12]) if sources else ""
    cta_block = ""
    if money_site:
        cta_block = (
            f"\nCTA OBLIGATOIRE : Dans la section sur les soumissions ou le choix d'entrepreneur, "
            f"intègre naturellement ce lien dans le texte (pas en fin d'article isolé) : "
            f"[{money_site['site_name']}]({money_site['site']})\n"
        )
    full = (
        f"{writing_prompt}\n\n"
        f"RAPPEL LONGUEUR : minimum 2000 mots, ne t'arrête pas avant.\n"
        f"{cta_block}"
        f"---\nSOURCES RÉELLES À CITER (utilise au moins 2 URLs):\n{sources_block}\n\n"
        f"DONNÉES DE RECHERCHE:\n{corpus[:4000]}"
    )

    for attempt in range(2):
        try:
            resp = gpt.chat.completions.create(
                model=WRITE_GPT,
                messages=[
                    {"role": "system", "content": STYLE_GUIDE},
                    {"role": "user", "content": full}
                ],
                max_completion_tokens=8000
            )
            text = resp.choices[0].message.content or ""
            if len(text.strip()) < 200:
                print(f"  Tentative {attempt+1}: reponse trop courte ({len(text)} chars), retry...")
                continue
            elapsed = time.time() - t0
            words = len(text.split())
            print(f"  OK {words} mots en {elapsed:.1f}s")
            return text, elapsed
        except Exception as e:
            print(f"  FAIL tentative {attempt+1}: {e}")

    elapsed = time.time() - t0
    print(f"  FAIL GPT-5.5 apres 2 tentatives")
    return "[ERREUR GPT: reponse vide apres retry]", elapsed


# ─── Phase 5: Scoring ─────────────────────────────────────────────────────────
SCORING_PROMPT = """Évalue cet article sur 10 critères (0-10 chacun).

Critères:
1. sources_citees      — Au moins 2 sources externes avec référence réelle
2. prise_position      — Point de vue clair et tranché (pas de "d'un côté/de l'autre")
3. donnees_locales     — Chiffres spécifiques au Québec (prix, pourcentages, régions)
4. angle_unique        — Angle différent des articles génériques sur ce sujet
5. style_fokuz         — Ton direct, tutoiement, phrases percutantes
6. zero_cliches        — Absence de "il est important", "n'hésitez pas", "en conclusion"
7. structure_narrative — Hook fort → contexte → données → pièges → action
8. longueur_adequate   — Entre 1600 et 2400 mots (0 = hors range, 10 = parfait)
9. element_contrarian  — Contredit une croyance commune du lecteur
10. cta_integre        — Lien/CTA naturel dans le texte (pas isolé en fin)

Retourne UNIQUEMENT ce JSON:
{
  "scores": {
    "sources_citees": X, "prise_position": X, "donnees_locales": X,
    "angle_unique": X, "style_fokuz": X, "zero_cliches": X,
    "structure_narrative": X, "longueur_adequate": X,
    "element_contrarian": X, "cta_integre": X
  },
  "total": X,
  "verdict": "phrase courte de verdict",
  "point_fort": "meilleur aspect de l'article",
  "point_faible": "aspect le plus faible à améliorer"
}"""


def phase5_score(article: str, label: str) -> dict:
    words = len(article.split())
    print(f"  Scoring {label} ({words} mots)...")

    if article.startswith("[ERREUR"):
        return {"total": 0, "scores": {}, "verdict": "Article non généré", "model": label, "word_count": 0}

    try:
        resp = claude.messages.create(
            model=QA_MODEL,
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": f"{SCORING_PROMPT}\n\nARTICLE ({words} mots):\n{article[:3500]}"
            }]
        )
        raw = resp.content[0].text
        start, end = raw.find('{'), raw.rfind('}') + 1
        result = json.loads(raw[start:end])
        result["model"] = label
        result["word_count"] = words
        print(f"  {label}: {result.get('total', '?')}/100")
        return result

    except Exception as e:
        print(f"  ✗ Erreur scoring {label}: {e}")
        return {"total": 0, "scores": {}, "verdict": f"Erreur: {e}", "model": label, "word_count": words}


# ─── Save Results ─────────────────────────────────────────────────────────────
def save_results(sujet, art_a, art_b, sc_a, sc_b, brief, prompt, sources, money_site=None):
    slug = sujet[:40].lower().replace(' ', '-').replace("'", "")
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    out  = Path(__file__).parent / "results" / f"{ts}_{slug}"
    out.mkdir(parents=True, exist_ok=True)

    (out / f"claude_sonnet.md").write_text(art_a, encoding="utf-8")
    (out / f"gpt55.md").write_text(art_b, encoding="utf-8")
    (out / "brief.json").write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "prompt.txt").write_text(prompt, encoding="utf-8")
    if sources:
        (out / "sources.txt").write_text("\n".join(sources), encoding="utf-8")

    # ─ Comparison Report ──────────────────────────────────────────────────────
    total_a = sc_a.get("total", 0)
    total_b = sc_b.get("total", 0)
    winner  = "Claude Sonnet 4.6" if total_a >= total_b else "GPT-5.5"

    criteria_labels = {
        "sources_citees": "Sources citées",
        "prise_position": "Prise de position",
        "donnees_locales": "Données locales QC",
        "angle_unique": "Angle unique",
        "style_fokuz": "Style Fokuz",
        "zero_cliches": "Zéro clichés",
        "structure_narrative": "Structure narrative",
        "longueur_adequate": "Longueur adéquate",
        "element_contrarian": "Élément contrarian",
        "cta_integre": "CTA intégré",
    }

    scores_a = sc_a.get("scores", {})
    scores_b = sc_b.get("scores", {})

    table_rows = ""
    for key, label in criteria_labels.items():
        sa = scores_a.get(key, "?")
        sb = scores_b.get(key, "?")
        if isinstance(sa, int) and isinstance(sb, int):
            badge = "← 🏆" if sa > sb else ("→ 🏆" if sb > sa else "🤝")
        else:
            badge = ""
        table_rows += f"| {label} | {sa}/10 | {sb}/10 | {badge} |\n"

    report = f"""# Rapport A/B Test — {sujet}
> Généré le {datetime.now().strftime("%Y-%m-%d %H:%M")}

## 🏆 Gagnant : {winner}

| | Claude Sonnet 4.6 | GPT-5.5 |
|---|---|---|
| **Score total** | **{total_a}/100** | **{total_b}/100** |
| Mots | {sc_a.get('word_count','?')} | {sc_b.get('word_count','?')} |

## Scores détaillés

| Critère | Claude Sonnet | GPT-5.5 | |
|---------|--------------|---------|---|
{table_rows}
## Verdicts

### Claude Sonnet 4.6
- **Score :** {total_a}/100
- **Verdict :** {sc_a.get('verdict', '')}
- **Point fort :** {sc_a.get('point_fort', '')}
- **Point faible :** {sc_a.get('point_faible', '')}

### GPT-5.5
- **Score :** {total_b}/100
- **Verdict :** {sc_b.get('verdict', '')}
- **Point fort :** {sc_b.get('point_fort', '')}
- **Point faible :** {sc_b.get('point_faible', '')}

## Brief éditorial utilisé
- **Angle :** {brief.get('angle_recommande', '')}
- **Insight :** {brief.get('insight_principal', '')}
- **Idée contrarienne :** {brief.get('idee_contrarienne', '')}
- **Prix réels :** {brief.get('prix_reels', '')}
- **Pièges :** {', '.join(brief.get('pieges_top3', []))}
- **Money site CTA :** {money_site['site_name'] + ' → ' + money_site['site'] if money_site else 'aucun'}

## Fichiers générés
- [Article Claude Sonnet](claude_sonnet.md)
- [Article GPT-5.5](gpt55.md)
- [Brief JSON](brief.json)
- [Prompt utilisé](prompt.txt)
"""
    (out / "rapport_ab.md").write_text(report, encoding="utf-8")
    return out, winner


# ─── Main Pipeline ────────────────────────────────────────────────────────────
def run(sujet: str):
    print(f"\n{'='*55}")
    print(f"  FOKUZ PIPELINE")
    print(f"  Sujet : {sujet}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*55}")

    t0 = time.time()

    money_site = detect_money_site(sujet)
    if money_site:
        print(f"  Money site detecte : {money_site['site_name']}")
    else:
        print(f"  Money site : aucun detecte (sujet hors niche connue)")

    corpus, sources    = phase1_research(sujet)
    brief              = phase2_synthesis(sujet, corpus)
    writing_prompt     = phase3_prompt_gen(sujet, brief, corpus, sources, money_site)
    art_a, time_a      = phase4a_claude(writing_prompt, corpus, sources, money_site)
    art_b, time_b      = phase4b_gpt(writing_prompt, corpus, sources, money_site)

    print(f"\n{'─'*50}")
    print(f"[Phase 5] Scoring ({QA_MODEL})")
    print(f"{'─'*50}")
    sc_a = phase5_score(art_a, "Claude Sonnet 4.6")
    sc_b = phase5_score(art_b, "GPT-5.5")

    out_dir, winner = save_results(sujet, art_a, art_b, sc_a, sc_b, brief, writing_prompt, sources, money_site)

    total = time.time() - t0
    print(f"\n{'='*55}")
    print(f"  TERMINÉ en {total:.0f}s")
    print(f"  🏆 Gagnant : {winner}")
    print(f"  Claude Sonnet : {sc_a.get('total','?')}/100 ({sc_a.get('word_count','?')} mots, {time_a:.0f}s)")
    print(f"  GPT-5.5       : {sc_b.get('total','?')}/100 ({sc_b.get('word_count','?')} mots, {time_b:.0f}s)")
    print(f"  Résultats     : {out_dir}")
    print(f"{'='*55}\n")


# ─── Test Models ──────────────────────────────────────────────────────────────
def test_models():
    """Vérifie que tous les modèles répondent correctement"""
    print("Test de connectivité des modèles...\n")
    tests = [
        ("Perplexity sonar-pro", lambda: pplx.chat.completions.create(
            model=PERPLEXITY_MODEL,
            messages=[{"role": "user", "content": "Dis bonjour en 5 mots."}],
            max_tokens=20
        ).choices[0].message.content),
        ("OpenAI gpt-5.4-nano", lambda: gpt.chat.completions.create(
            model=SYNTHESIS_MODEL,
            messages=[{"role": "user", "content": "Dis bonjour en 5 mots."}],
            max_completion_tokens=20
        ).choices[0].message.content),
        ("OpenAI gpt-5.4-mini", lambda: gpt.chat.completions.create(
            model=PROMPTGEN_MODEL,
            messages=[{"role": "user", "content": "Dis bonjour en 5 mots."}],
            max_completion_tokens=20
        ).choices[0].message.content),
        ("OpenAI gpt-5.5", lambda: gpt.chat.completions.create(
            model=WRITE_GPT,
            messages=[{"role": "user", "content": "Dis bonjour en 5 mots."}],
            max_completion_tokens=20
        ).choices[0].message.content),
        ("Claude sonnet-4-6", lambda: claude.messages.create(
            model=WRITE_CLAUDE,
            max_tokens=20,
            messages=[{"role": "user", "content": "Dis bonjour en 5 mots."}]
        ).content[0].text),
        ("Claude haiku-4-5", lambda: claude.messages.create(
            model=QA_MODEL,
            max_tokens=20,
            messages=[{"role": "user", "content": "Dis bonjour en 5 mots."}]
        ).content[0].text),
    ]
    all_ok = True
    for name, fn in tests:
        try:
            resp = fn()
            print(f"  OK {name}: {resp.strip()[:50]}")
        except Exception as e:
            print(f"  FAIL {name}: {e}")
            all_ok = False
    print()
    return all_ok


# ─── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fokuz Content Pipeline A/B")
    parser.add_argument("sujet", nargs="*", help="Sujet de l'article")
    parser.add_argument("--test-models", action="store_true", help="Tester la connectivité des modèles")
    args = parser.parse_args()

    if args.test_models:
        ok = test_models()
        sys.exit(0 if ok else 1)

    sujet = " ".join(args.sujet) if args.sujet else "entretien de toiture Québec"
    run(sujet)
