#!/usr/bin/env python3
"""
fetch_regional_context.py — Fetch real regional context via Perplexity API
Usage: python tools/fetch_regional_context.py --niche couvreur

Requires: PERPLEXITY_API_KEY env var (or --key argument)
Saves:    engine_qc/regional_context_<niche>.json
"""
import argparse
import csv
import json
import os
import time
from pathlib import Path

import requests

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

NICHE_PROMPTS = {
    "couvreur": (
        "Donne-moi 3-4 faits spécifiques et utiles sur la toiture résidentielle dans la région "
        "administrative {region} au Québec : types de toits courants, défis climatiques, âge moyen "
        "des maisons, particularités locales. Réponds en 100-150 mots, en français, texte continu "
        "(pas de puces). Sois factuel et précis."
    ),
    "bardeau": (
        "Donne-moi 3-4 faits spécifiques sur le bardeau d'asphalte et la réfection de toiture dans "
        "la région {region} au Québec : durée de vie typique selon le climat, fréquence de "
        "remplacement, particularités hivernales. Réponds en 100-150 mots en français, texte continu."
    ),
    "toiture-residentielle": (
        "Donne-moi 3-4 faits spécifiques sur la toiture résidentielle dans la région {region} au "
        "Québec : types de bâtiments, contraintes climatiques, fréquence des travaux, âge du parc "
        "immobilier. Réponds en 100-150 mots en français, texte continu."
    ),
    "climatisation": (
        "Donne-moi 3-4 faits spécifiques sur la climatisation et les thermopompes dans la région "
        "{region} au Québec : climat estival, taux d'adoption, subventions disponibles, types "
        "d'habitations. Réponds en 100-150 mots en français, texte continu."
    ),
    "fournaise": (
        "Donne-moi 3-4 faits spécifiques sur le chauffage et les fournaises dans la région "
        "{region} au Québec : types de chauffage courants, coûts énergétiques, programmes de "
        "remplacement, climat hivernal. Réponds en 100-150 mots en français, texte continu."
    ),
    "chauffage": (
        "Tu es un expert en systèmes de chauffage résidentiel au Québec. "
        "Donne-moi un contexte régional factuel et précis sur le chauffage dans la région administrative {region} au Québec. "
        "Couvre ces 5 points avec des données chiffrées propres à {region} :\n"
        "(1) Mix énergétique de chauffage dans {region} : proportion des ménages chauffés à l'électricité (plinthes, fournaise électrique, thermopompe) vs gaz naturel vs propane vs mazout — et l'évolution récente vers les thermopompes. "
        "Quelles municipalités de {region} ont accès au réseau de gaz naturel Énergir vs celles qui dépendent du propane ou du mazout.\n"
        "(2) Climat hivernal de {region} : températures minimales typiques en janvier, nombre de degrés-jours de chauffage, durée de la saison de chauffage — ces données justifient le choix entre thermopompe seule vs thermopompe + système d'appoint pour {region}.\n"
        "(3) Parc de systèmes de chauffage dans {region} : âge moyen des fournaises en place (les remplacements massifs des années 1990-2000 arrivent en fin de vie), proportion de maisons avec fournaise centrale vs chauffage électrique uniquement, potentiel de conversion vers la thermopompe.\n"
        "(4) Programmes de subventions disponibles pour les résidents de {region} : Rénoclimat (montants pour thermopompe et fournaise haute efficacité), Hydro-Québec LogisVert, programmes fédéraux RCEE, et tout programme municipal spécifique.\n"
        "(5) Marché des entrepreneurs en chauffage dans {region} : densité d'entreprises certifiées RBQ, délais typiques pour une soumission en haute saison (automne), coût moyen d'une urgence de chauffage dans {region}.\n"
        "Réponds en 220-270 mots, en français, texte continu par thème, données chiffrées partout. "
        "Toute généralité applicable à n'importe quelle région est inutile — sois spécifique à {region}."
    ),
    "thermopompe-aerothermique": (
        "Tu es un expert en efficacité énergétique résidentielle au Québec. "
        "Donne-moi un contexte régional détaillé et factuel sur les thermopompes aérothermiques "
        "dans la région administrative {region} au Québec. "
        "Couvre obligatoirement ces éléments avec des données précises : "
        "(1) Climat hivernal de {region} : températures minimales typiques en janvier, nombre de degrés-jours de chauffage, fréquence des épisodes sous -20°C — ces données déterminent si une thermopompe aérothermique haute performance (-25°C à -30°C) est pertinente. "
        "(2) Mix énergétique de {region} : proportion des ménages chauffés à l'électricité vs gaz naturel vs propane vs mazout — le passage à l'aérothermique est plus pertinent là où le gaz et le propane dominent encore. "
        "(3) Parc immobilier de {region} : âge moyen des maisons, proportion de maisons unifamiliales vs condos vs duplex, superficie typique — ces facteurs déterminent le type de système aérothermique recommandé. "
        "(4) Programmes de subventions disponibles spécifiquement pour {region} : Rénoclimat (montants actuels), LogisVert d'Hydro-Québec, programmes fédéraux (RCEE), crédits d'impôt provinciaux, et tout programme municipal si applicable. "
        "(5) Taux d'adoption des thermopompes dans {region} et tendances récentes — est-ce que cette région est en avance ou en retard sur la moyenne québécoise ? "
        "Réponds en 200-250 mots, en français, texte continu, ton factuel. Utilise des chiffres réels quand disponibles."
    ),
    "reparation-thermopompe": (
        "Tu es un expert en entretien et réparation de systèmes CVAC au Québec. "
        "Donne-moi un contexte régional détaillé et factuel sur la réparation de thermopompes "
        "dans la région administrative {region} au Québec. "
        "Couvre obligatoirement ces éléments : "
        "(1) Contraintes climatiques spécifiques de {region} qui causent des pannes de thermopompes : rigueur des hivers (températures extrêmes, durée des périodes de froid), cycles de gel-dégel printaniers, humidité estivale — explique concrètement l'impact sur les composants (compresseur, circuit réfrigérant, carte électronique, unité extérieure). "
        "(2) Âge du parc de thermopompes dans {region} : quand les premières installations massives ont eu lieu (généralement fin 2000s-début 2010s), ce qui signifie qu'un volume important d'appareils atteint maintenant 15-20 ans, la fin de leur durée de vie utile. "
        "(3) Problèmes spécifiques au type de logements de {region} : maisons mal isolées, planchers chauffants incompatibles, panneaux électriques vétustes à 100A insuffisants, gaines mal dimensionnées. "
        "(4) Disponibilité des techniciens certifiés en réfrigération dans {region} — zones rurales vs urbaines, délais typiques d'intervention en urgence en plein hiver. "
        "(5) Coûts typiques de réparation dans {region} : tarifs horaires des techniciens CVAC, coût des pièces les plus remplacées (compresseur, capaciteur, détendeur). "
        "Réponds en 200-250 mots, en français, texte continu, ton factuel et utile."
    ),
    "climatisation-thermopompe": (
        "Tu es un expert en climatisation et confort thermique résidentiel au Québec. "
        "Donne-moi un contexte régional détaillé et factuel sur la climatisation et les thermopompes "
        "dans la région administrative {region} au Québec. "
        "Couvre obligatoirement ces éléments avec des données précises : "
        "(1) Climat estival de {region} : températures maximales typiques en juillet-août, nombre de jours de chaleur accablante (plus de 30°C), humidex moyen, fréquence des vagues de chaleur — ces données justifient l'installation d'une climatisation. "
        "(2) Taux d'équipement en climatisation de {region} : quelle proportion des ménages est climatisée, évolution depuis 5-10 ans, types de systèmes les plus courants (murales, centrales, portables). "
        "(3) Particularités du parc immobilier de {region} pour la climatisation : maisons sans gaines d'air (limitées aux murales ou multi-zones), condos avec restrictions de copropriété, maisons ancestrales avec murs épais. "
        "(4) Programmes de subventions accessibles pour la climatisation dans {region} : aides disponibles, conditions d'admissibilité, montants, démarches. "
        "(5) Saisonnalité thermique de {region} : hivers rigoureux + étés chauds = argument fort pour la thermopompe air-air qui gère les deux saisons. Donne des données chiffrées sur les degrés-jours de chauffage ET de climatisation pour illustrer la double utilité. "
        "Réponds en 200-250 mots, en français, texte continu, ton factuel."
    ),
    "installation-thermopompe": (
        "Tu es un expert en installation de systèmes thermiques résidentiels au Québec. "
        "Donne-moi un contexte régional détaillé et factuel sur l'installation de thermopompes "
        "dans la région administrative {region} au Québec. "
        "Couvre obligatoirement ces éléments avec des données précises : "
        "(1) Types de logements dominants dans {region} et leur compatibilité avec différents systèmes de thermopompe : maisons unifamiliales (idéales pour multi-zones ou centrale), maisons de ville et duplex (murales ou systèmes compacts), condos (restrictions fréquentes, murales uniquement). Précise les proportions si possible. "
        "(2) Infrastructure électrique de {region} : proportion de maisons avec panneaux 200A (compatibles avec la plupart des thermopompes) vs 100A vétustes qui nécessitent une mise à niveau avant installation. L'âge du parc immobilier de {region} est clé ici. "
        "(3) Contexte climatique hivernal de {region} : températures minimales et nombre de degrés-jours de chauffage — ces données déterminent la puissance requise (BTU) et la nécessité d'un système de chauffage d'appoint pour les hivers extrêmes. "
        "(4) Délais et coûts d'installation dans {region} : disponibilité des installateurs certifiés RBQ en réfrigération, délais typiques de projet (1 semaine à 6 semaines selon la saison), facteurs qui font varier les prix (complexité d'accès, longueur des lignes frigorifiques, mise à niveau électrique). "
        "(5) Programmes d'aide à l'installation dans {region} : Rénoclimat, LogisVert, RCEE fédéral, financement 0% offert par certains distributeurs. Montants accessibles et conditions. "
        "Réponds en 200-250 mots, en français, texte continu, ton expert et utile."
    ),
    "pavage-asphalte": (
        "Tu es un expert en pavage résidentiel au Québec. "
        "Donne-moi un contexte régional détaillé et factuel sur le pavage en asphalte "
        "dans la région administrative {region} au Québec. "
        "Couvre obligatoirement ces éléments avec des données précises : "
        "(1) Cycles gel-dégel dans {region} : nombre de cycles annuels, amplitudes thermiques hivernales, impact concret sur la durée de vie d'une entrée en asphalte mal posée vs bien posée — c'est le facteur #1 qui justifie un entrepreneur certifié. "
        "(2) Âge et type du parc résidentiel de {region} : proportion de maisons unifamiliales avec entrée de garage (principal marché), âge moyen des propriétés, proportion de maisons construites avant 1990 dont les entrées asphalte originales arrivent en fin de vie. "
        "(3) Saisonnalité du pavage dans {region} : fenêtre optimale pour paver (généralement mai à octobre), contraintes climatiques locales qui raccourcissent la saison, impact sur les délais et la disponibilité des entrepreneurs. "
        "(4) Prix typiques dans {region} : coût au pied carré pour une entrée résidentielle standard (remplacement vs neuf), facteurs régionaux qui font varier les prix (coût du bitume, disponibilité de la main-d'œuvre, distance des usines d'asphalte). "
        "(5) Réglementation et certification dans {region} : exigences RBQ pour les travaux d'excavation et de pavage, importance d'un contrat écrit avec garantie, pratiques des entrepreneurs locaux. "
        "Réponds en 200-250 mots, en français, texte continu, ton factuel et pratique."
    ),
    "prix-pave-uni": (
        "Tu es un expert en aménagement extérieur et pavé uni au Québec. "
        "Donne-moi un contexte régional détaillé et factuel sur le pavé uni (interlock) "
        "dans la région administrative {region} au Québec. "
        "Couvre obligatoirement ces éléments avec des données précises : "
        "(1) Profil socio-économique de {region} pertinent pour le pavé uni : revenu médian des ménages, proportion de propriétaires vs locataires, valeur médiane des propriétés — le pavé uni cible les propriétaires à revenus moyens-élevés qui valorisent l'esthétique. "
        "(2) Types de projets typiques dans {region} : entrées de garage (le plus populaire), allées piétonnes, patios, bordures, cours arrière — quelle est la demande relative de chaque type selon les quartiers et le type de propriétés. "
        "(3) Impact climatique sur le pavé uni dans {region} : cycles gel-dégel et leur effet sur les pavés (soulèvement, désalignement), importance du lit de sable et de la fondation granulaire, durée de vie attendue dans les conditions de {region} (25-30 ans si bien installé). "
        "(4) Coûts typiques dans {region} : prix au pied carré selon le type de pavé (standard, premium, naturel), coût total pour une entrée typique, comparaison avec asphalte — justifier le surcoût du pavé uni. "
        "(5) Disponibilité des matériaux et entrepreneurs dans {region} : fournisseurs locaux de pavés (Oaks, Permacon, Techo-Bloc), délais de livraison, concentration des entrepreneurs spécialisés en interlock. "
        "Réponds en 200-250 mots, en français, texte continu, ton expert et accessible."
    ),
    "pavage-commercial": (
        "Tu es un expert en pavage commercial et industriel au Québec. "
        "Donne-moi un contexte régional détaillé et factuel sur le pavage commercial "
        "dans la région administrative {region} au Québec. "
        "Couvre obligatoirement ces éléments avec des données précises : "
        "(1) Tissu économique commercial et industriel de {region} : types d'industries et commerces dominants (manufactures, centres commerciaux, immeubles à bureaux, entrepôts logistiques, multi-résidentiels), densité de stationnements commerciaux nécessitant entretien ou remplacement. "
        "(2) Volume et taille des projets typiques dans {region} : superficie moyenne d'un stationnement commercial, fréquence de remplacement (15-20 ans pour asphalte commercial bien entretenu), budget typique (20k$ à 100k$+ selon la superficie et les charges de trafic). "
        "(3) Exigences techniques spécifiques au commercial dans {region} : épaisseur d'asphalte requise selon le trafic lourd (camions de livraison, chariots élévateurs), drainage obligatoire, signalisation, délimitation des cases de stationnement, conformité municipale. "
        "(4) Saisonnalité et planification dans {region} : contraintes pour minimiser la fermeture du stationnement (travaux par phases), délais de projet commercial (2 semaines à 2 mois), impact sur l'exploitation du commerce. "
        "(5) Critères de sélection d'un entrepreneur commercial dans {region} : licence RBQ obligatoire, assurance responsabilité civile commerciale (2M$+), références de projets similaires, capacité d'équipement (finisseurs industriels, compacteurs lourds). "
        "Réponds en 200-250 mots, en français, texte continu, ton expert B2B."
    ),
    "excavation": (
        "Tu es un expert en géotechnique et travaux d'excavation résidentielle au Québec. "
        "Donne-moi un contexte régional PRÉCIS et factuel sur l'excavation dans la région administrative {region} au Québec. "
        "Je veux des données réelles tirées de rapports géotechniques, études de sol, ou données municipales — pas des généralités qui s'appliquent à toutes les régions. "
        "Couvre ces 5 points avec des données chiffrées quand disponibles : "
        "(1) Géologie et sol dominant dans {region} : est-ce argile marine de la mer de Champlain (basses-terres), till glaciaire, roc du Bouclier canadien, sable fluvioglaciaire, sol organique ou tourbe ? "
        "Donne la profondeur typique des couches de sol avant d'atteindre le roc ou un sol portant. "
        "Mentionne si {region} est connue pour l'argile de Leda / argile sensible (zones à risque de glissement, liquéfaction), et si les projets d'excavation nécessitent souvent une étude géotechnique préalable. "
        "Explique concrètement ce que le type de sol implique pour le prix et la difficulté d'excavation (ex : argile = lent et lourd, roc = dynamitage possible, sable = risque d'éboulement). "
        "(2) Roc et dynamitage dans {region} : à quelle profondeur le roc affleure-t-il typiquement ? "
        "Est-ce fréquent de frapper du roc lors d'une excavation pour piscine creusée ou fondation dans {region} ? "
        "Le dynamitage ou le brise-roc hydraulique est-il courant, et quel surcoût cela représente-t-il ? "
        "(3) Nappe phréatique et drainage dans {region} : le niveau de la nappe phréatique est-il problématique ? "
        "Y a-t-il des zones connues pour l'eau souterraine élevée (ex : bord de rivière, zones inondables, secteurs argileux saturés) ? "
        "Cela force-t-il le pompage en cours de chantier ? Impact sur le coût et la durée des travaux. "
        "(4) Profondeur de gel et saisonnalité dans {region} : profondeur de pénétration du gel en cm ou mètres selon la latitude de {region}, "
        "ce que ça impose comme profondeur minimale de fondation, fenêtre optimale pour excaver, "
        "et ce que l'excavation en sol partiellement gelé coûte en surplus (location brise-béton, productivité réduite). "
        "(5) Types de projets et prix dans {region} : quels projets d'excavation résidentielle sont les plus fréquents (piscines creusées, agrandissements de sous-sol, fondations de garage, terrassement, drainage) ? "
        "Donne des fourchettes de prix réalistes pour {region} selon la difficulté du sol. "
        "Mentionne si le coût de transport des déblais est un facteur important (distance des sites d'enfouissement). "
        "Réponds en 280-320 mots, en français, texte continu, avec des chiffres réels partout où c'est possible. "
        "Sois spécifique à {region} — toute phrase qui s'appliquerait à n'importe quelle région du Québec est inutile."
    ),
    "prix-toiture": (
        "Tu es un expert en toiture résidentielle et en marché de la construction au Québec. "
        "Donne-moi un contexte régional TRÈS DÉTAILLÉ et factuel sur la toiture résidentielle "
        "dans la région administrative {region} au Québec. "
        "Couvre obligatoirement ces 6 éléments avec des données précises et chiffrées : "
        "(1) Climat hivernal de {region} : charge de neige annuelle en cm, nombre de cycles gel-dégel par année, températures minimales typiques en janvier, durée de la saison hivernale — ces données expliquent pourquoi les toitures de {region} ont une durée de vie souvent inférieure à la moyenne canadienne et justifient un couvreur certifié. "
        "(2) Parc immobilier résidentiel de {region} : âge moyen des maisons, proportion construites avant 1980/1990/2000, types de toits dominants (pente faible vs forte, maisons unifamiliales vs bungalows vs cottages), proportion de toits plats dans les zones urbaines — ces données permettent d'estimer combien de toitures arrivent en fin de vie. "
        "(3) Prix du marché dans {region} : coût moyen réel au pied carré pour bardeaux d'asphalte, toiture métallique et membrane TPO, fourchette de prix pour une maison standard de 1200-1500 pi² de surface de toit, facteurs régionaux qui influencent les prix (disponibilité des couvreurs, coût de la main-d'œuvre locale, distance des fournisseurs de matériaux). "
        "(4) Matériaux privilégiés dans {region} : quelle est la part de marché des bardeaux d'asphalte vs métal vs TPO/EPDM, pourquoi certains matériaux sont plus populaires dans cette région (coût, disponibilité, performance climatique), tendances récentes. "
        "(5) Saisonnalité des travaux dans {region} : fenêtre optimale pour la réfection de toiture (généralement mai à octobre), impact des conditions météo locales sur la durée et la qualité des travaux, disponibilité des couvreurs en haute saison vs basse saison, délais typiques pour obtenir une soumission et démarrer les travaux. "
        "(6) Réglementation et certification dans {region} : exigences RBQ spécifiques aux travaux de toiture, obligations d'assurance des couvreurs, permis requis selon les municipalités, programmes de subventions ou crédits disponibles pour rénovation de toiture dans la région. "
        "Réponds en 300-350 mots, en français, texte continu et bien structuré par thème, ton factuel et précis avec des chiffres réels quand disponibles."
    ),
    "peinture": (
        "Tu es un expert en peinture résidentielle et commerciale au Québec, et en marché de la rénovation. "
        "Ta mission : produire un contexte régional PRÉCIS, FACTUEL et RICHE sur la peinture résidentielle "
        "dans la région administrative {region} au Québec. "
        "Couvre obligatoirement ces 5 éléments avec des données précises et chiffrées : "
        "(1) Parc immobilier de {region} et besoins en peinture : âge moyen des maisons, proportion construites avant 1980/1990 (peinture intérieure et extérieure vieillissante), types de revêtements extérieurs dominants dans {region} (vinyle, aluminium, bois, brique, fibrociment) et leur fréquence de repeinture, proportion de maisons unifamiliales vs condos vs logements locatifs. "
        "(2) Climat de {region} et impact sur la peinture extérieure : nombre de cycles gel-dégel annuels, humidité relative, ensoleillement (UV qui dégrade la peinture), précipitations et leur impact sur la durée de vie d'une peinture extérieure dans {region}, fenêtre climatique idéale pour peindre l'extérieur (température minimale 10°C, humidité <80%). "
        "(3) Prix du marché dans {region} : coût moyen main-d'oeuvre au pied carré pour peinture intérieure et extérieure, fourchette de prix réaliste pour une maison unifamiliale standard (1000-1500 pi² intérieur, 2000-3000 pi² extérieur), facteurs régionaux qui influencent les prix (disponibilité des peintres locaux, coût de la main-d'oeuvre). "
        "(4) Produits et tendances dans {region} : types de peintures les plus utilisés (latex, alkyde, peintures sans COV), tendances actuelles, présence de maisons avec peinture au plomb (avant 1978), popularité des peintures haut de gamme selon le profil socio-économique de {region}. "
        "(5) Main-d'oeuvre et marché des peintres dans {region} : densité de peintres certifiés RBQ (2.3.1), délais typiques pour obtenir 3 soumissions en haute saison (mai-sept), saisonnalité (pointe printanière liée aux ventes immobilières). "
        "Réponds en 280-320 mots, en français, texte continu. "
        "Sois spécifique à {region} — toute phrase qui s'appliquerait à n'importe quelle région du Québec est inutile.\n\n"
        "Ensuite, fournis les prix typiques du marché de la peinture résidentielle dans {region} :\n"
        "- service1_min / service1_max : peinture intérieure complète (maison unifamiliale, toutes pièces)\n"
        "- service2_min / service2_max : peinture extérieure complète (revêtement, soffites, fascias)\n"
        "- service3_min / service3_max : peinture d'une pièce (murs + plafond)\n"
        "- service4_min / service4_max : peinture plafonds + moulures (maison complète)\n"
        "Fourchettes typiques QC 2024 pour calibrer (ADAPTE selon compétition et coût de vie de {region}) :\n"
        "  intérieur complet : 2 500–12 000 $ | extérieur complet : 2 000–10 000 $ | une pièce : 300–2 000 $ | plafonds+moulures : 400–2 500 $\n\n"
        "TERMINE TON TEXTE PAR CE BLOC EXACT — RÈGLES ABSOLUES :\n"
        "- La ligne `---PRIX---` doit être seule sur sa ligne, après un saut de ligne\n"
        "- Le JSON doit être sur la ligne immédiatement suivante, rien d'autre\n"
        "- Remplace les XXXXX par des entiers sans guillemets ni virgules dans les nombres\n"
        "- Ce bloc doit être la DERNIÈRE chose dans ta réponse\n\n"
        "---PRIX---\n"
        '{{"service1_min": XXXXX, "service1_max": XXXXX, "service2_min": XXXXX, "service2_max": XXXXX, "service3_min": XXXXX, "service3_max": XXXXX, "service4_min": XXXXX, "service4_max": XXXXX}}'
    ),
    "agrandissement": (
        "Tu es un expert en construction résidentielle, agrandissement de maison et réglementation municipale au Québec. "
        "Donne-moi un contexte régional TRÈS DÉTAILLÉ et factuel sur l'agrandissement de maison "
        "dans la région administrative {region} au Québec. "
        "Couvre obligatoirement ces 5 éléments avec des données précises et chiffrées : "
        "(1) Marché de l'agrandissement dans {region} : types de projets les plus fréquents (extension latérale, ajout d'étage, garage attenant, aménagement de sous-sol), pourquoi les propriétaires de {region} choisissent d'agrandir plutôt que déménager (coûts de transaction, valeur foncière élevée, attachement au quartier), superficie moyenne ajoutée et coût au pied carré dans {region} comparé à la construction neuve. "
        "(2) Règlements de zonage dans {region} : marges de recul latérales et arrière typiques imposées par les MRC de {region}, coefficient d'emprise au sol maximal, hauteur maximale autorisée, cas où un certificat d'autorisation ou une dérogation mineure est nécessaire, délais typiques pour l'obtention d'un permis de construction dans les municipalités de {region}. "
        "(3) Contraintes de sol et de fondation dans {region} : type de sol dominant (argile, sable, roc, limon — impact sur le type de fondation requis pour l'extension), profondeur de gel imposant une fondation hors-gel, surcoût si sol argileux ou roc en surface, nappe phréatique problématique dans certaines zones de {region}. "
        "(4) Prix du marché dans {region} : fourchette de prix réaliste pour une extension latérale de 300-500 pi², un ajout d'étage complet, un garage attenant double — avec et sans finition intérieure. Facteurs qui font varier le prix : accès au chantier, complexité structurale, MRC urbaine vs rurale. "
        "(5) Marché des entrepreneurs généraux dans {region} : densité d'entrepreneurs certifiés RBQ pour l'agrandissement, délais typiques pour obtenir 3 soumissions en haute saison (printemps-été), saisonnalité des travaux (quand commencer pour finir avant l'hiver), programmes d'aide financière disponibles pour agrandissement dans {region} (RénoVert, SCHL, prêts municipaux). "
        "Réponds en 280-320 mots, en français, texte continu, avec des chiffres réels partout où c'est possible. "
        "Sois spécifique à {region} — toute phrase qui s'appliquerait à n'importe quelle région du Québec est inutile."
    ),
    "cuisine": (
        "Tu es un expert en rénovation résidentielle et marché immobilier au Québec. "
        "Donne-moi un contexte régional TRÈS DÉTAILLÉ et factuel sur la rénovation de cuisine "
        "dans la région administrative {region} au Québec. "
        "Couvre obligatoirement ces 5 éléments avec des données précises et chiffrées : "
        "(1) Parc immobilier et profil des propriétaires de {region} : âge moyen des maisons, "
        "proportion construites avant 1990 (cuisines vieillissantes), valeur médiane des propriétés, "
        "proportion de propriétaires vs locataires, types de logements dominants (unifamiliales, condos, duplex) — "
        "ces données déterminent la taille et le budget typique des projets cuisine dans {region}. "
        "(2) Profil socio-économique de {region} pertinent pour la rénovation cuisine : revenu médian des ménages, "
        "propension à investir dans la rénovation vs déménager, présence d'une classe moyenne-supérieure portée sur "
        "les cuisines haut de gamme (quartz, armoires sur mesure, îlots). Compare avec la moyenne québécoise. "
        "(3) Tendances de rénovation cuisine dans {region} : styles et matériaux les plus demandés actuellement "
        "(cuisine ouverte vs fermée, couleurs populaires, armoires laminées vs MDF peint vs bois, "
        "comptoirs quartz vs granite, popularité des îlots multifonctions), "
        "ce qui distingue les goûts de {region} des grandes métropoles comme Montréal. "
        "(4) Marché local des entrepreneurs cuisine dans {region} : disponibilité des cuisinistes et rénovateurs, "
        "délais typiques entre la commande et la livraison des armoires (souvent 8-16 semaines), "
        "délais de disponibilité des entrepreneurs en haute saison (printemps-été), "
        "facteurs régionaux qui influencent les coûts (coût de la main-d'œuvre locale, présence de cuisinistes locaux vs déplacement depuis les grands centres). "
        "(5) Financement et aides disponibles dans {region} pour la rénovation cuisine : "
        "programmes RénoVert, crédits hypothécaires rénovation, financement sans intérêt offert par certains cuisinistes, "
        "tout programme municipal ou provincial d'aide à la rénovation domiciliaire applicable dans {region}. "
        "Réponds en 250-300 mots, en français, texte continu et bien structuré par thème, "
        "ton factuel et précis avec des chiffres réels quand disponibles. "
        "Toute généralité applicable à n'importe quelle région du Québec est inutile — sois spécifique à {region}."
    ),
    "prix-fenetres": (
        "Tu es un expert en rénovation résidentielle et efficacité énergétique au Québec. "
        "Donne-moi un contexte régional TRÈS DÉTAILLÉ et factuel sur le remplacement de fenêtres "
        "dans la région administrative {region} au Québec. "
        "Couvre obligatoirement ces 5 éléments avec des données précises et chiffrées : "
        "(1) Climat hivernal de {region} : températures minimales typiques en janvier-février, "
        "nombre de jours sous -20°C, accumulation de neige annuelle, indice d'humidité hivernale — "
        "ces données justifient concrètement le recours au triple vitrage ou aux fenêtres ER50+ dans cette région spécifique. "
        "Compare brièvement avec la moyenne québécoise si possible. "
        "(2) Parc immobilier de {region} : âge moyen des maisons, proportion construites avant 1990 "
        "(fenêtres originales ou première génération en fin de vie), types d'habitations dominants "
        "(unifamiliales, bungalows, condos, duplex), proportion de propriétaires vs locataires — "
        "ces données estiment le volume de fenêtres à remplacer dans la région. "
        "(3) Programmes d'aide financière disponibles pour {region} : Rénoclimat (montants actuels pour fenêtres), "
        "Hydro-Québec LogisVert, Rénover vert fédéral (RCEE), Novoclimat 2.0, "
        "tout crédit d'impôt provincial ou programme municipal. Précise les conditions d'admissibilité, "
        "les fenêtres éligibles (cotes ER minimales), et les montants réels accessibles pour un propriétaire typique de {region}. "
        "(4) Prix du marché dans {region} : coût moyen réel par fenêtre standard (60x36 po) en PVC double vs triple vitrage, "
        "fourchette pour une maison de 8-12 fenêtres, facteurs régionaux qui font varier les prix "
        "(disponibilité des installateurs locaux, coût de la main-d'œuvre, éloignement des grands centres, "
        "fournisseurs présents dans la région). "
        "(5) Contexte du marché local dans {region} : types de fenêtres les plus demandées selon les habitations locales, "
        "délais typiques d'installation (commande à pose), saisonnalité des travaux (peut-on installer en hiver ?), "
        "enjeux spécifiques à la région (vents dominants, condensation, givre intérieur). "
        "Réponds en 280-320 mots, en français, texte continu et bien structuré par thème, "
        "ton factuel et précis avec des chiffres réels quand disponibles. "
        "Toute phrase qui s'appliquerait à n'importe quelle région du Québec est inutile — sois spécifique à {region}."
    ),
    "prix-drain": (
        "Tu es un expert en drainage résidentiel, imperméabilisation et marché de la construction résidentielle au Québec. "
        "Ta mission : produire un contexte régional PRÉCIS, FACTUEL et RICHE sur le drainage de fondation "
        "dans la région administrative {region} au Québec. "
        "Recherche activement des données locales réelles (entrepreneurs locaux, forums de rénovation, "
        "études géologiques, données climatiques d'Environnement Canada pour {region}). "
        "\n\n"
        "Couvre ces 5 points avec des données chiffrées concrètes et propres à {region} :\n"
        "(1) GÉOLOGIE de {region} : type de sol dominant (argile de Leda, argile marine, till glaciaire, sable, roc), "
        "pression hydrostatique typique, zones ou municipalités les plus à risque d'infiltration dans {region} "
        "(bords de rivières nommées, secteurs argileux précis, zones inondables désignées). "
        "Explique ce que ça change concrètement pour l'excavation et la fréquence des appels.\n"
        "(2) CLIMAT de {region} : température minimale moyenne en janvier (°C), nombre de cycles gel-dégel annuels, "
        "profondeur de pénétration du gel (cm ou m) — données Environnement Canada. "
        "Impact réel sur les drains français de 40-50 ans (béton poreux vs PVC perforé), "
        "quels secteurs de {region} sont les plus touchés.\n"
        "(3) NAPPE ET HUMIDITÉ de {region} : niveau moyen de la nappe phréatique dans les secteurs bas, "
        "impact des printemps pluvieux et fonte des neiges sur la pression aux fondations dans {region}. "
        "Mentionne les périodes critiques (mois) et si possible la fréquence des urgences.\n"
        "(4) PARC IMMOBILIER de {region} : proportion de maisons construites avant 1985, "
        "types de fondations courants (béton coulé, blocs, pierre des champs), "
        "bungalows vs maisons à étages, périmètre de fondation typique en mètres linéaires.\n"
        "(5) MARCHÉ LOCAL de {region} : nombre estimé d'entrepreneurs spécialisés en drainage/imperméabilisation RBQ, "
        "délais de soumission typiques, saison optimale mai-octobre (pourquoi précisément dans {region}).\n"
        "\n"
        "Longueur : 320-380 mots, français, texte continu par thème, données chiffrées obligatoires partout. "
        "Toute généralité applicable à n'importe quelle région est inutile — sois hyper-spécifique à {region}.\n"
        "\n"
        "PRIX DU MARCHÉ DANS {region} — SECTION OBLIGATOIRE :\n"
        "Recherche les prix réels pratiqués par les entrepreneurs de drainage dans {region} en 2024-2025. "
        "Les prix ci-dessous sont des FOURCHETTES TOTALES (main-d'œuvre + matériaux + excavation) pour {region} :\n"
        "- drain_min / drain_max : coût total d'un drain français complet avec excavation extérieure, maison bungalow typique\n"
        "- fissure_min / fissure_max : coût total d'une réparation par injection polyuréthane (par fissure)\n"
        "- impermea_min : coût de départ d'une imperméabilisation extérieure complète avec excavation\n"
        "Fourchettes typiques QC 2024 pour calibrer (ADAPTE selon le niveau de vie et la compétition locale de {region}) :\n"
        "  drain complet : 14 000–35 000 $ | fissure injection : 4 000–12 000 $ | imperméabilisation : 18 000–40 000 $\n"
        "\n"
        "TERMINE TON TEXTE PAR CE BLOC EXACT — RÈGLES ABSOLUES :\n"
        "- La ligne `---PRIX---` doit être seule sur sa ligne, après un saut de ligne\n"
        "- Le JSON doit être sur la ligne immédiatement suivante, rien d'autre\n"
        "- Remplace les XXXXX par des entiers sans guillemets ni virgules dans les nombres\n"
        "- Ce bloc doit être la DERNIÈRE chose dans ta réponse\n"
        "\n"
        "---PRIX---\n"
        '{{"drain_min": XXXXX, "drain_max": XXXXX, "fissure_min": XXXXX, "fissure_max": XXXXX, "impermea_min": XXXXX}}'
    ),
    "prix-revetement": (
        "Tu es un expert en revêtement extérieur résidentiel et en marché de la construction au Québec. "
        "Donne-moi un contexte régional TRÈS DÉTAILLÉ et factuel sur le revêtement extérieur (siding) résidentiel "
        "dans la région administrative {region} au Québec. "
        "Couvre obligatoirement ces 5 éléments avec des données précises et chiffrées : "
        "(1) Climat de {region} et son impact sur le revêtement extérieur : nombre de cycles gel-dégel annuels, "
        "amplitudes thermiques hivernales (températures minimales typiques en janvier), accumulation de neige et humidité, "
        "exposition aux UV estivaux — explique concrètement pourquoi ces conditions dégradent certains revêtements plus vite "
        "et quels matériaux résistent le mieux dans {region} spécifiquement. "
        "(2) Parc immobilier de {region} et état des revêtements extérieurs : âge moyen des maisons, "
        "proportion construites avant 1990 (revêtements originaux en fin de vie), types de logements dominants "
        "(bungalows, cottages, maisons à pignons, bi-générationnels), "
        "surface de façade typique selon les habitations de {region}. "
        "Estime combien de maisons ont un revêtement à remplacer dans les 5-10 prochaines années. "
        "(3) Matériaux les plus populaires dans {region} : quelle est la part de marché actuelle du vinyle vs Canexel "
        "vs fibrociment (HardiePlank) vs aluminium vs brique, et pourquoi — est-ce que {region} penche vers "
        "le vinyle économique ou vers le fibrociment haut de gamme ? Tendances récentes dans les nouvelles constructions "
        "vs rénovations. Spécificités locales (ex : bois naturel encore courant dans certaines zones, brique dominante en milieu urbain). "
        "(4) Prix du marché dans {region} : coûts réels installés pour une maison unifamiliale standard (environ 150-200 m² de façade) "
        "en vinyle, Canexel et fibrociment, facteurs régionaux qui font varier les prix "
        "(coût de la main-d'œuvre locale, disponibilité des entrepreneurs spécialisés, distance des fournisseurs de matériaux, "
        "coût du retrait de l'ancien revêtement selon le type). "
        "(5) Saisonnalité et marché local dans {region} : fenêtre optimale pour la pose (mai à octobre), "
        "délais typiques pour obtenir une soumission d'un entrepreneur en revêtement dans {region}, "
        "disponibilité des poseurs en haute saison, certifications RBQ requises, "
        "programmes d'aide disponibles (Rénoclimat pour isolation simultanée, crédits d'impôt provinciaux, programmes municipaux). "
        "Réponds en 280-320 mots, en français, texte continu et bien structuré par thème, "
        "ton factuel et précis avec des chiffres réels quand disponibles. "
        "Toute phrase qui s'appliquerait à n'importe quelle région du Québec est inutile — sois spécifique à {region}."
    ),
    "prix-fissure": (
        "Tu es un expert en réparation de fissures de fondation, injection polyuréthane/époxy et marché de la construction résidentielle au Québec. "
        "Ta mission : produire un contexte régional PRÉCIS, FACTUEL et RICHE sur les fissures de fondation "
        "dans la région administrative {region} au Québec. "
        "Recherche activement des données locales réelles (entrepreneurs spécialisés, forums de rénovation, "
        "études géotechniques, données climatiques d'Environnement Canada pour {region}).\n\n"
        "Couvre ces 5 points avec des données chiffrées concrètes et propres à {region} :\n"
        "(1) GÉOLOGIE ET SOLS de {region} : type de sol dominant (argile de Leda, argile marine, till glaciaire, sable, roc), "
        "comment ces sols causent des fissures spécifiquement dans {region} (retrait argileux, tassement différentiel, "
        "pression hydrostatique latérale). Mentionne les municipalités ou secteurs de {region} les plus touchés par les fissures "
        "de fondation (zones argileuses, zones inondables, terrains en pente, anciens remblais).\n"
        "(2) CYCLES GEL-DÉGEL de {region} : température minimale moyenne en janvier (°C), nombre de cycles gel-dégel annuels "
        "— données Environnement Canada. Profondeur de pénétration du gel (m). "
        "Explique comment ces cycles créent concrètement des fissures dans les fondations de {region} : "
        "expansion/contraction du sol, soulèvement différentiel, fissures en chevron, fissures horizontales en blocs. "
        "Quels types de fondations (béton coulé, blocs de béton, pierre des champs) sont les plus vulnérables dans {region}.\n"
        "(3) HUMIDITÉ ET NAPPE de {region} : impact des printemps pluvieux et fonte des neiges sur l'activité des fissures "
        "(quand une fissure sèche devient une fissure active). Niveau typique de la nappe phréatique dans les secteurs bas de {region}. "
        "Périodes critiques de l'année (mois) où les fissures s'aggravent ou s'activent le plus.\n"
        "(4) PARC IMMOBILIER de {region} : proportion de maisons construites avant 1980 "
        "(béton maigre, peu armé, plus sujet aux fissures). Types de fondations courants dans {region} "
        "(béton coulé vs blocs de béton vs pierre des champs — chaque type fissure différemment). "
        "Proportion de bungalows avec sous-sol complet. Épaisseur et qualité typique du béton des constructions de {region} d'avant 1985.\n"
        "(5) MARCHÉ LOCAL de {region} : nombre estimé d'entreprises spécialisées en injection de fissures RBQ actives, "
        "délais typiques pour une soumission, est-ce que {region} a surtout des généralistes ou des spécialistes fissures. "
        "Saison optimale pour les réparations.\n\n"
        "Longueur : 320-380 mots, français, texte continu par thème, données chiffrées partout. "
        "Toute généralité applicable à n'importe quelle région est inutile — sois hyper-spécifique à {region}.\n\n"
        "PRIX DU MARCHÉ DANS {region} — SECTION OBLIGATOIRE :\n"
        "Recherche les prix réels pratiqués par les spécialistes en injection de fissures dans {region} en 2024-2025. "
        "Fourchettes TOTALES par fissure (main-d'œuvre + matériaux, injection intérieure standard) :\n"
        "- simple_min / simple_max : fissure capillaire ou sèche, injection polyuréthane intérieure simple\n"
        "- infiltration_min / infiltration_max : fissure avec infiltration ou eau active, injection polyuréthane expansive\n"
        "- struct_min / struct_max : fissure structurale ou déplacement, injection époxy + renfort éventuel\n"
        "Fourchettes typiques QC 2024 pour calibrer (ADAPTE selon compétition et coût de vie de {region}) :\n"
        "  simple : 600–2 500 $ | infiltration active : 1 200–4 500 $ | structurale : 2 500–7 000 $\n\n"
        "TERMINE TON TEXTE PAR CE BLOC EXACT — RÈGLES ABSOLUES :\n"
        "- La ligne `---PRIX---` doit être seule sur sa ligne, après un saut de ligne\n"
        "- Le JSON doit être sur la ligne immédiatement suivante, rien d'autre\n"
        "- Remplace les XXXXX par des entiers sans guillemets ni virgules dans les nombres\n"
        "- Ce bloc doit être la DERNIÈRE chose dans ta réponse\n\n"
        "---PRIX---\n"
        '{{"simple_min": XXXXX, "simple_max": XXXXX, "infiltration_min": XXXXX, "infiltration_max": XXXXX, "struct_min": XXXXX, "struct_max": XXXXX}}'
    ),
    "ceramique": (
        "Tu es un expert en pose de céramique, carrelage résidentiel et marché de la rénovation au Québec. "
        "Ta mission : produire un contexte régional PRÉCIS, FACTUEL et RICHE sur la pose de céramique "
        "dans la région administrative {region} au Québec. "
        "Recherche activement des données locales réelles (carreleurs locaux, forums de rénovation, "
        "coûts de main-d'œuvre régionaux, popularité des types de pose dans {region}).\n\n"
        "Couvre ces 5 points avec des données chiffrées concrètes et propres à {region} :\n"
        "(1) PARC IMMOBILIER ET PROFIL DES PROPRIÉTAIRES de {region} : âge moyen des maisons, "
        "proportion construites avant 1990 (salles de bain vieillissantes, tuiles à remplacer), "
        "valeur médiane des propriétés, types de logements dominants (unifamiliales, condos, duplex) — "
        "ces données déterminent la taille et le budget typique des projets céramique dans {region}.\n"
        "(2) TYPES DE PROJETS CÉRAMIQUE LES PLUS DEMANDÉS DANS {region} : proportion plancher vs salle de bain vs dosseret cuisine, "
        "popularité des douches à l'italienne, tendance grand format (24×24, 12×24) vs format classique, "
        "formats et matériaux les plus commandés dans {region} (céramique standard, porcelaine rectifiée, pierre naturelle). "
        "Ce qui distingue les goûts de {region} de Montréal et Québec.\n"
        "(3) MARCHÉ LOCAL DES CARRELEURS DANS {region} : disponibilité des poseurs de céramique certifiés RBQ, "
        "délais typiques en haute saison (printemps-été), facteurs qui influencent les coûts locaux "
        "(coût de la main-d'œuvre dans {region}, déplacement depuis les grands centres si région éloignée, "
        "disponibilité des matériaux premium en dehors des grands centres).\n"
        "(4) CONDITIONS LOCALES QUI INFLUENCENT LA POSE DANS {region} : présence de sous-planchers en bois "
        "(maisons anciens duplex montréalais vs dalles béton en banlieue), impact du gel-dégel sur les terrasses et patios "
        "extérieurs en céramique dans {region} (gel profond = céramique extérieure spécialisée), "
        "humidité des sous-sols dans {region} (argile, nappe phréatique) qui impose des membranes découplées.\n"
        "(5) FINANCEMENT ET AIDE À LA RÉNOVATION DANS {region} pour la céramique : "
        "programmes RénoVert, crédit logement, financement offert par les carreleurs locaux, "
        "tout programme municipal ou provincial d'aide à la rénovation applicable dans {region}.\n\n"
        "Réponds en 280-320 mots, en français, texte continu structuré par thème, "
        "ton factuel et précis avec des chiffres réels quand disponibles. "
        "Toute généralité applicable à n'importe quelle région du Québec est inutile — sois spécifique à {region}.\n\n"
        "PRIX DU MARCHÉ DANS {region} — SECTION OBLIGATOIRE :\n"
        "Recherche les prix réels pratiqués par les poseurs de céramique dans {region} en 2024-2025. "
        "Fourchettes TOTALES par projet (main-d'œuvre + matériaux standard inclus) :\n"
        "- service1_min / service1_max : plancher en céramique standard (pose complète, pièce type 150-200 pi2)\n"
        "- service2_min / service2_max : réfection salle de bain complète (plancher + murs douche ou bain)\n"
        "- service3_min / service3_max : dosseret de cuisine (métro, mosaïque ou grand format, 20-40 pi2)\n"
        "Fourchettes typiques QC 2024 pour calibrer (ADAPTE selon compétition et coût de vie de {region}) :\n"
        "  plancher : 1 000–6 000 $ | salle de bain : 700–4 000 $ | dosseret : 600–5 000 $\n\n"
        "TERMINE TON TEXTE PAR CE BLOC EXACT — RÈGLES ABSOLUES :\n"
        "- La ligne `---PRIX---` doit être seule sur sa ligne, après un saut de ligne\n"
        "- Le JSON doit être sur la ligne immédiatement suivante, rien d'autre\n"
        "- Remplace les XXXXX par des entiers sans guillemets ni virgules dans les nombres\n"
        "- Ce bloc doit être la DERNIÈRE chose dans ta réponse\n\n"
        "---PRIX---\n"
        '{{"service1_min": XXXXX, "service1_max": XXXXX, "service2_min": XXXXX, "service2_max": XXXXX, "service3_min": XXXXX, "service3_max": XXXXX}}'
    ),
    "beton": (
        "Tu es un expert en travaux de béton résidentiel et commercial au Québec. "
        "Ta mission : produire un contexte régional PRÉCIS, FACTUEL et RICHE sur les travaux de béton "
        "dans la région administrative {region} au Québec. "
        "Recherche activement des données locales réelles (entrepreneurs béton locaux, forums de rénovation, "
        "coûts de main-d'œuvre régionaux, conditions climatiques spécifiques à {region}).\n\n"
        "Couvre ces 5 points avec des données chiffrées concrètes et propres à {region} :\n"
        "(1) IMPACT DU CLIMAT DE {region} SUR LE BÉTON : nombre de cycles gel-dégel par année, "
        "profondeur de gel typique, températures minimales hivernales — ce que ces conditions imposent concrètement "
        "pour les entrées de garage, patios, dalles et fondations (armature obligatoire, dosage eau/ciment, "
        "fibres synthétiques, agents entraîneur d'air, timing du coulage). "
        "Ce qui distingue {region} des autres régions du Québec sur ce point.\n"
        "(2) PARC IMMOBILIER ET PROFIL DES CHANTIERS DE {region} : âge moyen des maisons, proportion avec "
        "fondations en béton coulé vs blocs, superficie typique des entrées de garage dans {region}, "
        "proportion de bungalows vs maisons 2 étages vs chalets — ces données déterminent les projets les plus fréquents.\n"
        "(3) TYPES DE PROJETS BÉTON LES PLUS DEMANDÉS DANS {region} : proportion entrée de garage vs dalle "
        "intérieure vs patio béton vs fondation, popularité du béton estampé vs uni vs coloré dans {region}, "
        "projets commerciaux (stationnements, trottoirs) vs résidentiels. "
        "Ce qui distingue {region} de Montréal et Québec.\n"
        "(4) MARCHÉ DES ENTREPRENEURS BÉTON DANS {region} : nombre estimé d'entreprises RBQ actives, "
        "délais typiques en haute saison (printemps-été), facteurs qui influencent les coûts locaux "
        "(main-d'œuvre, accès aux granulats/agrégats, distance des centrales à béton, "
        "déplacement depuis les grands centres si région éloignée).\n"
        "(5) PERMIS ET RÉGLEMENTATION DANS {region} : permis requis pour fondations, murets, "
        "dalles commerciales, programmes municipaux de réfection (trottoirs, entrées), "
        "tout programme d'aide à la rénovation applicable dans {region} pour les travaux de béton.\n\n"
        "Réponds en 280-320 mots, en français, texte continu structuré par thème, "
        "ton factuel et précis avec des chiffres réels quand disponibles. "
        "Toute généralité applicable à n'importe quelle région du Québec est inutile — sois spécifique à {region}.\n\n"
        "PRIX DU MARCHÉ DANS {region} — SECTION OBLIGATOIRE :\n"
        "Recherche les prix réels pratiqués par les entrepreneurs béton dans {region} en 2024-2025. "
        "Fourchettes TOTALES par projet (main-d'œuvre + matériaux inclus) :\n"
        "- service1_min / service1_max : entrée de garage béton (coulée standard ou estampée, 400-600 pi2)\n"
        "- service2_min / service2_max : dalle béton intérieure (sous-sol, garage, patio, 300-500 pi2)\n"
        "- service3_min / service3_max : réparation béton (fissures, affaissement, scellement)\n"
        "- service4_min / service4_max : fondation ou mur de fondation (coulée complète, maison standard)\n"
        "Fourchettes typiques QC 2024 pour calibrer (ADAPTE selon compétition et coût de vie de {region}) :\n"
        "  entrée garage : 3 000–20 000 $ | dalle : 2 000–14 000 $ | réparation : 500–9 000 $ | fondation : 8 000–45 000 $\n\n"
        "TERMINE TON TEXTE PAR CE BLOC EXACT — RÈGLES ABSOLUES :\n"
        "- La ligne `---PRIX---` doit être seule sur sa ligne, après un saut de ligne\n"
        "- Le JSON doit être sur la ligne immédiatement suivante, rien d'autre\n"
        "- Remplace les XXXXX par des entiers sans guillemets ni virgules dans les nombres\n"
        "- Ce bloc doit être la DERNIÈRE chose dans ta réponse\n\n"
        "---PRIX---\n"
        '{{"service1_min": XXXXX, "service1_max": XXXXX, "service2_min": XXXXX, "service2_max": XXXXX, "service3_min": XXXXX, "service3_max": XXXXX, "service4_min": XXXXX, "service4_max": XXXXX}}'
    ),
    "toiture-plate": (
        "Tu es un expert en toiture plate résidentielle et commerciale au Québec. "
        "Ta mission : produire un contexte régional PRÉCIS, FACTUEL et RICHE sur la toiture plate "
        "dans la région administrative {region} au Québec. "
        "Recherche activement des données locales réelles (couvreurs toit plat locaux, forums de rénovation, "
        "données climatiques d'Environnement Canada pour {region}, types de bâtiments locaux).\n\n"
        "Couvre ces 5 points avec des données chiffrées concrètes et propres à {region} :\n"
        "(1) PARC DE BÂTIMENTS AVEC TOITURE PLATE DE {region} : types de propriétés dominantes avec toit plat "
        "(bungalows des années 1960-1980, condos urbains, immeubles commerciaux, chalets), "
        "proportion du parc résidentiel avec toit plat dans {region}, âge moyen des membranes — "
        "combien de toitures plates arrivent en fin de vie dans les 5-10 prochaines années dans {region}.\n"
        "(2) SYSTÈME DE MEMBRANE DOMINANT DANS {region} : part de marché de la membrane "
        "élastomère bicouche vs TPO vs EPDM dans {region}, pourquoi un système domine (habitudes des couvreurs locaux, "
        "disponibilité des matériaux, coût). Mentionne si les couvreurs de {region} favorisent la torchée vs l'adhésive.\n"
        "(3) PROBLÈMES FRÉQUENTS ET IMPACT CLIMATIQUE DANS {region} : problèmes les plus signalés — "
        "bulles et décollements dus au gel-dégel (nombre de cycles annuels dans {region}), "
        "infiltrations aux joints et solins, accumulation de neige (charge annuelle), "
        "drainage insuffisant. Ce qui distingue {region} des autres régions du Québec sur ce plan.\n"
        "(4) MARCHÉ LOCAL DES COUVREURS TOIT PLAT DANS {region} : nombre estimé d'entrepreneurs spécialisés "
        "toit plat RBQ actifs, délais typiques en haute saison, certifications fabricant "
        "(Soprema, Firestone, IKO Commercial). Saisonnalité des travaux (fenêtre mai-octobre pour {region}).\n"
        "(5) FACTEURS DE COÛT SPÉCIFIQUES À {region} : superficie typique des toits plats résidentiels, "
        "coût d'arrachage de l'ancienne membrane, ajout d'isolant rigide selon les nouvelles normes, "
        "accès en zone urbaine dense vs banlieue.\n\n"
        "Réponds en 280-320 mots, en français, texte continu structuré par thème, "
        "ton factuel et précis avec des chiffres réels quand disponibles. "
        "Toute généralité applicable à n'importe quelle région du Québec est inutile — sois spécifique à {region}.\n\n"
        "PRIX DU MARCHÉ DANS {region} — SECTION OBLIGATOIRE :\n"
        "Recherche les prix réels pratiqués par les couvreurs toit plat dans {region} en 2024-2025. "
        "Fourchettes TOTALES par projet (main-d'œuvre + matériaux inclus) :\n"
        "- service1_min / service1_max : réfection membrane élastomère bicouche (bungalow standard, 1000-1500 pi2)\n"
        "- service2_min / service2_max : réfection membrane TPO ou EPDM (même surface)\n"
        "- service3_min / service3_max : réparation partielle de toit plat (fuite localisée, bulle, décollement)\n"
        "- service4_min / service4_max : inspection et entretien annuel\n"
        "Fourchettes typiques QC 2024 pour calibrer (ADAPTE selon compétition et coût de vie de {region}) :\n"
        "  élastomère : 8 000–30 000 $ | TPO/EPDM : 5 000–20 000 $ | réparation : 800–5 000 $ | inspection : 350–800 $\n\n"
        "TERMINE TON TEXTE PAR CE BLOC EXACT — RÈGLES ABSOLUES :\n"
        "- La ligne `---PRIX---` doit être seule sur sa ligne, après un saut de ligne\n"
        "- Le JSON doit être sur la ligne immédiatement suivante, rien d'autre\n"
        "- Remplace les XXXXX par des entiers sans guillemets ni virgules dans les nombres\n"
        "- Ce bloc doit être la DERNIÈRE chose dans ta réponse\n\n"
        "---PRIX---\n"
        '{{"service1_min": XXXXX, "service1_max": XXXXX, "service2_min": XXXXX, "service2_max": XXXXX, "service3_min": XXXXX, "service3_max": XXXXX, "service4_min": XXXXX, "service4_max": XXXXX}}'
    ),
    "salledebain": (
        "Tu es un expert en rénovation de salle de bain résidentielle au Québec. "
        "Ta mission : produire un contexte régional PRÉCIS, FACTUEL et RICHE sur la rénovation de salle de bain "
        "dans la région administrative {region} au Québec. "
        "Recherche activement des données locales réelles (entrepreneurs RBQ dans {region}, forums de rénovation québécois, "
        "données démographiques de la SCHL, types d'habitations locaux).\n\n"
        "Couvre ces 5 points avec des données chiffrées concrètes et propres à {region} :\n"
        "(1) PARC IMMOBILIER ET SALLES DE BAIN DE {region} : types de propriétés dominantes (maisons unifamiliales, "
        "condos, duplex/triplex, maisons de ville), âge moyen du parc immobilier de {region}, "
        "proportion de salles de bain vieillissantes (20+ ans) qui nécessitent une rénovation dans les 5 ans — "
        "pourquoi la salle de bain est le projet de rénovation le plus rentable dans {region}.\n"
        "(2) TYPES DE RÉNOVATIONS LES PLUS DEMANDÉES DANS {region} : popularité de la douche italienne sans rebord "
        "vs remplacement de baignoire, rénovations complètes clé en main vs partielles, tendance au plancher chauffant "
        "sous carrelage dans {region}, popularité des salles de bain luxe (bain autoportant, robinetterie haut de gamme).\n"
        "(3) MATÉRIAUX ET TENDANCES DANS {region} : carrelage grand format vs mosaïque vs vinyle de luxe (LVT), "
        "couleurs et styles populaires dans {region} (blanc mat, gris ardoise, vert sauge), vanités flottantes "
        "vs sur pied, popularité de la douche à vitre semi-frameless. Ce qui se commande le plus dans {region}.\n"
        "(4) MARCHÉ LOCAL DES ENTREPRENEURS SALLE DE BAIN DANS {region} : nombre estimé d'entrepreneurs RBQ "
        "actifs en rénovation salle de bain, délais typiques en haute saison (printemps-automne), "
        "importance de la plomberie sous-traitée (maître plombier CMMTQ), disponibilité des showrooms de salle de bain "
        "et centres de carrelage dans {region}.\n"
        "(5) FACTEURS DE COÛT SPÉCIFIQUES À {region} : coût du carrelage posé (main-d'œuvre + matériaux), "
        "impact des travaux de plomberie (déplacement de tuyaux, mise aux normes), surcoût en condo (bruit, "
        "règlements de copropriété, accès restreint), coût de l'imperméabilisation (membrane Schluter/Kerdi), "
        "saisonnalité des prix dans {region}.\n\n"
        "Réponds en 280-320 mots, en français, texte continu structuré par thème, "
        "ton factuel et précis avec des chiffres réels quand disponibles. "
        "Toute généralité applicable à n'importe quelle région du Québec est inutile — sois spécifique à {region}.\n\n"
        "PRIX DU MARCHÉ DANS {region} — SECTION OBLIGATOIRE :\n"
        "Recherche les prix réels pratiqués par les entrepreneurs salle de bain dans {region} en 2024-2025. "
        "Fourchettes TOTALES par projet (main-d'œuvre + matériaux inclus) :\n"
        "- service1_min / service1_max : rénovation partielle (douche ou baignoire seulement, carrelage et accessoires)\n"
        "- service2_min / service2_max : réfection complète de salle de bain (tous les éléments, clé en main)\n"
        "- service3_min / service3_max : salle de bain luxe (matériaux haut de gamme, bain autoportant, douche italienne)\n"
        "- service4_min / service4_max : carrelage seul (plancher ou mur, main-d'œuvre + matériaux)\n"
        "Fourchettes typiques QC 2024 pour calibrer (ADAPTE selon compétition et coût de vie de {region}) :\n"
        "  partielle : 3 500–12 000 $ | complète : 8 000–28 000 $ | luxe : 18 000–45 000 $ | carrelage : 1 500–6 000 $\n\n"
        "TERMINE TON TEXTE PAR CE BLOC EXACT — RÈGLES ABSOLUES :\n"
        "- La ligne `---PRIX---` doit être seule sur sa ligne, après un saut de ligne\n"
        "- Le JSON doit être sur la ligne immédiatement suivante, rien d'autre\n"
        "- Remplace les XXXXX par des entiers sans guillemets ni virgules dans les nombres\n"
        "- Ce bloc doit être la DERNIÈRE chose dans ta réponse\n\n"
        "---PRIX---\n"
        '{{"service1_min": XXXXX, "service1_max": XXXXX, "service2_min": XXXXX, "service2_max": XXXXX, "service3_min": XXXXX, "service3_max": XXXXX, "service4_min": XXXXX, "service4_max": XXXXX}}'
    ),
    "cloture": (
        "Tu es un expert en installation de clôtures résidentielles et commerciales au Québec. "
        "Ta mission : produire un contexte régional PRÉCIS, FACTUEL et RICHE sur le marché de la clôture "
        "dans la région administrative {region} au Québec. "
        "Recherche activement des données locales réelles (entrepreneurs en clôture dans {region}, fournisseurs locaux, "
        "réglementations municipales, types de propriétés dominantes, conditions climatiques).\n\n"
        "Couvre ces 5 points avec des données chiffrées concrètes et propres à {region} :\n"
        "(1) PARC RÉSIDENTIEL ET BESOINS EN CLÔTURE À {region} : types de propriétés dominantes (bungalows avec cour, "
        "maisons en rangée, condos avec terrain), proportion de propriétés avec cour clôturée dans {region}, "
        "principales motivations (sécurité enfants/animaux, intimité, délimitation de terrain, esthétique). "
        "Pourquoi la clôture est un investissement courant dans {region}.\n"
        "(2) TYPES DE CLÔTURES LES PLUS POPULAIRES DANS {region} : popularité bois traité vs vinyle vs aluminium "
        "vs chaîne maillée, préférences esthétiques locales (couleurs, hauteurs, styles palissade vs lattice), "
        "tendance aux clôtures mixtes (aluminium devant, bois derrière), impact des règlements municipaux sur la hauteur "
        "et le type dans {region}.\n"
        "(3) CONDITIONS CLIMATIQUES ET DURABILITÉ À {region} : impact du cycle gel-dégel sur les poteaux en bois "
        "vs béton vs aluminium dans {region}, profondeur de gel requise pour les fondations de poteaux, "
        "durabilité du vinyle face aux grands froids, résistance du bois traité sous-pression dans {region}, "
        "entretien annuel (teinture, remplacement de planches) propre au climat de {region}.\n"
        "(4) MARCHÉ LOCAL DES ENTREPRENEURS EN CLÔTURE À {region} : nombre estimé d'entrepreneurs actifs, "
        "délais typiques en haute saison (mai-septembre), fournisseurs de matériaux connus dans {region} "
        "(cours à bois, centres de rénovation), importance des permis de construction pour les clôtures "
        "dans les municipalités de {region}.\n"
        "(5) FACTEURS DE COÛT SPÉCIFIQUES À {region} : coût de la main-d'œuvre d'installation au pi linéaire, "
        "impact du terrain (pente, roche affleurante, sol argileux), coût du retrait de l'ancienne clôture, "
        "surcoût pour les portails et quincaillerie, variations saisonnières des prix dans {region}.\n\n"
        "Réponds en 280-320 mots, en français, texte continu structuré par thème, "
        "ton factuel et précis avec des chiffres réels quand disponibles. "
        "Toute généralité applicable à n'importe quelle région du Québec est inutile — sois spécifique à {region}.\n\n"
        "PRIX DU MARCHÉ DANS {region} — SECTION OBLIGATOIRE :\n"
        "Recherche les prix réels pratiqués par les entrepreneurs en clôture dans {region} en 2024-2025. "
        "Fourchettes TOTALES par projet (main-d'œuvre + matériaux inclus, pour 100 pi linéaires typiques) :\n"
        "- service1_min / service1_max : clôture en bois traité (installation complète, 100 pi)\n"
        "- service2_min / service2_max : clôture en vinyle (installation complète, 100 pi)\n"
        "- service3_min / service3_max : clôture en aluminium (installation complète, 100 pi)\n"
        "- service4_min / service4_max : clôture composite ou chaîne maillée (installation complète, 100 pi)\n"
        "Fourchettes typiques QC 2024 pour calibrer (ADAPTE selon compétition et coût de vie de {region}) :\n"
        "  bois : 3 500–12 000 $ | vinyle : 1 800–6 000 $ | aluminium : 1 200–4 500 $ | composite/chaîne : 2 500–8 000 $\n\n"
        "TERMINE TON TEXTE PAR CE BLOC EXACT — RÈGLES ABSOLUES :\n"
        "- La ligne `---PRIX---` doit être seule sur sa ligne, après un saut de ligne\n"
        "- Le JSON doit être sur la ligne immédiatement suivante, rien d'autre\n"
        "- Remplace les XXXXX par des entiers sans guillemets ni virgules dans les nombres\n"
        "- Ce bloc doit être la DERNIÈRE chose dans ta réponse\n\n"
        "---PRIX---\n"
        '{{"service1_min": XXXXX, "service1_max": XXXXX, "service2_min": XXXXX, "service2_max": XXXXX, "service3_min": XXXXX, "service3_max": XXXXX, "service4_min": XXXXX, "service4_max": XXXXX}}'
    ),
    "decontamination": (
        "Tu es un expert en décontamination professionnelle, qualité de l'air intérieur (IEQ) et salubrité résidentielle au Québec. "
        "Ta mission : produire un contexte régional PRÉCIS, FACTUEL et RICHE sur la décontamination dans la région administrative {region} au Québec. "
        "Recherche activement des données locales réelles (décontamineurs certifiés IEQ dans {region}, types de contaminations fréquentes, bâtiments à risque, réglementations).\n\n"
        "Couvre ces 5 points avec des données chiffrées concrètes et propres à {region} :\n"
        "(1) PARC IMMOBILIER ET RISQUES DE CONTAMINATION À {region} : proportion de maisons construites avant 1980 (risque amiante, plomb, moisissures chroniques), proportion avant 1990, âge moyen du parc, densité de logements locatifs (souvent moins bien entretenus), présence d'immeubles commerciaux ou institutionnels anciens. "
        "Quel pourcentage estimé des propriétés de {region} pourrait nécessiter une inspection IEQ.\n"
        "(2) CLIMAT ET HUMIDITÉ À {region} : taux d'humidité relative moyen en hiver et en été, nombre de journées de gel-dégel, précipitations annuelles, problèmes d'infiltration d'eau spécifiques à {region} (nappe phréatique, crues printanières, zones inondables), impact sur la croissance de moisissures dans les sous-sols et vides sanitaires.\n"
        "(3) PRÉVALENCE ET TYPES DE CONTAMINATIONS DANS {region} : types de contaminations les plus fréquents (moisissures, amiante dans les constructions avant 1980, radon — noter si {region} est dans une zone à risque radon selon Santé Canada), bactéries, contaminations post-sinistre (dégâts d'eau), types de propriétés les plus touchées (sous-sol, vide sanitaire, toiture, conduits de ventilation).\n"
        "(4) RÉGLEMENTATION ET CERTIFICATIONS DANS {region} : normes CNESST pour le retrait d'amiante (scaphandre, confinement, manifeste de transport), exigences INSPQ sur les moisissures, obligations des propriétaires bailleurs en cas de moisissures détectées (Loi sur le logement), rôle de la Régie du logement, permis municipaux pour travaux de décontamination majeurs, présence d'inspecteurs certifiés IEQ/IEDQ dans {region}.\n"
        "(5) MARCHÉ DES DÉCONTAMINEURS DANS {region} : nombre estimé d'entreprises certifiées IEQ actives, délais typiques pour une inspection d'urgence vs planifiée, coût typique d'une inspection IEQ dans {region}, facteurs qui font varier les prix (superficie contaminée, type de contaminant, urgence, accès au chantier), couverture d'assurance habitation pour décontamination dans {region}.\n\n"
        "Réponds en 280-320 mots, en français, texte continu structuré par thème, "
        "ton factuel et précis avec des chiffres réels quand disponibles. "
        "Toute généralité applicable à n'importe quelle région du Québec est inutile — sois spécifique à {region}.\n\n"
        "PRIX DU MARCHÉ DANS {region} — SECTION OBLIGATOIRE :\n"
        "Recherche les prix réels pratiqués par les décontamineurs certifiés IEQ dans {region} en 2024-2025. "
        "Fourchettes TOTALES par projet :\n"
        "- service1_min / service1_max : décontamination complète (moisissures ou amiante, résidentiel)\n"
        "- service2_min / service2_max : inspection certifiée IEQ (rapport officiel inclus)\n"
        "- service3_min / service3_max : prélèvements laboratoire (analyse mycologique ou amiante)\n"
        "- service4_min / service4_max : décontamination post-sinistre / dégât d'eau\n"
        "Fourchettes typiques QC 2024 pour calibrer (ADAPTE selon compétition et coût de vie de {region}) :\n"
        "  décontamination complète : 600–5 500 $ | inspection IEQ : 200–1 500 $ | prélèvements : 125–800 $ | post-sinistre : 500–3 500 $\n\n"
        "TERMINE TON TEXTE PAR CE BLOC EXACT — RÈGLES ABSOLUES :\n"
        "- La ligne `---PRIX---` doit être seule sur sa ligne, après un saut de ligne\n"
        "- Le JSON doit être sur la ligne immédiatement suivante, rien d'autre\n"
        "- Remplace les XXXXX par des entiers sans guillemets ni virgules dans les nombres\n"
        "- Ce bloc doit être la DERNIÈRE chose dans ta réponse\n\n"
        "---PRIX---\n"
        '{{"service1_min": XXXXX, "service1_max": XXXXX, "service2_min": XXXXX, "service2_max": XXXXX, "service3_min": XXXXX, "service3_max": XXXXX, "service4_min": XXXXX, "service4_max": XXXXX}}'
    ),
    "paysagement": (
        "Tu es un expert en aménagement paysager résidentiel et commercial au Québec. "
        "Ta mission : produire un contexte régional PRÉCIS, FACTUEL et RICHE sur le marché du paysagement "
        "dans la région administrative {region} au Québec. "
        "Recherche activement des données locales réelles (entrepreneurs paysagistes certifiés dans {region}, types de projets dominants, conditions climatiques spécifiques, réglementations municipales).\n\n"
        "Couvre ces 5 points avec des données chiffrées concrètes et propres à {region} :\n"
        "(1) PROFIL RÉSIDENTIEL DE {region} ET SES BESOINS EN PAYSAGEMENT : types de propriétés dominantes (bungalows avec terrain, maisons unifamiliales en banlieue, chalets avec lac, condos avec cour arrière), superficie moyenne des terrains dans {region}, proportion de propriétaires qui investissent dans l'aménagement paysager vs ceux qui entretiennent uniquement la pelouse, âge moyen du parc immobilier (les terrains des maisons des années 1960-1990 arrivent souvent à un âge critique pour une refonte complète).\n"
        "(2) IMPACT DU CLIMAT DE {region} SUR LES PROJETS DE PAYSAGEMENT : durée de la saison de jardinage (nombre de jours de gel, date moyenne des dernières gelées), types de végétaux qui résistent le mieux dans {region} (conifères, arbustes indigènes, vivaces robustes vs annuelles), impact de la profondeur de gel sur les aménagements durs (patios, murets, dalles — fondation requise), enjeux de drainage et d'érosion spécifiques au sol de {region} (sol argileux vs sablonneux vs rocheux).\n"
        "(3) TYPES DE PROJETS LES PLUS DEMANDÉS DANS {region} : proportion des projets par type — gazon en plaques ou semé (marché le plus courant), terrassement et nivellement, aménagement de plate-bandes et massifs, allées et entrées (pavé uni, asphalte, dalle de béton), terrasses en bois ou composite, piscines hors-terre vs creusées, pergolas et abris de jardin, murets et bordures. Ce qui distingue {region} des grands centres urbains comme Montréal.\n"
        "(4) MARCHÉ DES PAYSAGISTES DANS {region} : nombre estimé d'entreprises de paysagement actives et certifiées ASNQ (Association des professionnels en horticulture du Québec), délais typiques en haute saison (avril à juin — délais de 4 à 10 semaines), disponibilité de la main-d'oeuvre spécialisée dans {region}, saisonnalité des projets (gazon au printemps, aménagements majeurs printemps-été, entretien automne), importance des contrats d'entretien annuels.\n"
        "(5) FACTEURS DE COÛT SPÉCIFIQUES À {region} : coût de la main-d'oeuvre locale en paysagement, distance des pépinières et fournisseurs de matériaux (pavé Techo-Bloc, bois traité, pierre naturelle), impact du terrain (pente, roc affleurant, sol argileux nécessitant excavation), transport des déblais et des matériaux dans {region} (zones rurales éloignées vs zones suburbaines avec accès facile).\n\n"
        "Réponds en 280-320 mots, en français, texte continu structuré par thème, "
        "ton factuel et précis avec des chiffres réels quand disponibles. "
        "Toute généralité applicable à n'importe quelle région du Québec est inutile — sois spécifique à {region}.\n\n"
        "PRIX DU MARCHÉ DANS {region} — SECTION OBLIGATOIRE :\n"
        "Recherche les prix réels pratiqués par les paysagistes dans {region} en 2024-2025. "
        "Fourchettes TOTALES par projet (main-d'œuvre + matériaux inclus) :\n"
        "- service1_min / service1_max : aménagement paysager complet (terrain résidentiel standard, gazon + plate-bandes + allée)\n"
        "- service2_min / service2_max : gazon en plaques installé (terrain moyen, préparation incluse)\n"
        "- service3_min / service3_max : terrasse en bois traité ou composite (20-40 m²)\n"
        "- service4_min / service4_max : projet haut de gamme (piscine creusée + paysagement, pergola, murets naturels)\n"
        "Fourchettes typiques QC 2024 pour calibrer (ADAPTE selon compétition et coût de vie de {region}) :\n"
        "  aménagement complet : 5 000–45 000 $ | gazon plaques : 800–6 500 $ | terrasse : 1 500–12 000 $ | haut de gamme : 12 000–55 000 $\n\n"
        "TERMINE TON TEXTE PAR CE BLOC EXACT — RÈGLES ABSOLUES :\n"
        "- La ligne `---PRIX---` doit être seule sur sa ligne, après un saut de ligne\n"
        "- Le JSON doit être sur la ligne immédiatement suivante, rien d'autre\n"
        "- Remplace les XXXXX par des entiers sans guillemets ni virgules dans les nombres\n"
        "- Ce bloc doit être la DERNIÈRE chose dans ta réponse\n\n"
        "---PRIX---\n"
        '{{"service1_min": XXXXX, "service1_max": XXXXX, "service2_min": XXXXX, "service2_max": XXXXX, "service3_min": XXXXX, "service3_max": XXXXX, "service4_min": XXXXX, "service4_max": XXXXX}}'
    ),
    "electricien": (
        "Tu es un expert en électricité résidentielle et commerciale au Québec, et en marché de la construction. "
        "Ta mission : produire un contexte régional PRÉCIS, FACTUEL et RICHE sur le marché des électriciens "
        "dans la région administrative {region} au Québec. "
        "Recherche activement des données locales réelles (maîtres électriciens CMEQ actifs dans {region}, types de travaux fréquents, réglementations locales, prix du marché).\n\n"
        "Couvre ces 5 points avec des données chiffrées concrètes et propres à {region} :\n"
        "(1) PARC IMMOBILIER ET INFRASTRUCTURE ÉLECTRIQUE DE {region} : âge moyen des maisons (les constructions d'avant 1990 ont souvent des panneaux électriques vétustes à 100A ou 60A qui nécessitent une mise à niveau), proportion de maisons unifamiliales vs condos vs immeubles locatifs, densité de construction industrielle et commerciale dans {region} (génère des travaux électriques plus importants), proportion de maisons avec chauffage électrique (plinthes, fournaise, thermopompe) — ces données expliquent la charge électrique typique des propriétés de {region}.\n"
        "(2) TYPES DE TRAVAUX ÉLECTRIQUES LES PLUS FRÉQUENTS DANS {region} : mise aux normes de panneaux électriques (60A ou 100A → 200A), installation de circuits GFCI et AFCI dans salles de bain et cuisines, ajout de prises pour véhicule électrique (EVSE niveau 2 — demande croissante dans {region}), travaux pour rénovation cuisine et salle de bain (circuits dédiés, hotte, laveuse-sécheuse), installation de thermopompes et climatiseurs (circuits 240V dédiés), urgences (coupure de courant, court-circuit, panne tableau). Proportion des travaux d'urgence vs planifiés dans {region}.\n"
        "(3) RÉGLEMENTATION ÉLECTRIQUE DANS {region} : exigences du Code canadien de l'électricité (CCÉ) et de l'Hydro-Québec pour les raccordements dans {region}, rôle de la CMEQ (Corporation des maîtres électriciens du Québec), permis d'Hydro-Québec obligatoire pour certains travaux, inspections municipales dans les municipalités de {region}, conformité obligatoire lors d'une vente immobilière dans {region}.\n"
        "(4) MARCHÉ DES ÉLECTRICIENS DANS {region} : nombre estimé de maîtres électriciens CMEQ actifs, délais typiques pour une soumission en haute saison (printemps-automne — pénurie de main-d'œuvre électrique dans plusieurs régions), délais pour une urgence électrique dans {region} (24h en milieu urbain vs 2-5 jours en milieu rural), pénurie de compagnons électriciens et impact sur les délais.\n"
        "(5) FACTEURS DE COÛT SPÉCIFIQUES À {region} : taux horaire des maîtres électriciens dans {region} (tarif journalier, frais de déplacement hors zone urbaine), coût des matériaux (panneaux électriques Siemens/Square D, fil Romex, disjoncteurs AFCI), surcoût pour les maisons avec amiante ou constructions complexes, tarification des urgences (prime de nuit et de week-end dans {region}).\n\n"
        "Réponds en 280-320 mots, en français, texte continu structuré par thème, "
        "ton factuel et précis avec des chiffres réels quand disponibles. "
        "Toute généralité applicable à n'importe quelle région du Québec est inutile — sois spécifique à {region}.\n\n"
        "PRIX DU MARCHÉ DANS {region} — SECTION OBLIGATOIRE :\n"
        "Recherche les prix réels pratiqués par les maîtres électriciens dans {region} en 2024-2025. "
        "Fourchettes TOTALES par projet (main-d'œuvre + matériaux inclus) :\n"
        "- service1_min / service1_max : petits travaux électriques (prises, interrupteurs, luminaires, circuit ajouté)\n"
        "- service2_min / service2_max : mise aux normes et tableau électrique (100A → 200A, remplacement panneau)\n"
        "- service3_min / service3_max : grande installation (câblage complet, rénovation majeure, ajout de service)\n"
        "- service4_min / service4_max : urgence et dépannage (intervention prioritaire, diagnostic, réparation urgente)\n"
        "Fourchettes typiques QC 2024 pour calibrer (ADAPTE selon compétition et coût de vie de {region}) :\n"
        "  petits travaux : 150–1 200 $ | tableau électrique : 1 500–6 000 $ | grande installation : 3 500–9 000 $ | urgence : 300–2 500 $\n\n"
        "TERMINE TON TEXTE PAR CE BLOC EXACT — RÈGLES ABSOLUES :\n"
        "- La ligne `---PRIX---` doit être seule sur sa ligne, après un saut de ligne\n"
        "- Le JSON doit être sur la ligne immédiatement suivante, rien d'autre\n"
        "- Remplace les XXXXX par des entiers sans guillemets ni virgules dans les nombres\n"
        "- Ce bloc doit être la DERNIÈRE chose dans ta réponse\n\n"
        "---PRIX---\n"
        '{{"service1_min": XXXXX, "service1_max": XXXXX, "service2_min": XXXXX, "service2_max": XXXXX, "service3_min": XXXXX, "service3_max": XXXXX, "service4_min": XXXXX, "service4_max": XXXXX}}'
    ),
    "portes-fenetres": (
        "Tu es un expert en remplacement de fenêtres et portes résidentielles au Québec. "
        "Ta mission : produire un contexte régional PRÉCIS, FACTUEL et RICHE sur le marché des fenêtres et portes extérieures "
        "dans la région administrative {region} au Québec. "
        "Recherche activement des données locales réelles (installateurs certifiés dans {region}, types de produits dominants, programmes d'aide, prix du marché).\n\n"
        "Couvre ces 5 points avec des données chiffrées concrètes et propres à {region} :\n"
        "(1) PARC IMMOBILIER DE {region} ET ÉTAT DES FENÊTRES ET PORTES : âge moyen des maisons, proportion construites avant 1990 (fenêtres originales en simple ou double vitrage en fin de vie), proportion avant 2000 (fenêtres de première génération PVC qui se déforment et perdent leur étanchéité), types d'habitations dominants (bungalows avec beaucoup de fenêtres en façade, maisons à étages, chalets, condos). Estimation du nombre de propriétés dans {region} dont les fenêtres arriveront en fin de vie dans les 5-10 prochaines années.\n"
        "(2) IMPACT DU CLIMAT DE {region} SUR LES FENÊTRES ET PORTES : températures minimales typiques en janvier-février (justifient le triple vitrage dans les zones les plus froides de {region}), nombre de jours sous -20°C, accumulation de neige contre les portes et fenêtres, condensation intérieure sur les vitrages de mauvaise qualité, pont thermique sur les vieux cadres en aluminium, vent dominant et zones d'exposition critique. Ces données expliquent pourquoi des fenêtres certifiées ÉnerGuide/ENERGY STAR avec cote ER50+ sont particulièrement pertinentes dans {region}.\n"
        "(3) PROGRAMMES D'AIDE FINANCIÈRE ACCESSIBLES DANS {region} : Rénoclimat (montants actuels pour fenêtres et portes extérieures certifiées, conditions d'admissibilité, cotes ER minimales), Hydro-Québec LogisVert (si applicable aux fenêtres), programme fédéral RCEE (crédit remboursable + prêt 0% pour rénovations écoénergétiques), Novoclimat 2.0 pour les nouvelles constructions dans {region}, tout programme municipal ou régional spécifique à {region}. Montants réels et conditions.\n"
        "(4) TYPES DE PRODUITS PRÉFÉRÉS DANS {region} : PVC blanc standard (le plus courant), hybride bois-PVC ou bois-aluminium (segments haut de gamme dans {region}), fenêtres en aluminium (usage commercial, chalets — marché de niche), triple vitrage (proportion dans {region} vs double vitrage), styles les plus demandés (guillotine, battant, fixe, jalousie — selon le type de maison dominant dans {region}), marques et fabricants présents dans {region} (Fenêtres Verdun, Kohltech, Atis, Fenêtres Panorama, produits locaux).\n"
        "(5) MARCHÉ DES INSTALLATEURS DANS {region} : nombre estimé d'installateurs certifiés RBQ actifs, délais typiques en haute saison (printemps-été — délais de 6 à 16 semaines entre la commande et la pose), saisonnalité des travaux (installation possible en hiver mais conditions de calfeutrage plus difficiles), facteurs qui font varier le délai d'approvisionnement dans {region} (distance des manufacturiers, produits sur commande).\n\n"
        "Réponds en 280-320 mots, en français, texte continu structuré par thème, "
        "ton factuel et précis avec des chiffres réels quand disponibles. "
        "Toute généralité applicable à n'importe quelle région du Québec est inutile — sois spécifique à {region}.\n\n"
        "PRIX DU MARCHÉ DANS {region} — SECTION OBLIGATOIRE :\n"
        "Recherche les prix réels pratiqués par les installateurs de fenêtres et portes dans {region} en 2024-2025. "
        "Fourchettes TOTALES par projet (fourniture + installation incluses) :\n"
        "- service1_min / service1_max : remplacement d'une fenêtre standard (PVC double vitrage, taille courante 60x36 po)\n"
        "- service2_min / service2_max : remplacement d'une porte extérieure (porte d'entrée acier/fibre de verre avec vitrage)\n"
        "- service3_min / service3_max : porte-fenêtre coulissante ou patio (standard ou prestige)\n"
        "- service4_min / service4_max : remplacement complet maison (8-14 fenêtres + portes, projet global)\n"
        "Fourchettes typiques QC 2024 pour calibrer (ADAPTE selon compétition et coût de vie de {region}) :\n"
        "  fenêtre : 800–3 500 $ | porte extérieure : 400–2 000 $ | porte-fenêtre : 1 200–5 000 $ | maison complète : 2 500–12 000 $\n\n"
        "TERMINE TON TEXTE PAR CE BLOC EXACT — RÈGLES ABSOLUES :\n"
        "- La ligne `---PRIX---` doit être seule sur sa ligne, après un saut de ligne\n"
        "- Le JSON doit être sur la ligne immédiatement suivante, rien d'autre\n"
        "- Remplace les XXXXX par des entiers sans guillemets ni virgules dans les nombres\n"
        "- Ce bloc doit être la DERNIÈRE chose dans ta réponse\n\n"
        "---PRIX---\n"
        '{{"service1_min": XXXXX, "service1_max": XXXXX, "service2_min": XXXXX, "service2_max": XXXXX, "service3_min": XXXXX, "service3_max": XXXXX, "service4_min": XXXXX, "service4_max": XXXXX}}'
    ),
    "fosseseptique": (
        "Tu es un expert en systèmes d'assainissement autonome (fosses septiques, champs d'épuration) et en réglementation environnementale au Québec. "
        "Ta mission : produire un contexte régional PRÉCIS, FACTUEL et RICHE sur les fosses septiques "
        "dans la région administrative {region} au Québec. "
        "Recherche activement des données locales réelles (entrepreneurs en systèmes septiques MAMH dans {region}, types de systèmes courants, réglementations locales, problèmes fréquents).\n\n"
        "Couvre ces 5 points avec des données chiffrées concrètes et propres à {region} :\n"
        "(1) PARC DE SYSTÈMES SEPTIQUES DANS {region} : proportion de propriétés raccordées au réseau d'égout municipal vs avec système autonome (rural = plus grand pourcentage de fosses septiques), âge moyen du parc de fosses septiques dans {region} (les systèmes installés dans les années 1960-1990 arrivent en fin de vie et doivent être remplacés selon le Règlement Q-2, r.22), types de systèmes présents (fosse septique classique + champ d'épuration, fosse en béton vs polyéthylène, systèmes à compostage pour zones sans champ). Estimation du pourcentage de systèmes non conformes dans {region}.\n"
        "(2) RÉGLEMENTATION ET CONFORMITÉ DANS {region} : Règlement sur l'évacuation et le traitement des eaux usées des résidences isolées (Q-2, r.22 du MELCCFP), obligations de conformité lors d'une vente immobilière dans {region} (le vendeur doit fournir une déclaration de conformité du système septique depuis 2021), rôle des inspecteurs municipaux et du MAMH dans les MRC de {region}, délais pour se mettre aux normes après une inspection de non-conformité, amendes et recours possibles. Quel pourcentage de transactions immobilières dans {region} révèle des systèmes non conformes.\n"
        "(3) SOLS ET CONDITIONS D'INSTALLATION DANS {region} : type de sol dominant dans {region} et son impact sur le dimensionnement du champ d'épuration (sol argileux peu perméable = surface requise plus grande, sol sablonneux = risque de contamination de la nappe, roc affleurant = systèmes en milieu difficile), profondeur de gel et impact sur les canalisations et la fosse (protection requise), nappe phréatique et zones inondables dans {region} (zones où le champ d'épuration est problématique ou impossible), étude de sol requise pour tout nouveau système dans {region}.\n"
        "(4) PROBLÈMES FRÉQUENTS ET URGENCES DANS {region} : problèmes les plus signalés (refoulement de la fosse, odeurs persistantes, champ d'épuration saturé par les pluies printanières ou la fonte des neiges dans {region}, fosse trop petite pour la maison, drain de percolation bouché), fréquence des urgences en saison estivale (chalets occupés le week-end), impact de l'utilisation intensive des résidences secondaires dans {region}.\n"
        "(5) MARCHÉ DES ENTREPRENEURS EN FOSSES SEPTIQUES DANS {region} : nombre estimé d'entrepreneurs certifiés actifs dans {region}, délais typiques pour une soumission et le début des travaux, saisonnalité (travaux impossibles en sol gelé — fenêtre avril à novembre dans {region}), fréquence recommandée de vidange (tous les 2 ans selon le MELCCFP — quel % des propriétaires de {region} respecte cette fréquence).\n\n"
        "Réponds en 290-330 mots, en français, texte continu structuré par thème, "
        "ton factuel et précis avec des chiffres réels quand disponibles. "
        "Toute généralité applicable à n'importe quelle région du Québec est inutile — sois spécifique à {region}.\n\n"
        "PRIX DU MARCHÉ DANS {region} — SECTION OBLIGATOIRE :\n"
        "Recherche les prix réels pratiqués par les entrepreneurs en fosses septiques dans {region} en 2024-2025. "
        "Fourchettes TOTALES par projet (main-d'œuvre + matériaux + excavation inclus) :\n"
        "- service1_min / service1_max : installation fosse septique complète (fosse + champ d'épuration, résidence standard)\n"
        "- service2_min / service2_max : remplacement fosse septique (échange fosse seulement, champ existant conforme)\n"
        "- service3_min / service3_max : vidange et pompage (entretien régulier, fosse standard 3 000-4 500 litres)\n"
        "- service4_min / service4_max : inspection, rapport de conformité et entretien\n"
        "Fourchettes typiques QC 2024 pour calibrer (ADAPTE selon compétition et coût de vie de {region}) :\n"
        "  installation complète : 12 000–30 000 $ | remplacement fosse : 8 000–22 000 $ | vidange : 250–550 $ | inspection/entretien : 300–700 $\n\n"
        "TERMINE TON TEXTE PAR CE BLOC EXACT — RÈGLES ABSOLUES :\n"
        "- La ligne `---PRIX---` doit être seule sur sa ligne, après un saut de ligne\n"
        "- Le JSON doit être sur la ligne immédiatement suivante, rien d'autre\n"
        "- Remplace les XXXXX par des entiers sans guillemets ni virgules dans les nombres\n"
        "- Ce bloc doit être la DERNIÈRE chose dans ta réponse\n\n"
        "---PRIX---\n"
        '{{"service1_min": XXXXX, "service1_max": XXXXX, "service2_min": XXXXX, "service2_max": XXXXX, "service3_min": XXXXX, "service3_max": XXXXX, "service4_min": XXXXX, "service4_max": XXXXX}}'
    ),
    "nettoyage-conduits": (
        "Tu es un expert en nettoyage de conduits de ventilation, systèmes CVAC et qualité de l'air intérieur au Québec. "
        "Ta mission : produire un contexte régional PRÉCIS, FACTUEL et RICHE sur le nettoyage de conduits "
        "dans la région administrative {region} au Québec. "
        "Recherche activement des données locales réelles (entreprises de nettoyage de conduits certifiées NADCA dans {region}, types de systèmes courants, réglementations, prix du marché).\n\n"
        "Couvre ces 5 points avec des données chiffrées concrètes et propres à {region} :\n"
        "(1) PARC DE SYSTÈMES DE VENTILATION DANS {region} : proportion de maisons avec système de conduits (chauffage à air pulsé, thermopompe centrale, climatisation centrale) vs chauffage électrique sans conduits (plinthes — pas de conduits à nettoyer), proportion de maisons construites avant 2000 avec conduits d'origine (poussière, vermiculite potentielle, moisissures), types de systèmes dominants dans {region} (fournaise sur conduits d'air, thermopompe centrale, échangeur d'air — VRC ou ERV), proportion de conduits en métal galvanisé vs flexible en plastique (ce dernier étant plus sujet à l'accumulation de débris).\n"
        "(2) CONDITIONS LOCALES QUI ACCÉLÈRENT L'ENCRASSEMENT DES CONDUITS À {region} : niveau d'humidité relative (impact direct sur la croissance de moisissures dans les conduits humides ou mal isolés), présence de pollens et de spores dans {region} (forêts mixtes, zones agricoles, érables en floraison printanière), construction récente (poussière de construction dans les conduits neufs — recommandation de nettoyage dans l'année suivant la construction), présence d'animaux domestiques (poils et squames — impact sur le débit d'air), rénovations sans protection des conduits.\n"
        "(3) PROBLÈMES DE QUALITÉ DE L'AIR INTÉRIEUR SPÉCIFIQUES À {region} : taux de moisissures dans les sous-sols de {region} (humidité printanière, fonte des neiges), présence de vermiculite dans les maisons construites avant 1988 (risque amiante dans certaines constructions de {region}), radon dans les zones géologiques à risque de {region} (se diffuse dans les conduits de ventilation), contamination par les rongeurs (fientes dans les conduits inaccessibles), impact des longs hivers de {region} sur la qualité de l'air intérieur (maisons hermétiquement fermées 6-8 mois par an).\n"
        "(4) MARCHÉ DU NETTOYAGE DE CONDUITS DANS {region} : nombre estimé d'entreprises actives et certifiées NADCA (National Air Duct Cleaners Association), délais typiques pour une intervention planifiée (2-4 semaines en haute saison automne-hiver dans {region}), délais pour une urgence (odeurs, contamination visible), distinction entre nettoyage professionnel certifié NADCA (aspirateur industriel HEPA + brosses rotatives) et nettoyage low-cost (souffleur manuel inefficace — problème répandu dans {region}), fréquence recommandée (tous les 3-5 ans ou après dégâts d'eau, rénovations, infestation).\n"
        "(5) COÛTS ET FACTEURS DE VARIATION DANS {region} : taux horaire des techniciens certifiés NADCA dans {region}, facteurs qui font varier le prix (superficie de la maison et nombre de bouches d'air, linéaires de conduits, nombre d'étages, état d'encrassement, distance du fournisseur si zone rurale éloignée), coût supplémentaire pour le traitement antimicrobien (optionnel mais souvent recommandé dans les zones humides de {region}), prix du nettoyage de conduit de cheminée (appareils au bois courants dans {region}).\n\n"
        "Réponds en 280-320 mots, en français, texte continu structuré par thème, "
        "ton factuel et précis avec des chiffres réels quand disponibles. "
        "Toute généralité applicable à n'importe quelle région du Québec est inutile — sois spécifique à {region}.\n\n"
        "PRIX DU MARCHÉ DANS {region} — SECTION OBLIGATOIRE :\n"
        "Recherche les prix réels pratiqués par les entreprises de nettoyage de conduits dans {region} en 2024-2025. "
        "Fourchettes TOTALES par projet (main-d'œuvre + équipement inclus) :\n"
        "- service1_min / service1_max : nettoyage conduits de ventilation (maison unifamiliale standard, système complet)\n"
        "- service2_min / service2_max : ramonage conduit de cheminée (poêle à bois ou foyer, nettoyage complet + inspection)\n"
        "- service3_min / service3_max : nettoyage conduit de sécheuse (dégagement du lint et du conduit d'évacuation)\n"
        "- service4_min / service4_max : inspection vidéo des conduits (caméra + rapport d'état détaillé)\n"
        "Fourchettes typiques QC 2024 pour calibrer (ADAPTE selon compétition et coût de vie de {region}) :\n"
        "  conduits ventilation : 250–600 $ | cheminée : 150–400 $ | sécheuse : 350–800 $ | inspection vidéo : 200–500 $\n\n"
        "TERMINE TON TEXTE PAR CE BLOC EXACT — RÈGLES ABSOLUES :\n"
        "- La ligne `---PRIX---` doit être seule sur sa ligne, après un saut de ligne\n"
        "- Le JSON doit être sur la ligne immédiatement suivante, rien d'autre\n"
        "- Remplace les XXXXX par des entiers sans guillemets ni virgules dans les nombres\n"
        "- Ce bloc doit être la DERNIÈRE chose dans ta réponse\n\n"
        "---PRIX---\n"
        '{{"service1_min": XXXXX, "service1_max": XXXXX, "service2_min": XXXXX, "service2_max": XXXXX, "service3_min": XXXXX, "service3_max": XXXXX, "service4_min": XXXXX, "service4_max": XXXXX}}'
    ),
    "calfeutrage": (
        "Tu es un expert en calfeutrage résidentiel, étanchéité et isolation des bâtiments au Québec. "
        "Ta mission : produire un contexte régional PRÉCIS, FACTUEL et RICHE sur le calfeutrage "
        "dans la région administrative {region} au Québec. "
        "Recherche activement des données locales réelles (entrepreneurs en calfeutrage certifiés dans {region}, types de travaux courants, conditions climatiques spécifiques, réglementations).\n\n"
        "Couvre ces 5 points avec des données chiffrées concrètes et propres à {region} :\n"
        "(1) PARC IMMOBILIER DE {region} ET BESOINS EN CALFEUTRAGE : âge moyen des maisons, proportion construites avant 1990 (calfeutrage d'origine détérioré — silicone vieilli, corde d'étanchéité décomposée, joints de briques fissurés), types d'habitations dominants (bungalows avec fenêtres de plain-pied accessibles, maisons à étages nécessitant équipement en hauteur, condos avec accès restreint), proportion de maisons avec cadres de fenêtres en PVC vs bois vs aluminium (chacun se comporte différemment face au gel-dégel), importance du calfeutrage lors des transactions immobilières dans {region}.\n"
        "(2) IMPACT CLIMATIQUE PARTICULIÈREMENT SÉVÈRE DE {region} SUR LE CALFEUTRAGE : nombre de cycles gel-dégel annuels dans {region} (chaque cycle est une contrainte mécanique sur les joints de calfeutrage — expansion/contraction du matériau d'étanchéité), températures minimales hivernales (impact sur la flexibilité des calfeutrages à base de silicone — certains produits de qualité inférieure se fissurent sous -30°C), accumulation de neige contre les cadres de fenêtres et les fondations, pluies et fonte printanière (infiltrations d'eau sur les calfeutrages de fondation et de salle de bain), humidité relative élevée dans les sous-sols de {region}.\n"
        "(3) TYPES DE CALFEUTRAGE LES PLUS DEMANDÉS DANS {region} : proportion des projets par type — fenêtres et portes extérieures (le plus courant), salle de bain et cuisine (joints de baignoire, receveur de douche — durée de vie 3-7 ans), fondation et sous-sol (calfeutrage des joints entre la fondation et le muret, autour des fenêtres de sous-sol), briques et maçonnerie (jointoiement entre les briques et les cadres, mortier de remplacement), garage et calfeutrage de toiture (solin autour des cheminées, joints de toit plat). Proportion de travaux urgents (infiltration d'eau active) vs préventifs dans {region}.\n"
        "(4) PRODUITS ET NORMES DANS {region} : types de calfeutrant adaptés au climat de {region} — silicone pur (durée de vie 20-25 ans, idéal pour fenêtres, ne peint pas), silicone hybride/polyuréthane (plus facile à peindre, bonne flexibilité par grand froid), mastic acrylique (intérieur uniquement, durée de vie limitée), corde de calfeutrage comprimée (jointoiement de maçonnerie), mousse polyuréthane fermée (isolation des passages de tuyaux, tours de fenêtres). Importants critères de qualité pour les hivers de {region} (flexibilité maintenue à -40°C, résistance UV, adhérence sur matériaux peints ou galvanisés).\n"
        "(5) MARCHÉ DES CALFEUTREURS DANS {region} : nombre estimé d'entrepreneurs actifs, délais typiques en haute saison (printemps-automne — délais 2 à 4 semaines pour un projet résidentiel), saisonnalité des travaux (calfeutrage possible même en hiver si surfaces sèches et au-dessus de -5°C, mais qualité inférieure — meilleure adhérence entre 5°C et 25°C), distinction entre calfeutreurs spécialisés vs peintres ou rénovateurs qui offrent le service, importance des garanties (5-10 ans pour un calfeutrage extérieur de qualité).\n\n"
        "Réponds en 280-320 mots, en français, texte continu structuré par thème, "
        "ton factuel et précis avec des chiffres réels quand disponibles. "
        "Toute généralité applicable à n'importe quelle région du Québec est inutile — sois spécifique à {region}.\n\n"
        "PRIX DU MARCHÉ DANS {region} — SECTION OBLIGATOIRE :\n"
        "Recherche les prix réels pratiqués par les calfeutreurs dans {region} en 2024-2025. "
        "Fourchettes TOTALES par projet (main-d'œuvre + matériaux inclus) :\n"
        "- service1_min / service1_max : calfeutrage complet maison (toutes fenêtres + portes extérieures, résidence standard)\n"
        "- service2_min / service2_max : calfeutrage fenêtres et portes seulement (exterior, 8-12 ouvertures)\n"
        "- service3_min / service3_max : calfeutrage salle de bain (baignoire + douche + joints plancher, complet)\n"
        "- service4_min / service4_max : calfeutrage commercial ou immeuble multi-logements\n"
        "Fourchettes typiques QC 2024 pour calibrer (ADAPTE selon compétition et coût de vie de {region}) :\n"
        "  maison complète : 800–3 500 $ | fenêtres/portes : 350–1 500 $ | salle de bain : 250–900 $ | commercial : 400–1 800 $\n\n"
        "TERMINE TON TEXTE PAR CE BLOC EXACT — RÈGLES ABSOLUES :\n"
        "- La ligne `---PRIX---` doit être seule sur sa ligne, après un saut de ligne\n"
        "- Le JSON doit être sur la ligne immédiatement suivante, rien d'autre\n"
        "- Remplace les XXXXX par des entiers sans guillemets ni virgules dans les nombres\n"
        "- Ce bloc doit être la DERNIÈRE chose dans ta réponse\n\n"
        "---PRIX---\n"
        '{{"service1_min": XXXXX, "service1_max": XXXXX, "service2_min": XXXXX, "service2_max": XXXXX, "service3_min": XXXXX, "service3_max": XXXXX, "service4_min": XXXXX, "service4_max": XXXXX}}'
    ),
    "prix-gouttieres": (
        "Tu es un expert en installation, entretien et réparation de gouttières résidentielles au Québec. "
        "Ta mission : produire un contexte régional PRÉCIS, FACTUEL et RICHE sur les gouttières dans la région administrative {region} au Québec. "
        "Recherche activement des données locales réelles (entrepreneurs gouttières certifiés dans {region}, matériaux dominants, conditions climatiques spécifiques).\n\n"
        "Couvre ces 5 points avec des données chiffrées concrètes et propres à {region} :\n"
        "(1) PARC IMMOBILIER ET BESOINS EN GOUTTIÈRES À {region} : proportion de maisons unifamiliales vs condos, âge moyen du parc immobilier (gouttières remplacées tous les 20-30 ans), types de toitures dominantes dans {region} (pentes, matériaux), longueur moyenne de gouttières par maison, proportion de maisons avec protège-gouttières.\n"
        "(2) CLIMAT ET IMPACT SUR LES GOUTTIÈRES À {region} : accumulation de neige et glace (risque de bouchons et décrochements), nombre de cycles gel-dégel par saison, précipitations annuelles, problèmes spécifiques à {region} (feuillage dense, érables — pollen et feuilles bouchant les gouttières en automne, fonte printanière intense).\n"
        "(3) TYPES DE TRAVAUX LES PLUS FRÉQUENTS À {region} : remplacement de gouttières aluminium vs acier vs vinyle, installation de protège-gouttières (demande croissante), nettoyage saisonnier (printemps/automne), réparations (joints, fixations, pentes), fascias et soffites (souvent remplacés en même temps). Quelle proportion des demandes dans {region} est urgente (dégâts d'eau en cours) vs planifiée.\n"
        "(4) FOURNISSEURS ET NORMES DANS {region} : présence d'entrepreneurs spécialisés gouttières vs couvreurs polyvalents, certification RBQ requise pour les travaux de toiture incluant les gouttières, garanties typiques (5-10 ans sur aluminium), normes de pente minimum (1/16'' par pied), délais d'installation (1 journée pour maison standard).\n"
        "(5) MARCHÉ DES ENTREPRENEURS GOUTTIÈRES DANS {region} : nombre estimé d'entreprises actives, délais typiques en haute saison (printemps/automne), facteurs qui font varier les prix dans {region} (longueur totale, étages, accessibilité, arbres à proximité, dommages sous-jacents aux fascias), tendances (aluminium de calibre 0.027 standard, gouttières continues de chantier populaires).\n\n"
        "Réponds en 270-310 mots, en français, texte continu structuré par thème, "
        "ton factuel et précis avec des chiffres réels quand disponibles. "
        "Toute généralité applicable à n'importe quelle région du Québec est inutile — sois spécifique à {region}.\n\n"
        "PRIX DU MARCHÉ DANS {region} — SECTION OBLIGATOIRE :\n"
        "Recherche les prix réels pratiqués par les entrepreneurs gouttières dans {region} en 2024-2025. "
        "Fourchettes TOTALES par projet :\n"
        "- service1_min / service1_max : installation gouttières aluminium (maison unifamiliale complète)\n"
        "- service2_min / service2_max : installation protège-gouttières (leaf guard, maison complète)\n"
        "- service3_min / service3_max : nettoyage gouttières (1 passage complet)\n"
        "- service4_min / service4_max : réparation gouttières (joints, sections, pentes)\n"
        "Fourchettes typiques QC 2024 pour calibrer (ADAPTE selon compétition et coût de vie de {region}) :\n"
        "  installation aluminium : 900–3 500 $ | protège-gouttières : 700–2 600 $ | nettoyage : 120–420 $ | réparation : 180–850 $\n\n"
        "TERMINE TON TEXTE PAR CE BLOC EXACT — RÈGLES ABSOLUES :\n"
        "- La ligne `---PRIX---` doit être seule sur sa ligne, après un saut de ligne\n"
        "- Le JSON doit être sur la ligne immédiatement suivante, rien d'autre\n"
        "- Remplace les XXXXX par des entiers sans guillemets ni virgules dans les nombres\n"
        "- Ce bloc doit être la DERNIÈRE chose dans ta réponse\n\n"
        "---PRIX---\n"
        '{{"service1_min": XXXXX, "service1_max": XXXXX, "service2_min": XXXXX, "service2_max": XXXXX, "service3_min": XXXXX, "service3_max": XXXXX, "service4_min": XXXXX, "service4_max": XXXXX}}'
    ),
}


def get_regions(csv_path: Path) -> list:
    regions = set()
    encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            with open(csv_path, encoding=enc) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    region = row.get("regadm", "").strip()
                    if region:
                        regions.add(region)
            break
        except (UnicodeDecodeError, KeyError):
            continue
    return sorted(regions)


def load_prompt_from_research(niche: str) -> str | None:
    research_path = Path(__file__).parent.parent / "engine_qc" / f"niche_research_{niche}.json"
    if research_path.exists():
        try:
            data = json.loads(research_path.read_text(encoding="utf-8"))
            prompt = data.get("regional_context_prompt", "")
            if prompt:
                return prompt
        except Exception:
            pass
    return None


def fetch_region_context(region: str, niche: str, api_key: str) -> str:
    research_prompt = load_prompt_from_research(niche)
    if research_prompt:
        prompt = research_prompt.replace("{region}", region)
    else:
        prompt_tpl = NICHE_PROMPTS.get(niche, NICHE_PROMPTS["couvreur"])
        prompt = prompt_tpl.format(region=region)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "sonar-pro",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2000,
        "temperature": 0.2,
    }
    resp = requests.post(PERPLEXITY_API_URL, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def main():
    parser = argparse.ArgumentParser(description="Fetch regional context via Perplexity")
    parser.add_argument("--niche", required=True, help="Niche slug (couvreur, bardeau, etc.)")
    parser.add_argument("--csv", default=None, help="Path to MUN.csv")
    parser.add_argument("--key", default=None, help="Perplexity API key (or set PERPLEXITY_API_KEY)")
    parser.add_argument("--region", default=None, help="Re-fetch only this region (updates existing JSON, keeps others)")
    args = parser.parse_args()

    api_key = args.key or os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        print("ERROR: Set PERPLEXITY_API_KEY env var or pass --key")
        return

    base = Path(__file__).parent.parent
    csv_path = Path(args.csv) if args.csv else base / "MUN.csv"
    if args.niche in ("prix-toiture", "prix-fenetres", "prix-revetement", "prix-drain", "prix-fissure", "prix-gouttieres"):
        niche_dir = base.parent / "Sites_relateds"
    else:
        niche_dir = base / "engine_qc"
    output_path = niche_dir / f"regional_context_{args.niche}.json"

    regions = get_regions(csv_path)
    print(f"Régions trouvées : {len(regions)}")

    # Load existing only when targeting a specific region; otherwise start fresh
    if args.region and output_path.exists():
        output = json.loads(output_path.read_text(encoding="utf-8"))
    else:
        output = {}

    for i, region in enumerate(regions, 1):
        if args.region and region != args.region:
            continue
        print(f"[{i}/{len(regions)}] {region}...", end=" ", flush=True)
        try:
            context = fetch_region_context(region, args.niche, api_key)
            output[region] = context
            print(f"OK ({len(context)} chars)")
        except Exception as e:
            print(f"ERR {e}")
            output[region] = output.get(region, "")
        time.sleep(1.5)

    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSauvegardé : {output_path}")


if __name__ == "__main__":
    main()
