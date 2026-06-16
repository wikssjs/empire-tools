#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
"""
generate_city_content.py — Generate unique per-city intro paragraphs via Claude Haiku
Usage: python tools/generate_city_content.py --niche couvreur

Requires: ANTHROPIC_API_KEY env var
Reads:    engine_qc/regional_context_<niche>.json + MUN.csv
Saves:    engine_qc/city_content_<niche>.json  {slug: "paragraph"}

Run fetch_regional_context.py first.
Use --resume to continue an interrupted run.
"""
import argparse
import csv
import json
import os
import re
import time
import threading
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import anthropic
import urllib.request as _urllib_request

SYSTEM_PROMPTS = {
    "couvreur": (
        "Tu es un rédacteur web spécialisé en toiture résidentielle au Québec. "
        "Tu écris des textes courts, naturels et informatifs pour des pages locales de couverture."
    ),
    "bardeau": (
        "Tu es un rédacteur web spécialisé en bardeau d'asphalte et réfection de toiture au Québec. "
        "Tu écris des textes courts, naturels et convaincants pour des pages locales."
    ),
    "toiture-residentielle": (
        "Tu es un rédacteur web spécialisé en toiture résidentielle au Québec. "
        "Tu écris des textes courts, naturels et informatifs pour des entrepreneurs couvreurs locaux."
    ),
    "climatisation": (
        "Tu es un rédacteur web spécialisé en climatisation et thermopompes au Québec. "
        "Tu écris des textes courts, naturels et informatifs pour des pages locales de HVAC."
    ),
    "fournaise": (
        "Tu es un rédacteur web spécialisé en chauffage et fournaises au Québec. "
        "Tu écris des textes courts, naturels et informatifs pour des pages locales de chauffage."
    ),
    "chauffage": (
        "Tu es un rédacteur web expert en systèmes de chauffage résidentiel au Québec — thermopompes, fournaises au gaz/propane, "
        "chauffage radiant et remplacement de systèmes vétustes. Tu maîtrises les programmes de subventions (Rénoclimat, "
        "LogisVert, RCEE), les certifications RBQ et les enjeux climatiques québécois. Tu génères du contenu HTML structuré, "
        "riche en données locales, qui aide vraiment le propriétaire à prendre une décision éclairée sur son système de chauffage."
    ),
    "thermopompe-aerothermique": (
        "Tu es un rédacteur web expert en thermopompes aérothermiques et en efficacité énergétique au Québec. "
        "Tu maîtrises les programmes de subventions (Rénoclimat, LogisVert, Hydro-Québec) et tu écris pour des propriétaires qui veulent faire le bon choix, pas juste le moins cher."
    ),
    "reparation-thermopompe": (
        "Tu es un rédacteur web spécialisé en réparation et entretien de thermopompes au Québec. "
        "Tu écris pour des propriétaires en situation d'urgence ou qui veulent prévenir une panne — ton ton est rassurant, précis, orienté vers l'action immédiate."
    ),
    "climatisation-thermopompe": (
        "Tu es un rédacteur web expert en climatisation et thermopompes au Québec. "
        "Tu écris pour des propriétaires qui veulent à la fois se rafraîchir l'été et chauffer efficacement l'hiver — tu mets en valeur la double saisonnalité et les économies d'énergie."
    ),
    "installation-thermopompe": (
        "Tu es un rédacteur web spécialisé en installation de thermopompes résidentielles au Québec. "
        "Tu écris pour des propriétaires prêts à passer à l'acte — ton texte guide vers une décision éclairée et une installation réussie par un professionnel certifié RBQ."
    ),
    "pavage-asphalte": (
        "Tu es un rédacteur web expert en pavage asphalte résidentiel au Québec. "
        "Tu maîtrises les enjeux de base granulaire, de gel-dégel, de scellage et de réfection. "
        "Tu écris pour des propriétaires qui veulent comprendre ce qu'ils achètent et éviter les entrepreneurs qui coupent les coins ronds."
    ),
    "prix-pave-uni": (
        "Tu es un rédacteur web expert en pavé uni et aménagement extérieur au Québec. "
        "Tu maîtrises les différences entre les types de pavés, la fondation adéquate pour le climat québécois et les pièges à éviter en soumission. "
        "Tu écris pour des propriétaires qui veulent un aménagement durable et esthétique."
    ),
    "pavage-commercial": (
        "Tu es un rédacteur web expert en pavage commercial et institutionnel au Québec. "
        "Tu maîtrises les normes d'épaisseur, les contraintes logistiques des chantiers commerciaux, le drainage et la conformité réglementaire. "
        "Tu écris pour des gestionnaires d'immeubles, propriétaires commerciaux et responsables de municipalités."
    ),
    "prix-toiture": (
        "Tu es un rédacteur web expert en toiture résidentielle au Québec. "
        "Tu maîtrises les matériaux (bardeaux, métal, TPO), les prix du marché, les certifications RBQ et les enjeux climatiques québécois. "
        "Tu génères du HTML structuré avec des tableaux Tailwind CSS propres, des sections riches en données, et un contenu unique par ville qui aide vraiment le propriétaire à prendre une décision éclairée."
    ),
    "prix-thermopompe": (
        "Tu es un rédacteur web expert en thermopompes résidentielles au Québec. "
        "Tu maîtrises les types de systèmes (mini-split, centrale, aérothermique, géothermique), les programmes de subventions (Hydro-Québec, Rénoclimat, LogisVert), les certifications RBQ et les enjeux climatiques québécois. "
        "Tu génères du HTML structuré avec des tableaux Tailwind CSS propres, des sections riches en données chiffrées, et un contenu unique par ville qui aide le propriétaire à choisir et budgéter sa thermopompe de façon éclairée."
    ),
    "prix-drain": (
        "Tu es un rédacteur web expert en drainage résidentiel et imperméabilisation au Québec. "
        "Tu maîtrises les types de drains (drain français, drain de fondation), l'imperméabilisation, les méthodes d'injection, les enjeux du gel-dégel et de la nappe phréatique québécoise. "
        "Tu génères du HTML structuré avec des tableaux Tailwind CSS propres, des sections riches en données chiffrées, et un contenu unique par ville qui aide le propriétaire à comprendre son problème et son coût."
    ),
    "prix-fissure": (
        "Tu es un rédacteur web expert en réparation de fissures dans les fondations au Québec. "
        "Tu maîtrises les types de fissures (capillaires, infiltration, structurales), les méthodes de réparation (injection polyuréthane, époxy, excavation), les enjeux du gel-dégel québécois et les prix du marché. "
        "Tu génères du HTML structuré avec des tableaux Tailwind CSS propres, des sections riches en données chiffrées, et un contenu unique par ville qui aide le propriétaire à identifier la gravité et le coût de sa réparation."
    ),
    "prix-fenetres": (
        "Tu es un rédacteur web expert en remplacement de fenêtres résidentielles au Québec. "
        "Tu maîtrises les types de cadres (PVC, hybride bois-alu, aluminium), le triple vitrage, les certifications ÉnerGuide et ENERGY STAR, les programmes d'aide à la rénovation écoénergétique et les prix du marché québécois. "
        "Tu génères du HTML structuré avec des tableaux Tailwind CSS propres, des sections riches en données chiffrées, et un contenu unique par ville qui aide le propriétaire à bien choisir et budgéter son remplacement de fenêtres."
    ),
    "prix-revetement": (
        "Tu es un rédacteur web expert en revêtement extérieur résidentiel au Québec. "
        "Tu maîtrises tous les types de revêtements (vinyle, Canexel, fibrociment, brique, crépi, aluminium, bois), leur comportement face aux cycles gel-dégel québécois, les prix installés et les critères de durabilité. "
        "Tu génères du HTML structuré avec des tableaux Tailwind CSS propres, des sections riches en données chiffrées, et un contenu unique par ville qui aide le propriétaire à choisir le bon matériau selon son budget et son contexte régional."
    ),
    "prix-gouttieres": (
        "Tu es un rédacteur web expert en installation, nettoyage et réparation de gouttières résidentielles au Québec. "
        "Tu maîtrises les types de gouttières (aluminium calibre 0.027, acier galvanisé, vinyle, cuivre), les protège-gouttières (grille, filtre en mousse, protège-gouttières continues), les fascias et soffites, les normes de pente, les impacts du gel-dégel et des feuilles d'automne dans les différentes régions du Québec. "
        "Tu génères du HTML structuré avec des tableaux Tailwind CSS propres, des sections riches en données chiffrées, et un contenu unique par ville qui aide le propriétaire à comprendre ses besoins et à budgéter ses travaux de gouttières."
    ),
    "excavation": (
        "Tu es un rédacteur web expert en excavation et travaux de sol résidentiels au Québec. "
        "Tu maîtrises les types de travaux (excavation générale, terrassement, remblai, drainage, fossé, fondation, piscine creusée), les enjeux de sol (argile, roc, sable, nappe phréatique), les certifications RBQ, les permis municipaux et les prix du marché québécois. "
        "Tu génères du HTML structuré avec des tableaux Tailwind CSS propres, des sections riches en données chiffrées, et un contenu unique par ville qui aide le propriétaire à comprendre son projet, son coût réel et comment choisir un bon entrepreneur."
    ),
    "cuisine": (
        "Tu es un rédacteur web expert en rénovation de cuisine résidentielle au Québec. "
        "Tu maîtrises tous les niveaux de rénovation (réfection partielle, rénovation complète, cuisine haut de gamme), les matériaux d'armoires (laminé thermoplastique, MDF peint, bois massif, acrylique), les comptoirs (quartz, granite, stratifié, bois), les styles tendance (cuisine ouverte, îlot multifonction, semi-ouverte), les certifications RBQ et les prix du marché québécois. "
        "Tu génères du HTML structuré avec des tableaux Tailwind CSS propres, des sections riches en données chiffrées, et un contenu unique par ville qui aide le propriétaire à planifier, budgéter et réussir sa rénovation cuisine."
    ),
    "ceramique": (
        "Tu es un rédacteur web expert en pose de céramique et carrelage résidentiel au Québec. "
        "Tu maîtrises tous les formats (mosaïque, métro, grand format 24x24, 12x24), les matériaux (céramique, porcelaine rectifiée, pierre naturelle), les types de pose (droit, diagonal, chevron, opus), les applications (plancher, salle de bain, douche, dosseret cuisine, terrasse), la membrane découplée Schluter Ditra, les coulis époxy, les certifications RBQ et les prix du marché québécois. "
        "Tu génères du HTML structuré avec des tableaux Tailwind CSS propres, des sections riches en données chiffrées, et un contenu unique par ville qui aide le propriétaire à planifier, budgéter et réussir sa pose de céramique."
    ),
    "agrandissement": (
        "Tu es un rédacteur web expert en agrandissement de maison au Québec — extensions latérales, ajouts d'étage, garages attenants et rénovations majeures. "
        "Tu maîtrises les règlements de zonage et marges de recul des MRC québécoises, les permis de construction, les enjeux de structure et de fondation pour les extensions, "
        "et les certifications RBQ requises pour les entrepreneurs généraux. "
        "Tu génères du HTML structuré avec des tableaux Tailwind CSS propres, des sections riches en données chiffrées, "
        "et un contenu unique par ville qui aide le propriétaire à planifier, budgéter et réussir son projet d'agrandissement."
    ),
    "peinture": (
        "Tu es un rédacteur web expert en peinture résidentielle et commerciale au Québec. "
        "Tu maîtrises tous les types de travaux (peinture intérieure, extérieure, plafonds, moulures, béton, brique peinte), "
        "les produits (latex, alkyde, peintures sans COV, enduits, sous-couches), la préparation des surfaces (sablage, calfeutrage, imperméabilisation), "
        "les certifications RBQ pour les entrepreneurs en peinture, et les prix du marché québécois selon la région. "
        "Tu génères du HTML structuré avec des tableaux Tailwind CSS propres, des sections riches en données chiffrées, "
        "et un contenu unique par ville qui aide le propriétaire à planifier, budgéter et réussir ses travaux de peinture."
    ),
    "decontamination": (
        "Tu es un rédacteur web expert en décontamination professionnelle et qualité de l'air intérieur (IEQ) au Québec. "
        "Tu maîtrises tous les types de contaminations (moisissures, amiante, radon, bactéries, post-sinistre), "
        "les normes CNESST pour le retrait d'amiante, les certifications IEQ et IEDQ, les obligations légales des propriétaires, "
        "les processus d'inspection et les protocoles de décontamination certifiés. "
        "Tu génères du HTML structuré avec des tableaux Tailwind CSS propres, des sections riches en données chiffrées, "
        "et un contenu unique par ville qui aide vraiment le propriétaire à comprendre son problème, évaluer son coût et choisir un décontamineur certifié."
    ),
    "beton": (
        "Tu es un rédacteur web expert en travaux de béton résidentiel au Québec. "
        "Tu maîtrises tous les types de projets (entrée de garage, dalle intérieure, patio, fondation, béton estampé, béton coloré, béton scellé), les techniques de coulage (armature rebar, fibres synthétiques, agent entraîneur d'air pour le gel), les réparations (injection époxy, muretage, scellement), les exigences du climat québécois (gel-dégel, profondeur hors-gel), les certifications RBQ et les prix du marché québécois. "
        "Tu génères du HTML structuré avec des tableaux Tailwind CSS propres, des sections riches en données chiffrées, et un contenu unique par ville qui aide le propriétaire à planifier, budgéter et réussir ses travaux de béton."
    ),
    "toiture-plate": (
        "Tu es un rédacteur web expert en toiture plate résidentielle au Québec. "
        "Tu maîtrises tous les systèmes de membrane (élastomère bicouche torchée/adhésive, TPO thermoplastique, EPDM caoutchouc, système APP multicouche), "
        "les enjeux du gel-dégel québécois sur les membranes, les normes d'isolation rigide, "
        "les garanties fabricant (Soprema, Firestone, IKO Commercial), les certifications RBQ et les prix du marché québécois. "
        "Tu génères du HTML structuré avec des tableaux Tailwind CSS propres, des sections riches en données chiffrées, "
        "et un contenu unique par ville qui aide le propriétaire à comprendre son système, son coût et comment choisir un couvreur certifié."
    ),
    "salledebain": (
        "Tu es un rédacteur web expert en rénovation de salle de bain résidentielle au Québec. "
        "Tu maîtrises tous les types de projets (douche italienne sans rebord, remplacement de baignoire, réfection complète, salle de bain luxe), "
        "les matériaux (carrelage grand format, mosaïque, LVT, marbre, quartz), les systèmes d'imperméabilisation (Schluter, Kerdi, membrane Ditra), "
        "les normes de plomberie CMMTQ, les certifications RBQ et les prix du marché québécois. "
        "Tu génères du HTML structuré avec des tableaux propres, des sections riches en données chiffrées, "
        "et un contenu unique par ville qui aide le propriétaire à planifier sa rénovation, comprendre son budget et choisir un entrepreneur licencié RBQ."
    ),
    "paysagement": (
        "Tu es un rédacteur web expert en aménagement paysager résidentiel au Québec. "
        "Tu maîtrises tous les types de projets (gazon en plaques, terrassement, plate-bandes, pavé uni, terrasses en bois ou composite, pergolas, piscines hors-terre, murets et bordures), les végétaux adaptés au climat québécois, les certifications ASNQ (Association des professionnels en horticulture du Québec), les contraintes de sol et de gel, et les prix du marché québécois. "
        "Tu génères du HTML structuré avec des tableaux Tailwind CSS propres, des sections riches en données chiffrées, "
        "et un contenu unique par ville qui aide le propriétaire à planifier, budgéter et réussir son projet d'aménagement paysager."
    ),
    "electricien": (
        "Tu es un rédacteur web expert en électricité résidentielle et commerciale au Québec. "
        "Tu maîtrises tous les types de travaux électriques (mise aux normes 200A, panneaux électriques, circuits GFCI/AFCI, bornes de recharge VE, fournaises et thermopompes, urgences), les certifications CMEQ (Corporation des maîtres électriciens du Québec), le Code canadien de l'électricité, les exigences d'Hydro-Québec et les prix du marché québécois. "
        "Tu génères du HTML structuré avec des tableaux Tailwind CSS propres, des sections riches en données chiffrées, "
        "et un contenu unique par ville qui aide vraiment le propriétaire à comprendre ses travaux électriques, évaluer leur coût et choisir un maître électricien licencié RBQ."
    ),
    "portes-fenetres": (
        "Tu es un rédacteur web expert en remplacement de fenêtres et portes résidentielles au Québec. "
        "Tu maîtrises tous les types de produits (PVC double et triple vitrage, hybride bois-PVC, aluminium, porte d'acier, porte en fibre de verre, porte-fenêtre coulissante), les certifications ÉnerGuide et ENERGY STAR, les programmes d'aide (Rénoclimat, RCEE, LogisVert), les normes de performance thermique pour le climat québécois et les prix du marché. "
        "Tu génères du HTML structuré avec des tableaux Tailwind CSS propres, des sections riches en données chiffrées, "
        "et un contenu unique par ville qui aide le propriétaire à choisir les bons produits, maximiser ses subventions et sélectionner un installateur certifié."
    ),
    "fosseseptique": (
        "Tu es un rédacteur web expert en systèmes septiques et assainissement autonome au Québec. "
        "Tu maîtrises les types de systèmes (fosse septique classique, fosse à compostage, champs d'épuration, systèmes à milieu filtrant), le Règlement Q-2 r.22 du MELCCFP, les obligations de conformité lors des ventes immobilières, les enjeux de sol et de nappe phréatique, la fréquence de vidange recommandée et les prix du marché québécois. "
        "Tu génères du HTML structuré avec des tableaux Tailwind CSS propres, des sections riches en données chiffrées, "
        "et un contenu unique par ville qui aide le propriétaire à comprendre son système, respecter la réglementation et budgéter ses travaux de fosse septique."
    ),
    "nettoyage-conduits": (
        "Tu es un rédacteur web expert en nettoyage de conduits de ventilation et systèmes CVAC au Québec. "
        "Tu maîtrises les types de systèmes (conduits de ventilation forcée, conduits de cheminée, conduits de sécheuse, échangeurs d'air VRC/ERV), les normes NADCA (National Air Duct Cleaners Association), les enjeux de qualité de l'air intérieur (moisissures, allergènes, vermiculite, radon), les certifications RBQ et les prix du marché québécois. "
        "Tu génères du HTML structuré avec des tableaux Tailwind CSS propres, des sections riches en données chiffrées, "
        "et un contenu unique par ville qui aide le propriétaire à comprendre l'état de ses conduits, planifier un nettoyage professionnel et améliorer la qualité de l'air de sa maison."
    ),
    "calfeutrage": (
        "Tu es un rédacteur web expert en calfeutrage résidentiel et étanchéité des bâtiments au Québec. "
        "Tu maîtrises tous les types de calfeutrage (silicone pur, hybride silicone-polyuréthane, mastic acrylique, corde de calfeutrage, mousse polyuréthane), les zones critiques (fenêtres, portes, salle de bain, fondation, maçonnerie, toiture), le comportement des matériaux face aux cycles gel-dégel québécois, les certifications RBQ et les prix du marché québécois. "
        "Tu génères du HTML structuré avec des tableaux Tailwind CSS propres, des sections riches en données chiffrées, "
        "et un contenu unique par ville qui aide le propriétaire à identifier les zones à calfeutrer en priorité, choisir le bon produit et planifier ses travaux d'étanchéité."
    ),
    "cloture": (
        "Tu es un rédacteur web expert en installation de clôtures résidentielles au Québec. "
        "Tu maîtrises tous les types de clôtures (bois traité sous-pression, vinyle, aluminium décoratif, chaîne maillée, composite), "
        "les enjeux du gel-dégel québécois sur les fondations de poteaux, les règlements municipaux sur la hauteur et les distances "
        "de reculement, les fournisseurs québécois (bois traité CCA, vinyle Amerimax/Bufftech, aluminium Jerith/Fortress), "
        "les certifications RBQ et les prix du marché québécois. "
        "Tu génères du HTML structuré avec des tableaux propres, des sections riches en données chiffrées, "
        "et un contenu unique par ville qui aide le propriétaire à choisir le bon matériau, comprendre son budget et sélectionner un entrepreneur fiable."
    ),
}

USER_PROMPT_TEMPLATES = {
    "couvreur": """\
Écris un bloc de contenu HTML pour la page "couvreur à {ville}" ({region}, Québec).

Contexte régional : {context}

Génère 3 sections, chacune avec un <h2> et un <p>. Les titres H2 doivent être uniques et naturels — invente-les toi-même, ne répète pas les mêmes formules que pour d'autres villes.

Sujets à couvrir (un par section, dans cet ordre) :
1. Contexte local de la toiture à {ville} — types de toits courants dans {region}, défis climatiques, particularités du secteur. Intègre des faits du contexte régional.
2. Signes qu'il faut agir — usure, durée de vie selon le climat de {region}, risques d'inaction.
3. Comment bien choisir son couvreur — licence RBQ, garanties, comparaison de soumissions.

Chaque paragraphe : 120-150 mots, texte continu, ton humain et professionnel.
Mentionne {ville} naturellement dans les titres ou paragraphes (pas à chaque phrase).
Aucune liste à puces. Aucune promesse irréaliste.

Réponds uniquement avec le HTML (3 blocs h2+p), sans introduction ni commentaire.\
""",
    "bardeau": """\
Écris un bloc de contenu HTML pour la page "remplacement bardeau asphalte à {ville}" ({region}, Québec).

Contexte régional : {context}

Génère 3 sections avec <h2> + <p>. Invente des titres H2 accrocheurs et uniques — angle matériau/prix/valeur, pas de formules génériques.

Sujets à couvrir :
1. Bardeau 30 ans, architectural ou premium : lequel choisir à {ville} — explique les différences de qualité, de durée de vie et de prix selon le contexte climatique de {region}. Intègre des faits du contexte régional sur l'âge du parc immobilier ou la rigueur des hivers.
2. Ce qui fait vraiment varier le prix d'une réfection à {ville} — superficie, pentes, nombre de lucarnes, épaisseur du papier feutre, marque du bardeau. Donne des ordres de grandeur réalistes sans promettre de prix fixe.
3. Les erreurs à éviter en choisissant son couvreur pour le bardeau — soumission trop vague, pas de détail sur les matériaux, absence de garantie main-d'oeuvre. Conseils pratiques pour comparer correctement.

Chaque paragraphe : 120-150 mots, texte continu, ton direct et utile.
Mentionne {ville} naturellement (1-2 fois par section). Aucune liste à puces. Aucune promesse irréaliste.

Réponds uniquement avec le HTML (3 blocs h2+p), sans introduction ni commentaire.\
""",
    "toiture-residentielle": """\
Écris un bloc de contenu HTML pour la page "toiture résidentielle à {ville}" ({region}, Québec).

Contexte régional : {context}

Génère 3 sections avec <h2> + <p>. Invente des titres H2 naturels, différents de ce qu'on trouve sur n'importe quel site de toiture générique.

Sujets à couvrir :
1. Le parc résidentiel de {region} et ses toitures — âge typique des maisons, matériaux dominants (bardeau, métal, membrane), fréquence des réfections. Utilise des faits concrets du contexte régional pour ancrer le texte dans la réalité locale de {ville}.
2. Réparer ou tout refaire ? — comment évaluer l'état d'une toiture résidentielle, quand une réparation suffit et à quel moment la réfection complète devient inévitable. Sois précis sur les signes à observer.
3. Le déroulement d'un projet de toiture à {ville} — de l'inspection à la fin des travaux, ce à quoi s'attendre : délais, permis, nettoyage de chantier, garanties. Rassure le propriétaire sans survendre.

Chaque paragraphe : 120-150 mots, texte continu, ton humain et rassurant.
Mentionne {ville} naturellement. Aucune liste à puces. Aucune promesse irréaliste.

Réponds uniquement avec le HTML (3 blocs h2+p), sans introduction ni commentaire.\
""",
    "climatisation": """\
Écris un bloc de contenu HTML pour la page "installation climatisation à {ville}" ({region}, Québec).

Contexte régional : {context}

Génère 3 sections avec <h2> + <p>. Invente des titres H2 naturels et uniques pour cette ville.

Sujets à couvrir :
1. Besoins en climatisation et thermopompe à {ville} — contexte climatique de {region}, taux d'adoption, types de systèmes courants. Intègre des faits du contexte régional.
2. Subventions et programmes disponibles — Renoclimat, Hydro-Québec, économies à long terme pour les résidents de {region}.
3. Choisir le bon système pour sa maison — murale vs centrale, critères selon le type d'habitation, importance d'une installation certifiée.

Chaque paragraphe : 120-150 mots, texte continu, ton humain.
Mentionne {ville} naturellement. Aucune liste à puces. Aucune promesse irréaliste.

Réponds uniquement avec le HTML, sans introduction.\
""",
    "fournaise": """\
Écris un bloc de contenu HTML pour la page "installation fournaise à {ville}" ({region}, Québec).

Contexte régional : {context}

Génère 3 sections avec <h2> + <p>. Invente des titres H2 naturels et uniques pour cette ville.

Sujets à couvrir :
1. Chauffage à {ville} — types de fournaises courants dans {region}, durée de vie typique, contexte énergétique local. Intègre des faits du contexte régional.
2. Signes qu'il faut remplacer sa fournaise — indicateurs de fin de vie, coût de l'inaction, économies d'énergie potentielles.
3. Prix d'une nouvelle fournaise à {ville} — facteurs qui influencent le coût, types disponibles (gaz, électrique, propane), avantages de comparer plusieurs soumissions.

Chaque paragraphe : 120-150 mots, texte continu, ton humain.
Mentionne {ville} naturellement. Aucune liste à puces. Aucune promesse irréaliste.

Réponds uniquement avec le HTML, sans introduction.\
""",

    "peinture": """\
Génère un bloc de contenu HTML COMPLET et RICHE pour la page "peinture résidentielle à {ville}" ({region}, Québec).
Population : {population} habitants.

Contexte régional réel : {context}

Prix locaux fournis (utilise ces données dans le contenu) :
- Peinture intérieure complète (maison unifamiliale, toutes pièces) : {service1_min}$ – {service1_max}$
- Peinture extérieure complète (revêtement, soffites, fascias) : {service2_min}$ – {service2_max}$
- Peinture d'une pièce (salon, cuisine ou chambre — murs + plafond) : {service3_min}$ – {service3_max}$
- Peinture plafonds + moulures (maison complète) : {service4_min}$ – {service4_max}$

STRUCTURE OBLIGATOIRE — génère ces 6 sections dans l'ordre exact :

---
SECTION 1 — Tableau comparatif des types de travaux de peinture à {ville}
<h2 class="text-3xl font-bold mb-4">[Titre accrocheur sur la peinture résidentielle à {ville} — ex: "Peinture intérieure ou extérieure à {ville} : prix, étapes et conseils pour bien choisir"]</h2>
Suivi d'un <p> de 180-220 mots sur le marché de la peinture résidentielle dans {region} : âge du parc immobilier (les maisons de {region} construites avant 1990 nécessitent souvent une repeinture complète), fréquence recommandée de repeinture intérieure (7-10 ans) et extérieure (5-8 ans selon le climat), pourquoi les propriétaires de {region} investissent dans la peinture (vente de maison, rafraîchissement, protection contre l'humidité), tendances actuelles (couleurs neutres, peintures sans COV, finis mats satinés). Intègre les données chiffrées du contexte régional.
Suivi d'un tableau HTML COMPLET : Type de travail | Prix à {ville} | Superficie typique | Durée des travaux | Inclus dans le prix | Fréquence recommandée
Lignes : Peinture intérieure complète / Peinture d'une pièce / Peinture plafonds et moulures / Peinture extérieure complète / Peinture de portes et fenêtres / Peinture sous-sol ou garage
Classes tableau : <table class="w-full text-sm border-collapse mt-6 mb-2"> <thead style="background:#4f46e5;color:#fff"> <th class="px-4 py-3 text-left font-semibold"> <tbody> <tr class="border-b border-gray-200 hover:bg-gray-50"> <td class="px-4 py-3">

---
SECTION 2 — Facteurs qui font varier le prix de la peinture à {ville}
<h2> accrocheur ancré dans {ville} ou {region}
<p> de 180-220 mots : superficie totale à peindre et nombre de pièces (impact direct sur la quantité de peinture et le temps de main-d'oeuvre), état actuel des surfaces (murs en bon état vs fissures, trous, ancienne peinture écaillée, taches d'humidité nécessitant une préparation plus longue), nombre de couches requises (1 couche de finition sur une sous-couche vs 2-3 couches sur une ancienne couleur foncée), hauteur des plafonds (8 pi standard vs 9-12 pi nécessitant des échafaudages), accès extérieur (plain-pied simple vs maison 2 étages avec échafaudage complet), qualité de la peinture choisie (peinture d'entrée de gamme vs premium sans COV), main-d'oeuvre locale dans {region} selon la saison. Pour les chiffres clés, utilise <strong class="text-indigo-600">X $</strong>.
Suivi d'un tableau (thead style="background:#4f46e5;color:#fff") : Facteur | Impact sur le prix | Détail pour {ville}
Lignes : Superficie à peindre / État des surfaces / Nombre de couches / Hauteur des plafonds / Accès extérieur / Qualité de peinture / Saison et disponibilité

---
SECTION 3 — Peinture intérieure vs extérieure : ce qu'il faut savoir à {ville}
<h2> original mentionnant {ville} ou {region}
<p> de 200-250 mots : peinture intérieure — meilleure période (printemps-automne pour une bonne ventilation), importance de la préparation (reboucher fissures, poncer, sous-couche), produits adaptés au Québec (peinture latex lavable, sans COV pour les chambres d'enfants, peinture hydrofuge pour salles de bain), durée de vie d'une peinture intérieure de qualité (7-12 ans selon la circulation). Peinture extérieure dans {region} — contraintes climatiques (température minimale 10°C pour l'application, éviter les journées de forte chaleur ou de pluie), types de revêtements courants dans {region} (vinyle, aluminium, bois, brique peinte, fibrociment), produits adaptés au gel québécois (élastomères, peintures résistantes aux UV et à l'humidité), fréquence recommandée de repeinture extérieure (5-8 ans selon exposition). Mets les chiffres en <strong class="text-indigo-600">X $</strong>.
Suivi d'un tableau (thead style="background:#4f46e5;color:#fff") : Aspect | Peinture intérieure à {ville} | Peinture extérieure à {ville}
Lignes : Meilleure saison / Durée de vie / Préparation requise / Produits recommandés / Durée des travaux / Prix moyen

---
SECTION 4 — Les étapes d'un projet de peinture réussi à {ville}
<h2> pratique et motivant, ancré dans {ville}
<p> de 200-250 mots : les étapes dans l'ordre — (1) évaluation de l'état des surfaces et identification des réparations nécessaires (fissures, moisissures, ancienne peinture au plomb dans les maisons construites avant 1978), (2) choix des couleurs et des produits (consultation d'un coloriste, échantillons sur le mur), (3) demande de 3 soumissions détaillées auprès de peintres certifiés RBQ dans {region}, (4) préparation des surfaces (nettoyage, dégraissage, sablage, rebouchage, application de sous-couche), (5) application des couches de finition (technique rouleau, pinceau, pistolet selon la surface), (6) nettoyage et inspection finale. Délais typiques dans {region} pour un projet intérieur complet (2-5 jours pour une maison unifamiliale) et extérieur (3-7 jours selon la superficie). Mets les montants en <strong class="text-indigo-600">X $</strong>.
Suivi d'un tableau (thead style="background:#4f46e5;color:#fff") : Étape | Durée typique | Ce qui est inclus | Astuce pour {ville}
Lignes : Évaluation et devis / Choix des couleurs / Préparation des surfaces / Sous-couche / Application finition (1re couche) / Application finition (2e couche) / Inspection et retouches

---
SECTION 5 — Choisir son peintre à {ville} : ce qu'il faut vérifier
<h2> pratique et local
<p> de 200-250 mots : peintre certifié RBQ (sous-catégorie 2.3.1 peinture et décoration) — vérification du numéro de licence sur le site de la RBQ, assurance responsabilité civile minimale 2 M$ obligatoire, garantie main-d'oeuvre (minimum 1 an), contrat écrit avec description détaillée (surfaces à peindre, produits utilisés avec marque et fini, nombre de couches, calendrier). Points d'attention : méfiance envers les prix anormalement bas (peinture de mauvaise qualité, 1 seule couche, sous-traitants non assurés), refus du paiement comptant intégral à l'avance (un acompte de 10-20% est normal), vérifier que le peintre nettoie et protège les meubles, planchers et cadres de porte. Dans {region}, les peintres réputés sont souvent bookés 4-8 semaines à l'avance en haute saison (mai à septembre). Questions essentielles : combien de couches sont incluses ? Les produits sont-ils de marque reconnue (Dulux, Benjamin Moore, Sherwin-Williams) ? La préparation des surfaces est-elle incluse ?
Suivi d'un tableau (thead style="background:#4f46e5;color:#fff") : Critère | Ce qu'il faut vérifier | Pourquoi c'est important
Lignes : Licence RBQ valide / Assurance responsabilité / Contrat écrit détaillé / Marque de peinture utilisée / Nombre de couches incluses / Garantie main-d'oeuvre / Protection des surfaces

---
SECTION 6 — FAQ : Peinture résidentielle à {ville}
<h2 class="text-3xl font-bold mb-8">Questions fréquentes sur la peinture résidentielle à {ville}</h2>
Génère 6 questions-réponses en accordéon HTML avec ces classes exactes :
<details class="group bg-white rounded-xl border border-gray-200 overflow-hidden mb-3">
<summary class="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50">
<span class="font-semibold text-gray-900 pr-4">QUESTION ICI</span>
<svg class="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
</summary>
<div class="px-6 pb-6 text-gray-600 leading-relaxed">RÉPONSE ICI (100-130 mots, précise, avec données locales)</div>
</details>

Questions à couvrir :
1. Combien coûte la peinture d'une maison à {ville} (intérieur et extérieur — utilise les prix fournis)
2. Combien de temps faut-il pour peindre une maison à {ville}
3. Quelle est la meilleure saison pour peindre l'extérieur d'une maison à {ville}
4. Combien de couches de peinture faut-il appliquer à {ville}
5. Faut-il une licence RBQ pour les travaux de peinture à {ville}
6. Comment choisir les couleurs pour l'intérieur de sa maison à {ville}

---

RÈGLES ABSOLUES :
- Réponds UNIQUEMENT avec le HTML brut, aucun commentaire avant ou après
- NE génère PAS de wrapper extérieur <div> ou <section> global — commence directement par le contenu des sections
- Pour le texte courant utilise text-gray-900 (titres/spans), text-gray-600 (corps FAQ) — pour les prix utilise <strong class="text-indigo-600">X $</strong>
- Intègre les prix fournis directement dans les tableaux et le texte
- Mentionne {ville} et {region} naturellement dans chaque section
- Aucune liste à puces <ul><li> — uniquement <p>, tableaux et accordéons
- Chaque section doit apporter une valeur distincte, pas de répétition\
""",

    "decontamination": """\
Génère un bloc de contenu HTML COMPLET et RICHE pour la page "décontamination professionnelle à {ville}" ({region}, Québec).
Population : {population} habitants.

Contexte régional réel : {context}

Prix locaux fournis (utilise ces données dans le contenu) :
- Décontamination complète (moisissures, amiante ou bactéries, résidentiel) : {service1_min}$ – {service1_max}$
- Inspection certifiée IEQ (rapport officiel inclus) : {service2_min}$ – {service2_max}$
- Prélèvements laboratoire (analyse mycologique ou amiante) : {service3_min}$ – {service3_max}$
- Décontamination post-sinistre / dégât d'eau : {service4_min}$ – {service4_max}$

STRUCTURE OBLIGATOIRE — génère ces 6 sections dans l'ordre exact :

---
SECTION 1 — Tableau comparatif des types de décontamination à {ville}
<h2 class="text-3xl font-bold mb-4">[Titre accrocheur sur la décontamination à {ville} — ex: "Moisissures, amiante ou radon à {ville} : quel type de décontamination vous faut-il ?"]</h2>
Suivi d'un <p> de 180-220 mots sur les risques de contamination dans {region} : proportion de maisons construites avant 1980 (risque amiante élevé), humidité climatique de {region} et son impact sur la croissance de moisissures, types de contaminations les plus fréquents dans les propriétés de {region} selon le contexte régional (moisissures en sous-sol, amiante dans l'isolation ou les carreaux de plancher, radon selon la géologie locale), pourquoi l'inspection IEQ est devenue un réflexe pour les transactions immobilières dans {region}. Intègre les données chiffrées du contexte régional.
Suivi d'un tableau HTML COMPLET : Type de contamination | Prix à {ville} | Durée d'intervention | Certification requise | Résultats livrés | Urgence disponible
Lignes : Décontamination moisissures / Retrait d'amiante / Mitigation radon / Décontamination bactérienne / Inspection IEQ certifiée / Post-sinistre / dégât d'eau
Classes tableau : <table class="w-full text-sm border-collapse mt-6 mb-2"> <thead style="background:#0284c7;color:#fff"> <th class="px-4 py-3 text-left font-semibold"> <tbody> <tr class="border-b border-gray-200 hover:bg-gray-50"> <td class="px-4 py-3">

---
SECTION 2 — Facteurs qui font varier le prix de la décontamination à {ville}
<h2> accrocheur ancré dans {ville} ou {region}
<p> de 180-220 mots : superficie contaminée et impact direct sur le coût (prix au pi² selon l'étendue des moisissures ou la quantité de matériaux amiantés), type de contaminant (moisissures superficielles vs profondes dans les structures, amiante friable vs non friable — différences majeures de coût et de protocole), accessibilité de la zone contaminée (vide sanitaire vs sous-sol fini vs comble), niveau de contamination et nombre de matériaux à retirer, urgence de l'intervention (48h vs planifiée dans {region}), coûts de laboratoire (analyse mycologique, certificat d'amiante), rapport IEQ post-décontamination obligatoire. Pour les chiffres clés, utilise <strong class="text-sky-600">X $</strong>.
Suivi d'un tableau (thead style="background:#0284c7;color:#fff") : Facteur | Impact sur le prix | Détail pour {ville}
Lignes : Superficie contaminée (pi²) / Type de contaminant / Accessibilité de la zone / Niveau de contamination / Urgence (48h) / Analyses laboratoire / Rapport IEQ post-travaux

---
SECTION 3 — Moisissures, amiante et radon à {ville} : ce qu'il faut savoir
<h2> original mentionnant {ville} ou {region}
<p> de 200-250 mots : MOISISSURES dans {region} — signes visibles (taches noires, verdâtres, odeur de moisi persistante), causes fréquentes dans les maisons de {region} (humidité climatique, mauvaise ventilation, infiltrations d'eau printanières), risques pour la santé (allergies, asthme, mycotoxines), délai d'apparition après un dégât d'eau (24-48h). AMIANTE dans {region} — présence probable dans les maisons construites avant 1980 (isolation, carreaux de plancher, tuyaux en fibrociment, joints, vinyle), obligation légale de retrait avant travaux (CNESST), équipe en scaphandre et confinement obligatoire, manifeste de transport des déchets dangereux, coût du test d'amiante ({service3_min}$–{service3_max}$). RADON dans {region} — selon le contexte régional, niveau de risque géologique, recommandation Santé Canada (<200 Bq/m³), test de radon ({service3_min}$–{service3_max}$), mitigation si dépassement. Mets les montants en <strong class="text-sky-600">X $</strong>.
Suivi d'un tableau (thead style="background:#0284c7;color:#fff") : Contaminant | Signes à {ville} | Risque santé | Prix diagnostic | Prix décontamination | Urgence recommandée
Lignes : Moisissures noires / Moisissures diffuses / Amiante friable / Amiante non friable / Radon élevé / Contamination bactérienne

---
SECTION 4 — Les étapes d'une décontamination professionnelle à {ville}
<h2> pratique et rassurant, ancré dans {ville}
<p> de 200-250 mots : les étapes dans l'ordre — (1) inspection visuelle et prélèvements par un inspecteur certifié IEQ ({service2_min}$–{service2_max}$), (2) analyse laboratoire mycologique ou amiante ({service3_min}$–{service3_max}$), (3) rapport d'inspection IEQ officiel avec recommandations, (4) soumissions auprès de 3 décontamineurs certifiés RBQ dans {region}, (5) mise en place du confinement (zone de travail isolée, ventilation négative, protection des zones saines), (6) retrait des matériaux contaminés et traitement antifongique ou désamiantage selon le type, (7) nettoyage HEPA et traitement des surfaces, (8) inspection post-décontamination et rapport final certifié IEQ, (9) reconstruction des surfaces retirées si nécessaire. Délais typiques dans {region} pour une intervention standard (2-5 jours selon l'étendue). Pour les montants, utilise <strong class="text-sky-600">X $</strong>.
Suivi d'un tableau (thead style="background:#0284c7;color:#fff") : Étape | Durée typique | Coût estimé | Certifié requis
Lignes : Inspection IEQ et prélèvements / Analyse laboratoire / Rapport d'inspection / Confinement et protection / Retrait et traitement / Nettoyage HEPA / Inspection post-décontamination / Reconstruction

---
SECTION 5 — Choisir son décontamineur certifié à {ville}
<h2> pratique et local
<p> de 200-250 mots : décontamineur certifié IEQ (Indoor Environmental Quality) et IEDQ — vérification du certificat sur le site de l'IEDQ, licence RBQ obligatoire, assurance responsabilité civile minimale 2 M$, formation spécifique CNESST pour le retrait d'amiante. Ce que doit inclure une bonne soumission : description détaillée des matériaux contaminés identifiés, méthode de confinement prévue, traitement antifongique utilisé (marque, concentration), rapport post-décontamination inclus ou non, délai de livraison et garantie. Points d'attention dans {region} : méfiance envers les prix anormalement bas (sans rapport IEQ, sans confinement adéquat, personnel non certifié), refus de travailler sans inspection préalable, importance de comparer 3 soumissions pour un projet à {ville}. Dans {region}, les délais pour une inspection planifiée sont typiquement de 3-7 jours, et 24-48h pour une urgence. Questions essentielles : le décontamineur est-il certifié IEQ ? Le rapport post-décontamination est-il inclus ? L'assurance responsabilité couvre-t-elle les dommages pendant les travaux ?
Suivi d'un tableau (thead style="background:#0284c7;color:#fff") : Critère | Ce qu'il faut vérifier | Pourquoi c'est important
Lignes : Certification IEQ / IEDQ / Licence RBQ valide / Formation CNESST amiante / Assurance responsabilité 2 M$ / Rapport post-décontamination inclus / Méthode de confinement documentée / Garantie sur les travaux

---
SECTION 6 — FAQ : Décontamination à {ville}
<h2 class="text-3xl font-bold mb-8">Questions fréquentes sur la décontamination à {ville}</h2>
Génère 6 questions-réponses en accordéon HTML avec ces classes exactes :
<details class="group bg-white rounded-xl border border-gray-200 overflow-hidden mb-3">
<summary class="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50">
<span class="font-semibold text-gray-900 pr-4">QUESTION ICI</span>
<svg class="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
</summary>
<div class="px-6 pb-6 text-gray-600 leading-relaxed">RÉPONSE ICI (100-130 mots, précise, avec données locales)</div>
</details>

Questions à couvrir :
1. Combien coûte une décontamination aux moisissures à {ville} (utilise les prix fournis)
2. Comment détecter un problème de moisissures ou d'amiante dans ma maison à {ville}
3. Mon assurance habitation couvre-t-elle la décontamination à {ville}
4. Combien de temps dure une décontamination à {ville} et faut-il quitter les lieux
5. L'amiante est-il encore présent dans les maisons à {ville} et que faire
6. Comment choisir un bon décontamineur certifié IEQ à {ville}

---

RÈGLES ABSOLUES :
- Réponds UNIQUEMENT avec le HTML brut, aucun commentaire avant ou après
- NE génère PAS de wrapper extérieur <div> ou <section> global — commence directement par le contenu des sections
- Pour le texte courant utilise text-gray-900 (titres/spans), text-gray-600 (corps FAQ) — pour les prix utilise <strong class="text-sky-600">X $</strong>
- Intègre les prix fournis directement dans les tableaux et le texte
- Mentionne {ville} et {region} naturellement dans chaque section
- Aucune liste à puces <ul><li> — uniquement <p>, tableaux et accordéons
- Chaque section doit apporter une valeur distincte, pas de répétition\
""",

    "agrandissement": """\
Génère un bloc de contenu HTML COMPLET et RICHE pour la page "agrandissement de maison à {ville}" ({region}, Québec).
Population : {population} habitants.

Contexte régional réel : {context}

Prix locaux fournis (utilise ces données dans le contenu) :
- Extension latérale / agrandissement arrière (maçonnerie, charpente, finition incluse) : {service1_min}$ – {service1_max}$
- Ajout d'étage / mansarde (structure, isolation, finition) : {service2_min}$ – {service2_max}$
- Garage attenant (simple ou double, avec porte de garage) : {service3_min}$ – {service3_max}$
- Agrandissement clé en main entrepreneur général (toutes dimensions) : {service4_min}$ – {service4_max}$

STRUCTURE OBLIGATOIRE — génère ces 6 sections dans l'ordre exact :

---
SECTION 1 — Tableau comparatif des types d'agrandissement à {ville}
<h2 class="text-3xl font-bold mb-4">[Titre accrocheur sur le choix du type d'agrandissement à {ville} — ex: "Extension latérale, ajout d'étage ou garage : quel agrandissement pour votre maison à {ville} ?"]</h2>
Suivi d'un <p> de 180-220 mots sur le marché de l'agrandissement dans {region} : types de projets les plus fréquents selon le parc immobilier local (bungalows vs maisons à étage), pourquoi les propriétaires de {region} choisissent d'agrandir plutôt que déménager (coûts de transaction, attachement au quartier, valeur foncière), tendances récentes des projets (espaces de travail à domicile, suites parentales). Intègre les données chiffrées du contexte régional.
Suivi d'un tableau HTML COMPLET : Type d'agrandissement | Prix à {ville} | Superficie typique | Délai travaux | Permis requis | Valeur ajoutée
Lignes : Extension latérale / Agrandissement arrière / Ajout d'étage complet / Mansarde aménagée / Garage attenant simple / Garage attenant double
Classes tableau : <table class="w-full text-sm border-collapse mt-6 mb-2"> <thead style="background:#0d9488;color:#fff"> <th class="px-4 py-3 text-left font-semibold"> <tbody> <tr class="border-b border-gray-200 hover:bg-gray-50"> <td class="px-4 py-3">

---
SECTION 2 — Facteurs qui font varier le prix d'un agrandissement à {ville}
<h2> accrocheur ancré dans {ville} ou {region}
<p> de 180-220 mots : superficie ajoutée et impact direct sur le coût (prix au pi² moyen dans {region} pour une extension vs construction neuve), type de fondation requise selon le sol de {region} (dalle, pieux vissés, semelles filantes — coût et délais différents selon la géologie locale), complexité structurale (mur porteur à déplacer, renforcement de la charpente existante pour l'ajout d'étage), qualité des matériaux de finition (bardage, revêtement, fenêtres), raccordements (plomberie, électricité, chauffage à étendre dans la nouvelle section), coût de la main-d'oeuvre dans {region} en haute saison (printemps-été — délais 4 à 8 semaines), permis et taxes de la MRC locale. Pour les chiffres clés, utilise <strong class="text-teal-600">X $</strong>.
Suivi d'un tableau (thead style="background:#0d9488;color:#fff") : Facteur | Impact sur le prix | Détail pour {ville}
Lignes : Superficie ajoutée (pi²) / Type de fondation / Complexité structurale / Finition intérieure / Raccordements MEP / Haute saison / Permis et taxes MRC

---
SECTION 3 — Permis, zonage et règlements pour un agrandissement à {ville}
<h2> original mentionnant {ville} ou la MRC de {region}
<p> de 200-250 mots : obligation d'obtenir un permis de construction auprès de la municipalité de {ville} avant tout agrandissement, marges de recul latérales et arrière imposées par le règlement de zonage (typiquement 1,2 m à 2 m selon la zone résidentielle), coefficient d'emprise au sol maximal (souvent 40-50% du terrain), hauteur maximale autorisée (nombre d'étages), règles spécifiques à {region} mentionnées dans le contexte régional, processus de demande de permis (délais habituels, plans requis, certificat d'implantation). Conséquences d'un agrandissement sans permis (ordre de démolition, amende, problèmes à la vente). Mets les montants en <strong class="text-teal-600">X $</strong>.
Suivi d'un tableau (thead style="background:#0d9488;color:#fff") : Démarche | Délai typique à {ville} | Ce qu'il faut fournir
Lignes : Demande de permis de construction / Plan d'implantation (arpenteur) / Plans architecturaux ou de dessinateur / Inspection en cours de travaux / Inspection finale / Certificat de conformité

---
SECTION 4 — Planifier son agrandissement : étapes et calendrier à {ville}
<h2> pratique et motivant, ancré dans {ville}
<p> de 200-250 mots : les étapes dans l'ordre — (1) définir le projet et le budget réaliste incluant une réserve de 15-20%, (2) vérifier la faisabilité avec le service d'urbanisme de {ville}, (3) mandater un dessinateur ou architecte pour les plans, (4) demande de permis (délais variables à {ville}), (5) appel d'offres auprès de 3 entrepreneurs généraux certifiés RBQ dans {region}, (6) signature du contrat avec échéancier, (7) travaux — phases fondation, charpente, enveloppe, finition, (8) inspection finale et certificat. Meilleure période pour lancer un agrandissement dans {region} (fin d'hiver pour les démarches, printemps pour les fondations). Mets les montants en <strong class="text-teal-600">X $</strong>.
Suivi d'un tableau (thead style="background:#0d9488;color:#fff") : Étape | Durée typique | Coût estimé | Intervenant
Lignes : Conception et plans / Permis de construction / Fondation et structure / Enveloppe (toit, murs, fenêtres) / Raccordements MEP / Finition intérieure / Inspection et conformité

---
SECTION 5 — Choisir son entrepreneur en agrandissement à {ville}
<h2> pratique et local
<p> de 200-250 mots : entrepreneur général certifié RBQ (licence 1.1.1 construction résidentielle ou 4.1.1 rénovation résidentielle pour les projets de moins de 3 logements), importance de vérifier que le devis inclut : plans approuvés, permis inclus ou non, sous-traitants (électricien, plombier) certifiés RBQ également. Délais typiques dans {region} en haute saison. Importance de comparer 3 soumissions détaillées — méfiance envers les prix anormalement bas (sans plans ni permis inclus). Contrat écrit obligatoire avec description des travaux, matériaux, calendrier et modalités de paiement. Garanties : Garantie de construction résidentielle (GCR) obligatoire pour les nouvelles constructions, garantie entrepreneur 1 an main-d'oeuvre minimum. Questions essentielles : le permis est-il inclus ? Les sous-traitants sont-ils RBQ ? Y a-t-il une réserve de contingence prévue ?
Suivi d'un tableau (thead style="background:#0d9488;color:#fff") : Critère | Ce qu'il faut vérifier | Pourquoi c'est important
Lignes : Licence RBQ valide / Permis inclus dans le devis / Plans détaillés fournis / Sous-traitants certifiés / Calendrier d'étapes précis / Garantie main-d'oeuvre / Assurance responsabilité civile

---
SECTION 6 — FAQ : Agrandissement de maison à {ville}
<h2 class="text-3xl font-bold mb-8">Questions fréquentes sur l'agrandissement de maison à {ville}</h2>
Génère 6 questions-réponses en accordéon HTML avec ces classes exactes :
<details class="group bg-white rounded-xl border border-gray-200 overflow-hidden mb-3">
<summary class="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50">
<span class="font-semibold text-gray-900 pr-4">QUESTION ICI</span>
<svg class="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
</summary>
<div class="px-6 pb-6 text-gray-600 leading-relaxed">RÉPONSE ICI (100-130 mots, précise, avec données locales)</div>
</details>

Questions à couvrir :
1. Combien coûte un agrandissement de maison à {ville} (utilise les prix fournis)
2. Faut-il un permis pour agrandir sa maison à {ville} et comment l'obtenir
3. Combien de temps prend un agrandissement de maison à {ville}
4. Extension latérale ou ajout d'étage : que choisir pour une maison à {ville}
5. Comment financer un agrandissement de maison à {ville}
6. Quelles marges de recul s'appliquent pour un agrandissement à {ville}

---

RÈGLES ABSOLUES :
- Réponds UNIQUEMENT avec le HTML brut, aucun commentaire avant ou après
- NE génère PAS de wrapper extérieur <div> ou <section> global — commence directement par le contenu des sections
- Pour le texte courant utilise text-gray-900 (titres/spans), text-gray-600 (corps FAQ) — pour les prix utilise <strong class="text-teal-600">X $</strong>
- Intègre les prix fournis directement dans les tableaux et le texte
- Mentionne {ville} et {region} naturellement dans chaque section
- Aucune liste à puces <ul><li> — uniquement <p>, tableaux et accordéons
- Chaque section doit apporter une valeur distincte, pas de répétition\
""",

    "chauffage": """\
Génère un bloc de contenu HTML COMPLET et RICHE pour la page "chauffage à {ville}" ({region}, Québec).
Population : {population} habitants.

Contexte régional réel : {context}

Prix locaux fournis (utilise ces données dans le contenu) :
- Thermopompe murale (installation complète, mural ou mini-split) : {service1_min}$ – {service1_max}$
- Remplacement fournaise (gaz, propane ou électrique, installation incluse) : {service2_min}$ – {service2_max}$
- Chauffage radiant (plancher chauffant, eau ou électrique, par pièce) : {service3_min}$ – {service3_max}$
- Entretien annuel système de chauffage (contrat, nettoyage, vérification) : {service4_min}$ – {service4_max}$

STRUCTURE OBLIGATOIRE — génère ces 6 sections dans l'ordre exact :

---
SECTION 1 — Tableau comparatif des systèmes de chauffage à {ville}
<h2 class="text-3xl font-bold mb-4">[Titre accrocheur sur le choix de chauffage à {ville} — ex: "Thermopompe, fournaise ou radiant : lequel convient à {ville} ?"]</h2>
Suivi d'un <p> de 180-220 mots sur le profil de chauffage de {region} : mix énergétique local (électricité vs gaz vs propane/mazout selon le contexte régional), rigueur des hivers (degrés-jours de chauffage, températures minimales), tendance vers les thermopompes, proportion de maisons avec fournaise centrale vs plinthes. Intègre les données chiffrées du contexte régional.
Suivi d'un tableau HTML COMPLET : Système | Prix à {ville} | Coût annuel moyen | Durée de vie | Subvention dispo | Idéal pour
Lignes : Thermopompe murale (mini-split) / Thermopompe centrale (sur conduits) / Fournaise au gaz naturel / Fournaise électrique / Chauffage radiant plancher / Plinthes électriques
Classes tableau : <table class="w-full text-sm border-collapse mt-6 mb-2"> <thead style="background:#ea580c;color:#fff"> <th class="px-4 py-3 text-left font-semibold"> <tbody> <tr class="border-b border-gray-200 hover:bg-gray-50"> <td class="px-4 py-3">

---
SECTION 2 — Facteurs qui font varier le prix du chauffage à {ville}
<h2> accrocheur ancré dans {ville} ou {region}
<p> de 180-220 mots : superficie de la maison et impact direct sur la puissance BTU requise à {ville}, isolation de l'enveloppe (maisons avant 1980 vs post-2000 — différence de 30-40% de consommation), type de distribution (fournaise sur conduits existants vs thermopompe murale sans conduits), marque et efficacité (SEER, HSPF, AFUE), coût de la main-d'oeuvre dans {region} (pénurie de techniciens RBQ en haute saison), coût d'une mise à niveau électrique (panneau 200A requis pour thermopompe centrale dans les maisons de {region} construites avant 1985). Pour les chiffres clés dans le paragraphe, utilise <strong class="text-orange-600">X $</strong>.
Suivi d'un tableau (thead style="background:#ea580c;color:#fff") : Facteur | Impact sur le prix | Détail pour {ville}
Lignes : Superficie (pi²) / Isolation de l'enveloppe / Maison avec conduits existants / Mise à niveau électrique requise / Urgence vs planifié / Haute saison (sept-nov) / Marque et efficacité SEER/HSPF

---
SECTION 3 — Thermopompe vs Fournaise : quel système choisir à {ville}
<h2> original mentionnant {region} ou le climat de {ville}
<p> de 200-250 mots : thermopompe air-air — avantages double saison (chauffage + climatisation), subventions Rénoclimat, performance en hiver québécois selon le contexte climatique de {region}, nécessité d'un appoint si températures extrêmes ; fournaise électrique — installation simple, coût moindre, mais consommation plus élevée ; fournaise au gaz/propane — pertinente seulement si réseau Énergir accessible à {ville} (selon le contexte régional) ou si propane disponible, coût de fonctionnement vs électricité dans {region} ; thermopompe centrale — idéale si conduits existants, meilleur ROI à long terme. Le bon choix selon le profil de propriétaire à {ville}. Mets les prix en <strong class="text-orange-600">X $</strong>.
Suivi d'un tableau (thead style="background:#ea580c;color:#fff") : Critère | Thermopompe murale | Thermopompe centrale | Fournaise électrique | Fournaise gaz/propane
Lignes : Prix à {ville} | Coût annuel moyen | Subvention disponible | Double usage clim/chauffage | Nécessite conduits | Performance sous -20°C | Durée de vie | Entretien annuel

---
SECTION 4 — Subventions et programmes d'aide au chauffage à {ville}
<h2> direct et rassurant, mentionnant {ville} ou {region}
<p> de 200-250 mots : programme Rénoclimat (montants actuels pour thermopompe murale et centrale dans {region}, conditions d'admissibilité, audit obligatoire ou non), Hydro-Québec LogisVert (montants additionnels pour thermopompes haute performance, cumulable avec Rénoclimat), programme fédéral RCEE (subventions + prêt sans intérêt pour travaux d'enveloppe jumelés à la thermopompe), crédits d'impôt provinciaux et fédéraux, programmes municipaux spécifiques à {region} si mentionnés dans le contexte régional. Quel cumul maximal est possible pour un propriétaire de {ville}. Pour les montants de subventions, utilise <strong class="text-orange-600">X $</strong>.
Suivi d'un tableau (thead style="background:#ea580c;color:#fff") : Programme | Montant disponible | Conditions | Cumulable avec
Lignes : Rénoclimat — thermopompe centrale / Rénoclimat — thermopompe murale / LogisVert Hydro-Québec / RCEE fédéral / Crédit d'impôt provincial / Programme municipal (si applicable)

---
SECTION 5 — Choisir son entrepreneur en chauffage à {ville}
<h2> pratique et local
<p> de 200-250 mots : entrepreneur certifié RBQ (licence 15.10 mécanique du bâtiment ou 16 réfrigération pour les thermopompes), importance du calcul de charge thermique complet (Manual J ou équivalent) pour bien dimensionner le système à {ville}, vérification que le devis inclut : pose, raccordements électriques, mise en service, enlèvement de l'ancien équipement. Délais typiques dans {region} en haute saison (septembre-novembre — délais 2 à 6 semaines). Importance de comparer 3 soumissions pour un projet à {ville}. Garanties : main-d'oeuvre 1 an minimum, équipement selon fabricant (5-10 ans compresseur). Questions essentielles à poser : le devis inclut-il le calcul BTU ? L'entrepreneur est-il certifié réfrigération ? L'ancien équipement est-il inclus dans le retrait ?
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

Questions à couvrir :
1. Combien coûte une thermopompe installée à {ville} (utilise les prix fournis)
2. Thermopompe ou fournaise : que choisir pour le climat de {region}
3. Quelles subventions pour remplacer mon système de chauffage à {ville}
4. Quand faut-il remplacer sa fournaise ou sa thermopompe à {ville}
5. Combien coûte une urgence de chauffage en hiver à {ville}
6. Faut-il un permis pour installer une thermopompe ou une fournaise à {ville}

---

RÈGLES ABSOLUES :
- Réponds UNIQUEMENT avec le HTML brut, aucun commentaire avant ou après
- NE génère PAS de wrapper extérieur <div> ou <section> global — commence directement par le contenu des sections
- Pour le texte courant utilise text-gray-900 (titres/spans), text-gray-600 (corps FAQ) — pour les prix et montants importants utilise <strong class="text-orange-600">X $</strong>
- Intègre les prix fournis directement dans les tableaux et le texte
- Mentionne {ville} et {region} naturellement dans chaque section
- Aucune liste à puces <ul><li> — uniquement <p>, tableaux et accordéons
- Chaque section doit apporter une valeur distincte, pas de répétition\
""",

    "thermopompe-aerothermique": """\
Écris un bloc de contenu HTML pour la page "thermopompe aérothermique à {ville}" ({region}, Québec).

Contexte régional : {context}

Génère 3 sections avec <h2> + <p>. Chaque section doit avoir un angle DISTINCT et un H2 original ancré dans la réalité de {ville}.

RÈGLES ABSOLUES :
- Les H2 doivent être inventés librement à partir du contexte régional — jamais des formules génériques
- Ne commence PAS un paragraphe par "À {ville}" ni par "{ville} est"
- N'utilise PAS la même structure d'ouverture pour deux paragraphes
- Choisis 3 angles parmi les suivants selon ce qui colle le mieux au contexte de {ville} :

ANGLES POSSIBLES (choisis 3) :
A) Le bilan économique réel : coût de fonctionnement d'une aérothermique vs chauffage actuel dans {region}, subventions Rénoclimat/LogisVert disponibles, retour sur investissement réaliste
B) Les performances à froid : comment les modèles actuels tiennent à -25°C/-30°C, différence avec la génération précédente, ce que ça change concrètement en janvier à {ville}
C) La double saison : pourquoi remplacer deux appareils par un seul fait du sens dans le climat de {region} — canicules estivales ET hivers rigoureux, un seul contrat d'entretien
D) Le bon timing pour planifier : printemps = installateurs disponibles + prêt pour l'été et l'hiver, délais d'approvisionnement, comment éviter le rush de septembre
E) Le dimensionnement : erreur la plus coûteuse — sous/sur-dimensionné, calcul BTU chauffage ET refroidissement, ce qu'un mauvais dimensionnement coûte sur 10 ans
F) Choisir son installateur : licence RBQ + certification réfrigération obligatoire, calcul de charge thermique complet, garanties main-d'œuvre, signaux d'alarme à éviter

Chaque paragraphe : 130-160 mots, texte continu, ton expert mais accessible.
Mentionne {ville} et {region} naturellement. Aucune liste à puces. Aucun prix fixe garanti.

Réponds uniquement avec le HTML (3 blocs h2+p), sans introduction ni commentaire.\
""",

    "reparation-thermopompe": """\
Écris un bloc de contenu HTML pour la page "réparation thermopompe à {ville}" ({region}, Québec).

Contexte régional : {context}

Génère 3 sections avec <h2> + <p>. H2 uniques, ancrés dans la réalité concrète de {ville} — pas de formules.

INTERDICTIONS STRICTES pour les H2 :
- Pas de "Quand le froid de {region}..." ni "Quand le gel-dégel..."
- Pas de formule commençant par "Quand le..." ou "Quand la..."
- Pas de formule générique qui fonctionnerait pour n'importe quelle ville

Choisis 3 angles DIFFÉRENTS parmi ceux-ci, dans n'importe quel ordre :
A) Les pannes liées au climat de {region} : gel-dégel, humidité, grands froids — ce que ça fait concrètement au compresseur, au circuit réfrigérant, aux contacteurs
B) Les symptômes à reconnaître : air froid en mode chauffage, unité extérieure givrée en permanence, bruits inhabituels (cliquetis, sifflement), voyant de panne — ce que chaque signe indique
C) Réparer ou remplacer : règle du 50%, âge du système, réfrigérant R-22 interdit à la recharge, comment évaluer honnêtement sa situation sans se faire vendre un remplacement inutile
D) L'entretien préventif : ce qu'on fait en début de saison pour éviter la panne au pire moment, nettoyage des filtres, inspection du circuit, vérification électrique — coût vs panne en plein hiver
E) Urgence et délais : comment trouver un technicien disponible rapidement à {ville}, ce qu'il faut exiger (devis écrit, diagnostic avant remplacement de pièces, pas de devis par téléphone)
F) Certification et licences : attestation provinciale réfrigération obligatoire pour manipuler les fluides, licence RBQ valide, différence entre un technicien certifié et un bricoleur

Chaque paragraphe : 130-160 mots, texte continu, ton rassurant et orienté solution.
Mentionne {ville} naturellement. Aucune liste à puces. Aucune promesse de délai ou de prix garanti.

Réponds uniquement avec le HTML (3 blocs h2+p), sans introduction ni commentaire.\
""",

    "climatisation-thermopompe": """\
Écris un bloc de contenu HTML pour la page "climatisation thermopompe à {ville}" ({region}, Québec).

Contexte régional : {context}

Génère 3 sections avec <h2> + <p>. H2 uniques, ancrés dans la réalité concrète de {ville} — pas de formules.

INTERDICTIONS STRICTES pour les H2 :
- Pas de "Les étés de {ville}..." ni "Les étés de {region}..."
- Pas de "Quand la climatisation devient..."
- Pas de formule commençant par le nom de la ville ou de la région

Choisis 3 angles DIFFÉRENTS parmi ceux-ci, dans n'importe quel ordre :
A) Comparaison économique concrète : coût annuel d'un climatiseur fenêtre vs thermopompe sur 10 ans dans {region}, double usage chauffage/climatisation, un seul entretien annuel
B) Le dimensionnement : erreur qui coûte cher — calcul BTU selon superficie, isolation, fenêtres, exposition. Ce qui se passe quand c'est mal dimensionné en canicule et en hiver à {ville}
C) Le COP en pratique : ce que 3.0 de coefficient signifie concrètement sur la facture d'Hydro-Québec pour un propriétaire de {ville}, comparé à un climatiseur fenêtre
D) L'entretien qui prolonge la durée de vie : ce qu'on fait chaque année, ce que ça coûte, ce que ça évite — et pourquoi les propriétaires de {region} l'oublient souvent
E) Ce que le contexte climatique de {region} exige vraiment : données précises du contexte (températures, jours de chaleur, humidité) et ce que ça implique comme choix de système
F) Choisir son installateur sans se tromper : pourquoi une évaluation sur place est non-négociable, certification réfrigération, garanties fabricant, signaux d'alarme à {ville}

Chaque paragraphe : 130-160 mots, texte continu, ton informatif et concret.
Mentionne {ville} et {region} naturellement. Aucune liste à puces. Aucun prix fixe garanti.

Réponds uniquement avec le HTML (3 blocs h2+p), sans introduction ni commentaire.\
""",

    "installation-thermopompe": """\
Écris un bloc de contenu HTML pour la page "installation thermopompe à {ville}" ({region}, Québec).

Contexte régional : {context}

Génère 3 sections avec <h2> + <p>. H2 uniques, ancrés dans la réalité concrète de {ville} — pas de formules.

INTERDICTIONS STRICTES pour les H2 :
- Pas de "Thermopompe murale ou multi-zones..." ni "Murale ou multi-zones..."
- Pas de "Quel type de thermopompe..."
- Pas de formule générique qui fonctionnerait pour n'importe quelle ville

Choisis 3 angles DIFFÉRENTS parmi ceux-ci, dans n'importe quel ordre :
A) Le COP à froid : pourquoi les hivers de {region} imposent de choisir un système certifié à -25°C — ce que ça change sur les factures de janvier, comment lire une fiche technique
B) Le déroulement réel d'une installation à {ville} : visite de repérage, calcul de charge thermique, câblage 240V, test de pression, activation garantie fabricant — chaque étape et pourquoi elle compte
C) Les subventions Rénoclimat et LogisVert : montants concrets pour les résidents de {region}, conditions d'admissibilité, comment ne pas perdre sa garantie en les réclamant
D) Ce qui fait réellement varier le prix : longueur de ligne frigorifique, accès au mur, mise à niveau électrique, nombre de têtes — comment lire et comparer deux soumissions
E) Garanties et certifications : différence entre garantie fabricant et garantie main-d'œuvre de l'installateur, licence RBQ, attestation réfrigération — ce qui protège vraiment le propriétaire à {ville}
F) Le bon système selon le type de logement de {ville} : unifamiliale, duplex, condo — ce qui change en termes de distribution d'air, d'accès et de capacité selon les constructions typiques de {region}

Chaque paragraphe : 130-160 mots, texte continu, ton pratique et professionnel.
Mentionne {ville} et {region} naturellement. Aucune liste à puces. Aucun prix fixe garanti.

Réponds uniquement avec le HTML (3 blocs h2+p), sans introduction ni commentaire.\
""",

    "pavage-asphalte": """\
Écris un bloc de contenu HTML pour la page "pavage asphalte à {ville}" ({region}, Québec).

Contexte régional : {context}

Génère 3 sections avec <h2> + <p>. Les 3 H2 doivent traiter des aspects COMPLÈTEMENT DIFFÉRENTS — jamais deux H2 sur le même thème.

RÈGLE ABSOLUE : Commence OBLIGATOIREMENT par l'angle numéro {start_angle} pour le premier H2. Puis choisis 2 autres angles différents parmi les restants. Les 3 H2 doivent couvrir 3 thèmes complètement différents.

Les 6 angles (commence par le numéro {start_angle}) :
1) La saison de pavage à {ville} : les bonnes fenêtres météo (mai-juin, août-septembre), pourquoi juillet et octobre sont risqués, comment réserver tôt pour ne pas attendre
2) Ce qui fait vraiment varier le prix : superficie, accès de la cour, pente, type de sol, excavation requise, bordures — comment lire deux soumissions et choisir la bonne
3) Les garanties et le contrat : ce qu'un devis sérieux doit contenir à {ville}, différence garantie main-d'œuvre vs matériaux, signaux d'alarme chez un entrepreneur qui coupe les coins
4) La base granulaire invisible : le facteur que les clients ne voient pas mais qui détermine si l'asphalte dure 10 ou 25 ans dans les conditions de {region}
5) Gel-dégel et entrées à {ville} : ce que les cycles climatiques de {region} font à une entrée mal posée vs bien posée — épaisseur, compaction, drainage
6) Refaire ou recouvrir : quand l'excavation complète s'impose et quand un recouvrement suffit — les signes concrets, ce qu'un bon entrepreneur vérifie avant de recommander

Chaque paragraphe : 130-160 mots, texte continu, ton expert et accessible.
Mentionne {ville} et {region} naturellement. Aucune liste à puces. Aucun prix fixe garanti.

Réponds uniquement avec le HTML (3 blocs h2+p), sans introduction ni commentaire.\
""",

    "prix-pave-uni": """\
Écris un bloc de contenu HTML pour la page "prix pavé uni à {ville}" ({region}, Québec).

Contexte régional : {context}

Génère 3 sections avec <h2> + <p>. Les 3 H2 doivent traiter des aspects COMPLÈTEMENT DIFFÉRENTS — jamais deux H2 sur le même thème.

RÈGLE ABSOLUE : Commence OBLIGATOIREMENT par l'angle numéro {start_angle} pour le premier H2. Puis choisis 2 autres angles différents parmi les restants. Les 3 H2 doivent couvrir 3 thèmes complètement différents.

Les 6 angles (commence par le numéro {start_angle}) :
1) Asphalte vs pavé uni à {ville} : le vrai calcul sur 20 ans — coût initial, entretien, durée de vie, valeur de revente, pour qui le pavé uni a du sens financièrement
2) Les types de pavés et leur vrai coût installé : béton standard, béton premium (Techo-Bloc, Permacon), pierre naturelle — ce que chaque option donne comme résultat à {ville}
3) L'entretien au fil des années : sable polymère, scellant annuel, nettoyage, remplacement de pavés brisés — ce qu'un propriétaire doit faire pour que son investissement dure à {ville}
4) La saison et les délais : pourquoi les bons installateurs sont bookés plusieurs semaines à l'avance au printemps à {ville}, comment planifier pour ne pas attendre
5) Ce qui fait exploser le prix : escaliers, murets, courbes, patrons complexes, excavation profonde — comment lire une soumission et éviter les mauvaises surprises
6) La fondation sous le pavé : pourquoi le lit de sable et la base granulaire déterminent si le pavé résiste aux cycles de {region} pendant 25 ans ou commence à soulever dès le 3e hiver

Chaque paragraphe : 130-160 mots, texte continu, ton expert et accessible.
Mentionne {ville} et {region} naturellement. Aucune liste à puces. Aucun prix fixe garanti.

Réponds uniquement avec le HTML (3 blocs h2+p), sans introduction ni commentaire.\
""",

    "pavage-commercial": """\
Écris un bloc de contenu HTML pour la page "pavage commercial à {ville}" ({region}, Québec).

Contexte régional : {context}

Génère 3 sections avec <h2> + <p>. Les 3 H2 doivent traiter des aspects COMPLÈTEMENT DIFFÉRENTS — jamais deux H2 sur le même thème.

RÈGLE ABSOLUE : Commence OBLIGATOIREMENT par l'angle numéro {start_angle} pour le premier H2. Puis choisis 2 autres angles différents parmi les restants. Les 3 H2 doivent couvrir 3 thèmes complètement différents.

Les 6 angles (commence par le numéro {start_angle}) :
1) Lire et comparer des soumissions commerciales à {ville} : ce qu'un devis sérieux doit contenir (épaisseur spécifiée, type de bitume, compaction, marquage inclus), comment repérer un entrepreneur sous-équipé
2) Scellage et marquage du stationnement : pourquoi sceller dès la première année prolonge la durée de vie de 30% à {ville}, conformité des cases handicapées, renouvellement du marquage
3) Réfection vs entretien préventif : la règle du 15 ans pour un stationnement commercial à {ville}, coût d'un programme d'entretien comparé à une réfection complète après négligence
4) Le drainage commercial : pentes réglementaires, avaloirs, bassins de rétention — ce qu'un stationnement mal drainé coûte en réparations à {ville} après 3 hivers de gel
5) Planifier les phases sans fermer le commerce : comment séquencer les travaux sur un grand stationnement à {ville}, délais réalistes, communication avec locataires et clients
6) Épaisseur et résistance aux charges lourdes : pourquoi un stationnement commercial exige une spécification différente du résidentiel à {ville}, ce qui arrive quand un entrepreneur résidentiel fait du commercial

Chaque paragraphe : 130-160 mots, texte continu, ton B2B expert et direct.
Mentionne {ville} et {region} naturellement. Aucune liste à puces. Aucun prix fixe garanti.

Réponds uniquement avec le HTML (3 blocs h2+p), sans introduction ni commentaire.\
""",

    "prix-toiture": """\
Génère un bloc de contenu HTML COMPLET et RICHE pour la page "prix toiture à {ville}" ({region}, Québec).
Population : {population} habitants.

Contexte régional réel : {context}

Prix locaux fournis (utilise ces données dans le contenu) :
- Bardeaux d'asphalte : {bard_min}$ – {bard_max}$ (maison standard 1200-1500 pi²)
- Toiture métal : {metal_min}$ – {metal_max}$
- Membrane TPO/EPDM : {tpo_min}$ – {tpo_max}$
- Réparation : {rep_min}$ – {rep_max}$

STRUCTURE OBLIGATOIRE — génère ces 6 sections dans l'ordre exact :

---
SECTION 1 — Tableau comparatif complet des matériaux
<h2 class="text-3xl font-bold text-gray-900 mb-4">Comparatif des matériaux de toiture à {ville}</h2>
Suivi d'un <p> de 180-220 mots sur les critères de choix selon le climat de {region} (cycles gel-dégel, charge de neige, durée de vie réelle). Intègre les données climatiques du contexte régional.
Suivi d'un tableau HTML Tailwind COMPLET avec ces colonnes : Matériau | Prix à {ville} | Durée de vie | Avantages | Idéal pour
Lignes : Bardeaux 3 tabs (entrée de gamme) / Bardeaux architecturaux / Bardeaux premium / Toiture métallique / Membrane TPO / Membrane EPDM
Classes tableau : <table class="w-full text-sm border-collapse mt-6 mb-2"> <thead class="bg-gray-900 text-white"> <th class="px-4 py-3 text-left font-semibold"> <tbody> <tr class="border-b border-gray-200 hover:bg-gray-50"> <td class="px-4 py-3">

---
SECTION 2 — Coût selon le type et la taille de maison
<h2> accrocheur ancré dans {ville}
<p> de 180-220 mots : superficie de toit vs superficie habitable, impact de la pente, nombre de lucarnes, facteurs qui font varier le prix à {ville} spécifiquement.
Suivi d'un tableau : Type de maison | Surface de toit estimée | Prix bardeaux | Prix métal | Prix TPO
Lignes : Bungalow 1 étage / Cottage / Maison 2 étages / Maison avec garage / Triplex / Maison ancestrale (avant 1970)

---
SECTION 3 — Impact du climat de {region} sur la durée de vie de votre toit
<h2> original qui intègre une donnée climatique réelle de {region}
<p> de 200-250 mots : cycles gel-dégel, charge de neige, vent, humidité — ce que ces facteurs font concrètement à chaque matériau dans {region}. Durée de vie réaliste locale vs durée de vie théorique du fabricant. Conseil sur l'entretien préventif.

---
SECTION 4 — Ce qui fait vraiment varier le prix d'une réfection à {ville}
<h2> direct et utile
<p> de 200-250 mots : facteurs techniques (pente, lucarnes, cheminées, ventilation, soffites), facteurs logistiques (accès au toit, hauteur, saison), facteurs matériaux (marque, épaisseur du feutre, membrane sous-couche). Explique pourquoi deux maisons identiques peuvent avoir des prix très différents à {ville}.
Suivi d'un tableau facteurs : Facteur | Impact sur le prix | Détail
Lignes : Pente du toit / Nombre de lucarnes / Enlèvement ancienne toiture / Saison des travaux / Accès difficile / Mise à niveau ventilation / Type de feutre/membrane

---
SECTION 5 — Quand réparer vs tout refaire : le guide pour {ville}
<h2> pratique et local
<p> de 200-250 mots : règle des 25%, signes visuels (bardeaux gondolés, granules dans les gouttières, taches d'humidité au plafond), âge du toit selon le parc immobilier de {region}, moment optimal pour agir avant l'hiver à {ville}.

---
SECTION 6 — FAQ : Prix toiture à {ville}
<h2 class="text-3xl font-bold text-gray-900 mb-8">Questions fréquentes sur le prix d'une toiture à {ville}</h2>
Génère 6 questions-réponses en accordéon HTML avec ces classes exactes :
<details class="group bg-white rounded-xl border border-gray-200 overflow-hidden mb-3">
<summary class="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50">
<span class="font-semibold text-gray-900 pr-4">QUESTION ICI</span>
<svg class="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
</summary>
<div class="px-6 pb-6 text-gray-600 leading-relaxed">RÉPONSE ICI (80-120 mots, précise, avec données locales)</div>
</details>

Questions à couvrir (invente des formulations naturelles pour {ville}) :
1. Prix exact d'une toiture pour une maison standard à {ville} (utilise les prix fournis)
2. Durée de vie réaliste d'une toiture dans le climat de {region}
3. Bardeaux vs métal : que choisir à {ville} selon budget et longévité voulue
4. Comment obtenir une soumission fiable d'un couvreur à {ville}
5. Quelle est la meilleure saison pour refaire sa toiture à {ville}
6. La garantie RBQ couvre-t-elle les travaux de toiture à {ville}

---

RÈGLES ABSOLUES :
- Réponds UNIQUEMENT avec le HTML brut, aucun commentaire avant ou après
- Utilise les classes Tailwind déjà définies dans le site (text-gray-900, text-gray-600, font-bold, etc.)
- Intègre les prix fournis ({bard_min}$–{bard_max}$, etc.) directement dans les tableaux et le texte
- Mentionne {ville} et {region} naturellement dans chaque section
- Aucune liste à puces <ul><li> — uniquement <p>, tableaux et accordéons
- Chaque section doit apporter une valeur distincte, pas de répétition\
""",
    "prix-thermopompe": """\
Génère un bloc de contenu HTML COMPLET et RICHE pour la page "prix thermopompe à {ville}" ({region}, Québec).
Population : {population} habitants.

Contexte régional réel : {context}

Prix locaux fournis (utilise ces données dans le contenu) :
- Mini-split 1 zone : {mini_min}$ – {mini_max}$
- Mini-split 2-3 zones : {multi_min}$ – {multi_max}$
- Thermopompe centrale : {centrale_min}$ – {centrale_max}$
- Thermopompe aérothermique : {aero_min}$ – {aero_max}$
- Entretien annuel : {entretien_min}$ – {entretien_max}$

STRUCTURE OBLIGATOIRE — génère ces 6 sections dans l'ordre exact :

---
SECTION 1 — Tableau comparatif des types de thermopompes
<h2 class="text-3xl font-bold text-gray-900 mb-4">Comparatif des thermopompes à {ville}</h2>
Suivi d'un <p> de 180-220 mots sur les critères de choix selon le climat de {region} (hivers rigoureux, besoins chauffage vs climatisation, type de maison dominant). Intègre les données climatiques du contexte régional.
Suivi d'un tableau HTML Tailwind COMPLET : Type | Prix à {ville} | COP moyen | Idéal pour | Subvention possible
Lignes : Mini-split 1 zone / Mini-split 2-3 zones / Thermopompe centrale / Aérothermique / Géothermique
Classes tableau : <table class="w-full text-sm border-collapse mt-6 mb-2"> <thead class="bg-gray-900 text-white"> <th class="px-4 py-3 text-left font-semibold"> <tbody> <tr class="border-b border-gray-200 hover:bg-gray-50"> <td class="px-4 py-3">

---
SECTION 2 — Coût selon le type de maison à {ville}
<h2> accrocheur ancré dans {ville}
<p> de 180-220 mots : superficie, nombre de zones, isolation existante, type de chauffage remplacé — facteurs qui font varier le prix d'installation à {ville} spécifiquement.
Suivi d'un tableau : Type de maison | Système recommandé | Prix estimé à {ville} | Économies annuelles
Lignes : Condo / Bungalow 1000 pi² / Maison 1500 pi² / Maison 2000+ pi² / Maison mal isolée / Chalet saisonnier

---
SECTION 3 — Subventions et programmes disponibles en {region}
<h2> original mentionnant {region} ou {ville}
<p> de 200-250 mots : détail des programmes Hydro-Québec (Thermopompe résidentielle), Rénoclimat, LogisVert, Canada Greener Homes — montants réels, conditions d'éligibilité, comment les combiner. Calcule l'économie nette après subventions sur le prix d'un mini-split standard à {ville}.

---
SECTION 4 — Ce qui fait vraiment varier le prix à {ville}
<h2> direct et utile
<p> de 200-250 mots : facteurs techniques (linéaire de tuyauterie, perçage de murs, électricité à mettre aux normes), marques (Mitsubishi, Daikin, Fujitsu vs génériques), saison. Explique pourquoi deux maisons similaires à {ville} peuvent avoir des prix très différents.
Suivi d'un tableau facteurs : Facteur | Impact sur le prix | Détail
Lignes : Linéaire de tuyauterie / Mise à niveau électrique / Nombre de zones / Marque et modèle / Saison d'installation / Accès difficile / Retrait ancien système

---
SECTION 5 — Économies réelles et retour sur investissement à {ville}
<h2> pratique mentionnant {ville}
<p> de 200-250 mots : calcul du retour sur investissement selon le chauffage remplacé (mazout, propane, plinthes électriques), COP réel en hiver québécois, économies annuelles typiques en {region}, durée de vie 15-20 ans, coût d'entretien. Sois précis avec des chiffres réalistes.

---
SECTION 6 — FAQ : Prix thermopompe à {ville}
<h2 class="text-3xl font-bold text-gray-900 mb-8">Questions fréquentes sur le prix d'une thermopompe à {ville}</h2>
Génère 6 questions-réponses en accordéon HTML avec ces classes exactes :
<details class="group bg-white rounded-xl border border-gray-200 overflow-hidden mb-3">
<summary class="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50">
<span class="font-semibold text-gray-900 pr-4">QUESTION ICI</span>
<svg class="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
</summary>
<div class="px-6 pb-6 text-gray-600 leading-relaxed">RÉPONSE ICI (80-120 mots, précise, avec données locales)</div>
</details>

Questions à couvrir :
1. Prix exact d'un mini-split à {ville} (utilise les prix fournis)
2. Quelle subvention peut-on obtenir à {ville} en {region}
3. Mini-split ou thermopompe centrale : que choisir pour une maison à {ville}
4. Combien économise-t-on sur le chauffage avec une thermopompe à {ville}
5. Quelle marque de thermopompe choisir au Québec et pourquoi
6. Combien de temps dure l'installation d'une thermopompe à {ville}

---

RÈGLES ABSOLUES :
- Réponds UNIQUEMENT avec le HTML brut, aucun commentaire avant ou après
- Utilise les classes Tailwind déjà définies dans le site (text-gray-900, text-gray-600, font-bold, etc.)
- Intègre les prix fournis dans les tableaux et le texte
- Mentionne {ville} et {region} naturellement dans chaque section
- Aucune liste à puces <ul><li> — uniquement <p>, tableaux et accordéons
- Chaque section doit apporter une valeur distincte, pas de répétition\
""",

    "prix-drain": """\
Génère un bloc de contenu HTML COMPLET et RICHE pour la page "prix drainage résidentiel à {ville}" ({region}, Québec).
Population : {population} habitants.

Contexte régional réel : {context}

Prix locaux fournis (utilise ces données dans le contenu) :
- Installation drain français complet : {drain_min}$ – {drain_max}$
- Réparation/injection fissure : {fissure_min}$ – {fissure_max}$
- Imperméabilisation extérieure : à partir de {impermea_min}$

STRUCTURE OBLIGATOIRE — génère ces 6 sections dans l'ordre exact :

---
SECTION 1 — Tableau comparatif des types de travaux de drainage
<h2 class="text-3xl font-bold text-gray-900 mb-4">Types de travaux de drainage à {ville}</h2>
Suivi d'un <p> de 180-220 mots sur les enjeux de drainage résidentiel dans {region} (cycles gel-dégel, nappe phréatique, argile, pression hydrostatique printanière). Intègre les données climatiques du contexte régional.
Suivi d'un tableau HTML Tailwind COMPLET : Type de travail | Prix à {ville} | Durée | Garantie typique | Quand le faire
Lignes : Drain français complet / Drain de fondation (partiel) / Injection polyuréthane (fissure) / Imperméabilisation extérieure / Membrane Delta / Pompe de puisard
Classes tableau : <table class="w-full text-sm border-collapse mt-6 mb-2"> <thead class="bg-gray-900 text-white"> <th class="px-4 py-3 text-left font-semibold"> <tbody> <tr class="border-b border-gray-200 hover:bg-gray-50"> <td class="px-4 py-3">

---
SECTION 2 — Coût selon le type de maison à {ville}
<h2> accrocheur ancré dans {ville}
<p> de 180-220 mots : périmètre de fondation, profondeur d'excavation, type de sol (argile, sable, roc), accès, distance de rejet des eaux — facteurs qui font varier le prix à {ville} spécifiquement.
Suivi d'un tableau : Type de maison | Travail typique | Prix estimé à {ville} | Durée des travaux
Lignes : Bungalow 900 pi² / Cottage / Maison 2 étages / Semi-détaché / Maison ancestrale avant 1970 / Maison en terrain en pente

---
SECTION 3 — Ce que le gel-dégel de {region} fait à vos fondations
<h2> original qui intègre une donnée climatique réelle de {region}
<p> de 200-250 mots : ce que les cycles gel-dégel de {region} font concrètement aux drains et fondations, pression hydrostatique printanière, argile gonflante, pourquoi les maisons de {region} sont particulièrement exposées. Données chiffrées sur les cycles annuels. Conseil préventif.

---
SECTION 4 — Ce qui fait vraiment varier le prix à {ville}
<h2> direct et utile
<p> de 200-250 mots : type de sol (argile vs sable vs roc), largeur d'accès latéral pour excavatrice, profondeur de fondation, présence de garage ou perron, longueur de tuyau, point de rejet des eaux. Explique pourquoi deux bungalows similaires à {ville} peuvent avoir des prix très différents.
Suivi d'un tableau facteurs : Facteur | Impact sur le prix | Détail
Lignes : Type de sol argileux / Accès difficile (côté étroit) / Profondeur fondation / Présence garage ou perron / Longueur du drain / Point de rejet éloigné / Saison des travaux

---
SECTION 5 — Les signes que votre drainage est défaillant : guide pour {ville}
<h2> pratique et local
<p> de 200-250 mots : eau dans le sous-sol après pluie ou fonte des neiges, odeur d'humidité persistante, efflorescence sur le béton, fissures en escalier dans la fondation, sol qui s'affaisse près de la maison. Expliquer la différence entre un problème de fissure injectable et un drain à remplacer entièrement. Moment optimal pour agir avant l'hiver à {ville}.

---
SECTION 6 — FAQ : Drainage résidentiel à {ville}
<h2 class="text-3xl font-bold text-gray-900 mb-8">Questions fréquentes sur le drainage à {ville}</h2>
Génère 6 questions-réponses en accordéon HTML avec ces classes exactes :
<details class="group bg-white rounded-xl border border-gray-200 overflow-hidden mb-3">
<summary class="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50">
<span class="font-semibold text-gray-900 pr-4">QUESTION ICI</span>
<svg class="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
</summary>
<div class="px-6 pb-6 text-gray-600 leading-relaxed">RÉPONSE ICI (80-120 mots, précise, avec données locales)</div>
</details>

Questions à couvrir :
1. Combien coûte un drain français complet à {ville} (utilise les prix fournis)
2. Quelle est la différence entre drain français et imperméabilisation
3. Mon sous-sol est humide — drain, injection ou imperméabilisation : que choisir à {ville}
4. Les travaux de drainage sont-ils subventionnés ou déductibles d'impôt
5. Quelle garantie exiger d'un entrepreneur en drainage à {ville}
6. Faut-il un permis de construction pour refaire son drain à {ville}

---

RÈGLES ABSOLUES :
- Réponds UNIQUEMENT avec le HTML brut, aucun commentaire avant ou après
- Utilise les classes Tailwind déjà définies dans le site (text-gray-900, text-gray-600, font-bold, etc.)
- Intègre les prix fournis directement dans les tableaux et le texte
- Mentionne {ville} et {region} naturellement dans chaque section
- Aucune liste à puces <ul><li> — uniquement <p>, tableaux et accordéons
- Chaque section doit apporter une valeur distincte, pas de répétition\
""",

    "prix-fissure": """\
Génère un bloc de contenu HTML COMPLET et RICHE pour la page "prix réparation fissure fondation à {ville}" ({region}, Québec).
Population : {population} habitants.

Contexte régional réel : {context}

Prix locaux fournis (utilise ces données dans le contenu) :
- Fissure simple (injection polyuréthane) : {simple_min}$ – {simple_max}$
- Fissure avec infiltration active : {infiltration_min}$ – {infiltration_max}$
- Fissure structurale (époxy + renfort) : {struct_min}$ – {struct_max}$

STRUCTURE OBLIGATOIRE — génère ces 6 sections dans l'ordre exact :

---
SECTION 1 — Tableau comparatif des types de fissures et méthodes de réparation
<h2 class="text-3xl font-bold text-gray-900 mb-4">Types de fissures de fondation à {ville}</h2>
Suivi d'un <p> de 180-220 mots sur les causes des fissures dans {region} (gel-dégel, argile, pression latérale, tassement différentiel, retrait du béton). Intègre les données climatiques du contexte régional.
Suivi d'un tableau HTML Tailwind COMPLET : Type de fissure | Prix à {ville} | Méthode | Urgence | Résultat attendu
Lignes : Fissure capillaire (cheveu) / Fissure par retrait (béton neuf) / Fissure avec suintement / Fissure avec infiltration active / Fissure diagonale (tassement) / Fissure structurale (horizontale)
Classes tableau : <table class="w-full text-sm border-collapse mt-6 mb-2"> <thead class="bg-gray-900 text-white"> <th class="px-4 py-3 text-left font-semibold"> <tbody> <tr class="border-b border-gray-200 hover:bg-gray-50"> <td class="px-4 py-3">

---
SECTION 2 — Coût selon la gravité et le type de maison à {ville}
<h2> accrocheur ancré dans {ville}
<p> de 180-220 mots : nombre de fissures, accessibilité intérieure vs excavation extérieure, longueur de la fissure, âge de la fondation, présence d'humidité — facteurs qui font varier le prix à {ville}.
Suivi d'un tableau : Scénario | Méthode recommandée | Prix estimé à {ville} | Durée intervention
Lignes : 1 fissure capillaire / 1 fissure avec infiltration / Fissure avec moisissures / 3-4 fissures simultanées / Fissure + drain défaillant / Fissure structurale avec déplacement

---
SECTION 3 — Pourquoi les fondations de {region} fissurent plus
<h2> original qui intègre une donnée climatique réelle de {region}
<p> de 200-250 mots : nombre de cycles gel-dégel par an dans {region}, sols argileux et pression hydrostatique, fondations d'avant 1980 moins armées, épaisseur de béton des constructions de l'époque. Pourquoi agir vite dans le contexte de {ville} avant que la fissure s'aggrave.

---
SECTION 4 — Injection polyuréthane vs époxy vs excavation : que choisir à {ville}
<h2> direct et comparatif
<p> de 200-250 mots : différences concrètes entre les trois méthodes principales, quand chaque méthode s'applique, avantages et limites, durabilité attendue dans le contexte climatique de {region}. Ce qui détermine le choix : accessibilité, profondeur, type de fissure.
Suivi d'un tableau comparatif : Méthode | Prix à {ville} | Durabilité | Idéal pour | Limite principale
Lignes : Injection polyuréthane / Injection époxy / Excavation extérieure + membrane / Renfort intérieur (plaques carbone)

---
SECTION 5 — Quand agir d'urgence vs attendre : guide pour les propriétaires de {ville}
<h2> pratique et local
<p> de 200-250 mots : signes d'urgence (eau qui coule activement, fissure qui s'élargit, déplacement visible du mur, efflorescence extensive), signes à surveiller sans urgence immédiate (petite fissure sèche stable), moment idéal pour intervenir selon les saisons de {region}. Comment photographier et mesurer sa fissure pour obtenir un devis précis.

---
SECTION 6 — FAQ : Réparation fissure à {ville}
<h2 class="text-3xl font-bold text-gray-900 mb-8">Questions fréquentes sur la réparation de fissures à {ville}</h2>
Génère 6 questions-réponses en accordéon HTML avec ces classes exactes :
<details class="group bg-white rounded-xl border border-gray-200 overflow-hidden mb-3">
<summary class="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50">
<span class="font-semibold text-gray-900 pr-4">QUESTION ICI</span>
<svg class="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
</summary>
<div class="px-6 pb-6 text-gray-600 leading-relaxed">RÉPONSE ICI (80-120 mots, précise, avec données locales)</div>
</details>

Questions à couvrir :
1. Combien coûte une injection polyuréthane à {ville} (utilise les prix fournis)
2. Ma fissure est-elle structurale ou cosmétique — comment le savoir à {ville}
3. L'injection de fissure est-elle permanente dans le climat de {region}
4. Peut-on réparer une fissure soi-même ou faut-il un professionnel à {ville}
5. Ma garantie de construction couvre-t-elle les fissures de fondation
6. Combien de temps prend une réparation de fissure par injection à {ville}

---

RÈGLES ABSOLUES :
- Réponds UNIQUEMENT avec le HTML brut, aucun commentaire avant ou après
- Utilise les classes Tailwind déjà définies dans le site (text-gray-900, text-gray-600, font-bold, etc.)
- Intègre les prix fournis directement dans les tableaux et le texte
- Mentionne {ville} et {region} naturellement dans chaque section
- Aucune liste à puces <ul><li> — uniquement <p>, tableaux et accordéons
- Chaque section doit apporter une valeur distincte, pas de répétition\
""",

    "prix-fenetres": """\
Génère un bloc de contenu HTML COMPLET et RICHE pour la page "prix remplacement fenêtres à {ville}" ({region}, Québec).
Population : {population} habitants.

Contexte régional réel : {context}

Prix locaux fournis (utilise ces données dans le contenu) :
- Fenêtre PVC : {pvc_min}$ – {pvc_max}$ (par fenêtre installée)
- Fenêtre hybride bois-alu : {hyb_min}$ – {hyb_max}$ (par fenêtre installée)
- Porte-fenêtre : {pf_min}$ – {pf_max}$ (installée)

STRUCTURE OBLIGATOIRE — génère ces 6 sections dans l'ordre exact :

---
SECTION 1 — Tableau comparatif des types de fenêtres
<h2 class="text-3xl font-bold text-gray-900 mb-4">Comparatif des types de fenêtres à {ville}</h2>
Suivi d'un <p> de 180-220 mots sur les enjeux de performance thermique dans {region} (rigueur des hivers, ponts thermiques, condensation, triple vitrage). Intègre les données climatiques du contexte régional.
Suivi d'un tableau HTML Tailwind COMPLET : Type | Prix à {ville} | Durée de vie | Cote ÉnerGuide | Entretien | Idéal pour
Lignes : PVC blanc / PVC couleur / Hybride bois-alu / Aluminium / Bois naturel traité / Porte-fenêtre PVC
Classes tableau : <table class="w-full text-sm border-collapse mt-6 mb-2"> <thead class="bg-gray-900 text-white"> <th class="px-4 py-3 text-left font-semibold"> <tbody> <tr class="border-b border-gray-200 hover:bg-gray-50"> <td class="px-4 py-3">

---
SECTION 2 — Coût total selon le type de maison à {ville}
<h2> accrocheur ancré dans {ville}
<p> de 180-220 mots : nombre de fenêtres typique selon le type de maison à {ville}, format des fenêtres (battant, coulissant, à guillotine), impact des dimensions hors-standard, retrait de l'ancienne fenêtre et finition intérieure.
Suivi d'un tableau : Type de maison | Nb fenêtres typique | Budget PVC total | Budget hybride total | Durée des travaux
Lignes : Condo / Bungalow 3 chambres / Maison 4-5 pièces / Maison 2 étages / Maison ancestrale (formats spéciaux) / Remplacement partiel (5 fenêtres)

---
SECTION 3 — Économies d'énergie et programmes disponibles à {ville}
<h2> original mentionnant {region} ou {ville}
<p> de 200-250 mots : économies réelles sur la facture de chauffage avec des fenêtres triple vitrage certifiées ENERGY STAR dans le contexte de {region}, programmes Rénoclimat, Canada Greener Homes, retour sur investissement réaliste sur 10 ans à {ville}.

---
SECTION 4 — Ce qui fait vraiment varier le prix à {ville}
<h2> direct et utile
<p> de 200-250 mots : format hors-standard, hauteur d'étage (échafaudage), remplacement cadre complet vs insert seulement, finition intérieure (boiseries), marque et certification, nombre de fenêtres (économie d'échelle). Explique pourquoi deux maisons similaires à {ville} peuvent avoir des coûts très différents.
Suivi d'un tableau facteurs : Facteur | Impact sur le prix | Détail
Lignes : Format hors-standard / Fenêtre en hauteur (échafaudage) / Remplacement cadre complet / Finition intérieure incluse / Certification ENERGY STAR / Volume (économie d'échelle) / Retrait fenêtres peintes ou scellées

---
SECTION 5 — Les signes que vos fenêtres sont à remplacer : guide pour {ville}
<h2> pratique et local
<p> de 200-250 mots : condensation entre les vitres (sceau brisé), courants d'air autour du cadre, givre intérieur en hiver, cadres qui ferment mal, moisissures dans les coins, facture de chauffage qui augmente. Durée de vie réelle selon les matériaux dans le contexte de {region}. Quand tout remplacer d'un coup vs graduellement.

---
SECTION 6 — Comment choisir son installateur de fenêtres à {ville}
<h2> direct et rassurant, ancré dans {ville}
<p> de 200-250 mots : quoi vérifier avant d'embaucher un installateur à {ville} — licence RBQ obligatoire (vérifiable sur le registre), assurance responsabilité civile minimale, garantie main-d'œuvre distincte de la garantie fabricant, ce qu'une bonne soumission doit inclure (marque exacte, cote ER, dimensions, délais, conditions de paiement). Explique pourquoi deux soumissions au même prix peuvent cacher une différence de qualité importante. Mentionne les pratiques à éviter (acompte excessif, pression à signer sur place, fenêtres sans cote ÉnerGuide). Adapte les conseils au contexte local de {region} (délais en haute saison, disponibilité des installateurs certifiés).
Suivi d'un tableau : Critère | Ce qu'il faut vérifier | Pourquoi c'est important
Lignes : Licence RBQ / Assurance RC / Garantie main-d'œuvre / Cote ÉnerGuide sur devis / Acompte demandé / Délai de livraison confirmé / Références locales vérifiables

---
SECTION 7 — FAQ : Remplacement de fenêtres à {ville}
<h2 class="text-3xl font-bold text-gray-900 mb-8">Questions fréquentes sur le prix des fenêtres à {ville}</h2>
Génère 6 questions-réponses en accordéon HTML avec ces classes exactes :
<details class="group bg-white rounded-xl border border-gray-200 overflow-hidden mb-3">
<summary class="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50">
<span class="font-semibold text-gray-900 pr-4">QUESTION ICI</span>
<svg class="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
</summary>
<div class="px-6 pb-6 text-gray-600 leading-relaxed">RÉPONSE ICI (80-120 mots, précise, avec données locales)</div>
</details>

Questions à couvrir :
1. Combien coûte une fenêtre PVC installée à {ville} (utilise les prix fournis)
2. PVC ou hybride bois-alu : que choisir à {ville} selon le budget et la longévité
3. Le triple vitrage est-il nécessaire dans le climat de {region}
4. Peut-on obtenir des subventions pour remplacer ses fenêtres à {ville}
5. Combien de temps prend le remplacement de 10 fenêtres dans une maison à {ville}
6. Faut-il un permis de construction pour remplacer ses fenêtres à {ville}

---

RÈGLES ABSOLUES :
- Réponds UNIQUEMENT avec le HTML brut, aucun commentaire avant ou après
- Utilise les classes Tailwind déjà définies dans le site (text-gray-900, text-gray-600, font-bold, etc.)
- Intègre les prix fournis directement dans les tableaux et le texte
- Mentionne {ville} et {region} naturellement dans chaque section
- Aucune liste à puces <ul><li> — uniquement <p>, tableaux et accordéons
- Chaque section doit apporter une valeur distincte, pas de répétition\
""",

    "excavation": """\
Génère un bloc de contenu HTML COMPLET et RICHE pour la page "prix excavation à {ville}" ({region}, Québec).
Population : {population} habitants.

Contexte régional réel : {context}

Prix locaux fournis (utilise ces données dans le contenu) :
- Excavation générale : {excav_min}$ – {excav_max}$
- Terrassement / remblai : {terras_min}$ – {terras_max}$
- Drainage / fossé : {drain_min}$ – {drain_max}$
- Fondation / piscine creusée : {fondation_min}$ – {fondation_max}$

STRUCTURE OBLIGATOIRE — génère ces 6 sections dans l'ordre exact :

---
SECTION 1 — Tableau comparatif des types de travaux d'excavation
<h2 class="text-3xl font-bold text-gray-900 mb-4">Types de travaux d'excavation à {ville}</h2>
Suivi d'un <p> de 180-220 mots sur les enjeux de l'excavation résidentielle dans {region} : type de sol dominant (argile, sable, roc, till), profondeur de gel, nappe phréatique, contraintes d'accès urbain vs rural. Intègre les données du contexte régional.
Suivi d'un tableau HTML Tailwind COMPLET : Type de travail | Prix à {ville} | Durée typique | Équipement requis | Permis requis
Lignes : Excavation générale (terrassement) / Remblai et nivellement / Creusage pour fondation / Piscine creusée / Drainage / fossé / Démolition et déblai
Classes tableau : <table class="w-full text-sm border-collapse mt-6 mb-2"> <thead class="bg-gray-900 text-white"> <th class="px-4 py-3 text-left font-semibold"> <tbody> <tr class="border-b border-gray-200 hover:bg-gray-50"> <td class="px-4 py-3">

---
SECTION 2 — Coût selon le type de projet à {ville}
<h2> accrocheur ancré dans {ville}
<p> de 180-220 mots : superficie à excaver, profondeur, type de sol (argile = plus lent et cher, roc = dynamitage), accès de l'équipement, distance de rejet des déblais, besoin de remblai — facteurs qui font varier le prix à {ville} spécifiquement.
Suivi d'un tableau : Type de projet | Superficie typique | Prix estimé à {ville} | Durée des travaux
Lignes : Sous-sol résidentiel / Fondation pour garage / Piscine creusée 16x32 / Piscine creusée 20x40 / Terrassement entrée + cour / Système de drainage complet

---
SECTION 3 — Ce que le sol de {region} implique pour vos travaux
<h2> original qui intègre une donnée géologique ou climatique réelle de {region}
<p> de 200-250 mots : type de sol dominant dans {region} (argile marine, till glaciaire, roc du Bouclier canadien, sable, etc.), profondeur de gel typique en cm, nappe phréatique, défi particulier que ça pose pour l'excavation et le drainage, comment un bon entrepreneur s'adapte. Conseil sur le choix d'équipement selon le sol de {region}.

---
SECTION 4 — Ce qui fait vraiment varier le prix à {ville}
<h2> direct et utile
<p> de 200-250 mots : type de sol (argile vs sable vs roc), largeur d'accès pour la machinerie, distance de transport des déblais, présence de services souterrains (gaz, électricité, aqueduc), dénivelé du terrain, saison (sol gelé), permis et inspection requis par la municipalité de {ville}. Explique pourquoi deux projets similaires à {ville} peuvent avoir des coûts très différents.
Suivi d'un tableau facteurs : Facteur | Impact sur le prix | Détail
Lignes : Type de sol argileux ou rocheux / Accès machinerie (rue étroite) / Distance de transport des déblais / Présence de services souterrains / Dénivelé important / Sol gelé (saison) / Permis municipal requis

---
SECTION 5 — Permis, règlements et certification à {ville}
<h2> pratique et local
<p> de 200-250 mots : obligation de localisation des services souterrains (Info-Excavation est obligatoire avant tout creusage au Québec), permis requis par la plupart des municipalités pour excavation de fondation ou piscine creusée, certification RBQ (licence 1.1.1 ou 1.2.1 selon le type de travaux), assurance responsabilité exigée, inspection de chantier selon le type de projet. Préciser ce que ça implique concrètement pour un propriétaire à {ville}.

---
SECTION 6 — FAQ : Excavation à {ville}
<h2 class="text-3xl font-bold text-gray-900 mb-8">Questions fréquentes sur les travaux d'excavation à {ville}</h2>
Génère 6 questions-réponses en accordéon HTML avec ces classes exactes :
<details class="group bg-white rounded-xl border border-gray-200 overflow-hidden mb-3">
<summary class="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50">
<span class="font-semibold text-gray-900 pr-4">QUESTION ICI</span>
<svg class="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
</summary>
<div class="px-6 pb-6 text-gray-600 leading-relaxed">RÉPONSE ICI (80-120 mots, précise, avec données locales)</div>
</details>

Questions à couvrir :
1. Combien coûte une excavation générale à {ville} (utilise les prix fournis)
2. Faut-il un permis pour excaver un terrain résidentiel à {ville}
3. Mon terrain est argileux — qu'est-ce que ça change pour le prix et les travaux à {ville}
4. Combien de temps prend l'excavation pour une piscine creusée à {ville}
5. Qu'est-ce qu'Info-Excavation et est-ce obligatoire à {ville}
6. Comment choisir un entrepreneur en excavation certifié RBQ à {ville}

---

RÈGLES ABSOLUES :
- Réponds UNIQUEMENT avec le HTML brut, aucun commentaire avant ou après
- Utilise les classes Tailwind déjà définies dans le site (text-gray-900, text-gray-600, font-bold, etc.)
- Intègre les prix fournis directement dans les tableaux et le texte
- Mentionne {ville} et {region} naturellement dans chaque section
- Aucune liste à puces <ul><li> — uniquement <p>, tableaux et accordéons
- Chaque section doit apporter une valeur distincte, pas de répétition\
""",

    "prix-revetement": """\
Génère un bloc de contenu HTML COMPLET et RICHE pour la page "prix revêtement extérieur à {ville}" ({region}, Québec).
Population : {population} habitants.

Contexte régional réel : {context}

Prix locaux fournis — coût complet installé pour une maison standard (utilise ces données dans le contenu) :
- Vinyle : {vinyle_min}$ – {vinyle_max}$
- Canexel (fibres de bois) : {canexel_min}$ – {canexel_max}$
- Fibrociment (HardiePlank) : {fibrociment_min}$ – {fibrociment_max}$
- Aluminium : {aluminium_min}$ – {aluminium_max}$

STRUCTURE OBLIGATOIRE — génère ces 6 sections dans l'ordre exact :

---
SECTION 1 — Tableau comparatif des types de revêtement extérieur
<h2 class="text-3xl font-bold text-gray-900 mb-4">Comparatif des revêtements extérieurs à {ville}</h2>
Suivi d'un <p> de 180-220 mots sur les enjeux de durabilité dans {region} (cycles gel-dégel, humidité, UV, vent). Intègre les données climatiques du contexte régional.
Suivi d'un tableau HTML Tailwind COMPLET : Matériau | Prix à {ville} | Durée de vie | Entretien | Résistance gel-dégel | Idéal pour
Lignes : Vinyle standard / Vinyle premium / Canexel / Fibrociment (HardiePlank) / Aluminium / Bois naturel traité / Brique parement / Crépi
Classes tableau : <table class="w-full text-sm border-collapse mt-6 mb-2"> <thead class="bg-gray-900 text-white"> <th class="px-4 py-3 text-left font-semibold"> <tbody> <tr class="border-b border-gray-200 hover:bg-gray-50"> <td class="px-4 py-3">

---
SECTION 2 — Coût selon le type de maison à {ville}
<h2> accrocheur ancré dans {ville}
<p> de 180-220 mots : superficie de façade vs superficie habitable, nombre de pignons, soffites et fascias inclus ou non, découpe autour des fenêtres et portes, hauteur de maison (échafaudage).
Suivi d'un tableau : Type de maison | Surface approx. | Prix vinyle | Prix Canexel | Prix fibrociment | Durée chantier
Lignes : Bungalow simple / Maison plain-pied à pignons / Cottage / Maison 2 étages / Maison avec garage / Maison ancestrale avant 1960

---
SECTION 3 — Ce que le climat de {region} exige vraiment de votre revêtement
<h2> original qui intègre une donnée climatique réelle de {region}
<p> de 200-250 mots : nombre de cycles gel-dégel dans {region}, accumulation de glace derrière un revêtement mal posé, UV estivaux, humidité relative, pourquoi certains matériaux résistent moins dans {region} qu'ailleurs. Conseils sur la barrière pare-air et la lisse de départ.

---
SECTION 4 — Ce qui fait vraiment varier le prix à {ville}
<h2> direct et utile
<p> de 200-250 mots : retrait de l'ancien revêtement (vinyle vs brique), isolation ajoutée, soffites et fascias remplacés en même temps, hauteur de chantier, accès difficile. Explique pourquoi deux maisons similaires à {ville} peuvent avoir des prix très différents.
Suivi d'un tableau facteurs : Facteur | Impact sur le prix | Détail
Lignes : Retrait ancien revêtement / Isolation sous-jacente / Soffites et fascias / Nombre de fenêtres / Hauteur (échafaudage) / Accès difficile / Saison des travaux

---
SECTION 5 — Vinyle vs Canexel vs Fibrociment : que choisir à {ville}
<h2> comparatif pratique ancré dans {ville}
<p> de 200-250 mots : comparaison directe des trois matériaux les plus populaires dans {region} — durabilité réelle après 20 ans dans le contexte climatique local, entretien requis, résistance aux chocs, valeur de revente. Cas où le bois ou la brique s'imposent malgré le prix. Ce que les installateurs de {ville} recommandent le plus souvent.

---
SECTION 6 — FAQ : Revêtement extérieur à {ville}
<h2 class="text-3xl font-bold text-gray-900 mb-8">Questions fréquentes sur le prix du revêtement extérieur à {ville}</h2>
Génère 6 questions-réponses en accordéon HTML avec ces classes exactes :
<details class="group bg-white rounded-xl border border-gray-200 overflow-hidden mb-3">
<summary class="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50">
<span class="font-semibold text-gray-900 pr-4">QUESTION ICI</span>
<svg class="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
</summary>
<div class="px-6 pb-6 text-gray-600 leading-relaxed">RÉPONSE ICI (80-120 mots, précise, avec données locales)</div>
</details>

Questions à couvrir :
1. Combien coûte un revêtement vinyle installé à {ville} (utilise les prix fournis)
2. Canexel ou vinyle : lequel choisit-on le plus à {ville} et pourquoi
3. Le fibrociment HardiePlank dure-t-il vraiment plus longtemps dans le climat de {region}
4. Peut-on poser un nouveau revêtement par-dessus l'ancien à {ville}
5. Combien de temps prend un chantier de revêtement extérieur complet à {ville}
6. Faut-il un permis de construction pour changer son revêtement extérieur à {ville}

---

RÈGLES ABSOLUES :
- Réponds UNIQUEMENT avec le HTML brut, aucun commentaire avant ou après
- NE génère PAS de wrapper extérieur <div> ou <section> global — commence directement par le contenu des sections
- Utilise les classes Tailwind déjà définies dans le site (text-gray-900, text-gray-600, font-bold, etc.)
- Intègre les prix fournis directement dans les tableaux et le texte
- Mentionne {ville} et {region} naturellement dans chaque section
- Aucune liste à puces <ul><li> — uniquement <p>, tableaux et accordéons
- Chaque section doit apporter une valeur distincte, pas de répétition\
""",

    "prix-gouttieres": """\
Génère un bloc de contenu HTML COMPLET et RICHE pour la page "prix gouttières à {ville}" ({region}, Québec).
Population : {population} habitants.

Contexte régional réel : {context}

Prix locaux fournis (utilise ces données dans le contenu) :
- Installation gouttières aluminium (maison complète) : {service1_min}$ – {service1_max}$
- Installation protège-gouttières (leaf guard, maison complète) : {service2_min}$ – {service2_max}$
- Nettoyage gouttières (1 passage complet) : {service3_min}$ – {service3_max}$
- Réparation gouttières (joints, sections, pentes) : {service4_min}$ – {service4_max}$

STRUCTURE OBLIGATOIRE — génère ces 6 sections dans l'ordre exact :

---
SECTION 1 — Tableau comparatif des types de travaux de gouttières à {ville}
<h2 class="text-3xl font-bold mb-4">[Titre accrocheur sur les gouttières à {ville} — ex: "Gouttières à {ville} : installation, nettoyage ou protège-gouttières — quel projet vous faut-il ?"]</h2>
Suivi d'un <p> de 180-220 mots sur les gouttières dans {region} : impact du climat de {region} sur les gouttières (accumulation de neige et glace, cycles gel-dégel, feuillage dense en automne), types de problèmes fréquents (bouchons, décrochements, gouttières rouillées ou percées), différence entre nettoyage préventif et remplacement, âge moyen du parc immobilier dans {region} et conséquences sur l'état des gouttières, pourquoi les protège-gouttières gagnent en popularité dans {region}.
Suivi d'un tableau HTML COMPLET : Type de travaux | Prix à {ville} | Durée | Matériaux | Garantie typique | Urgence disponible
Lignes : Installation aluminium / Installation protège-gouttières / Nettoyage complet / Réparation joints/sections / Remplacement partiel / Fascias et soffites
Classes tableau : <table class="w-full text-sm border-collapse mt-6 mb-2"> <thead style="background:#0369a1;color:#fff"> <th class="px-4 py-3 text-left font-semibold"> <tbody> <tr class="border-b border-gray-200 hover:bg-gray-50"> <td class="px-4 py-3">

---
SECTION 2 — Facteurs qui font varier le prix des gouttières à {ville}
<h2> accrocheur ancré dans {ville} ou {region}
<p> de 180-220 mots : longueur totale de gouttières (pi linéaires — maison standard vs grande maison dans {region}), nombre d'étages (accès en hauteur = prime de difficulté à {ville}), présence d'arbres à proximité (feuilles, graines de samare — impact direct sur fréquence de nettoyage dans {region}), état des fascias sous-jacents (fascias pourris = coût supplémentaire de remplacement), choix du matériau (aluminium standard vs calibre renforcé vs acier galvanisé vs vinyle), type de protège-gouttières choisi (grilles perforées vs filtres en mousse vs micro-grille en acier inoxydable), descentes pluviales à remplacer simultanément, accessibilité du toit selon la pente et la configuration à {ville}. Pour les montants clés, utilise <strong class="text-sky-600">X $</strong>.
Suivi d'un tableau (thead style="background:#0369a1;color:#fff") : Facteur | Impact sur le prix | Détail pour {ville}
Lignes : Longueur totale (pi linéaires) / Nombre d'étages / Arbres à proximité / État des fascias / Choix du matériau / Type de protège-gouttières / Descentes pluviales / Accessibilité du toit

---
SECTION 3 — Aluminium, vinyle ou protège-gouttières : quel choix pour {ville} ?
<h2> original mentionnant {ville} ou {region}
<p> de 200-250 mots : ALUMINIUM (calibre 0.027) — standard dans {region}, durée de vie 20-30 ans, résistant aux cycles gel-dégel, disponible en gouttières continues de chantier (sans joints = sans fuites), coût installation {service1_min}$–{service1_max}$ à {ville}. VINYLE — moins coûteux à l'achat mais se fragilise avec le froid de {region}, joints qui bougent en hiver → fuites fréquentes, déconseillé pour les régions à -30°C. ACIER GALVANISÉ — très résistant mais plus lourd, tendance à rouiller après 15-20 ans, souvent utilisé pour les bâtiments commerciaux dans {region}. PROTÈGE-GOUTTIÈRES — investissement {service2_min}$–{service2_max}$ à {ville} mais élimine les nettoyages annuels (rentable en 5-7 ans dans {region} si arbres à proximité), types : grille (plus abordable, efficace contre les feuilles), filtre en mousse (retient trop d'humidité — non recommandé au Québec), micro-grille en acier inoxydable (premium, efficace même contre les petites graines d'érable). Mets les montants en <strong class="text-sky-600">X $</strong>.
Suivi d'un tableau (thead style="background:#0369a1;color:#fff") : Matériau | Durée de vie | Prix {ville} | Avantages | Inconvénients | Recommandé pour {region}
Lignes : Aluminium standard / Aluminium renforcé / Vinyle / Acier galvanisé / Cuivre / Protège-gouttières micro-grille

---
SECTION 4 — Nettoyage et entretien des gouttières à {ville}
<h2> pratique et local
<p> de 200-250 mots : fréquence recommandée à {ville} — 2 fois par an (printemps après la fonte des neiges, automne après la chute des feuilles), mais potentiellement 3-4 fois si arbres d'érable ou autres feuillus à proximité dans {region}. Signes d'urgence : débordement lors des pluies (gouttières bouchées), glaçons qui se forment en hiver (mauvaise circulation de l'eau), dégâts d'eau sur les fascias ou la fondation, gouttières qui penchent ou se décrochent. Coût nettoyage à {ville} : {service3_min}$–{service3_max}$ pour un passage complet. Ce qu'inclut un nettoyage professionnel : retrait des débris à la main ou au souffleur, rinçage à l'eau sous pression, vérification des joints et des pentes, inspection visuelle des fascias, rapport d'état. Pourquoi le bricolage est risqué : travail en hauteur, risque de chute, gouttières qui peuvent se déformer si on s'appuie dessus. Pour les montants, utilise <strong class="text-sky-600">X $</strong>.
Suivi d'un tableau (thead style="background:#0369a1;color:#fff") : Service | Fréquence | Prix {ville} | Ce qui est inclus | Délai typique {region}
Lignes : Nettoyage printemps / Nettoyage automne / Nettoyage d'urgence / Inspection complète / Dégivrage hiver / Nettoyage + inspection combinés

---
SECTION 5 — Choisir son entrepreneur gouttières à {ville}
<h2> pratique et local
<p> de 200-250 mots : licence RBQ requise pour les travaux de toiture et de gouttières à {ville} — vérifier la licence sur le site de la RBQ avant de signer. Assurance responsabilité civile minimale 2 M$ obligatoire pour tout entrepreneur travaillant en hauteur dans {region}. Ce que doit inclure une bonne soumission pour des gouttières à {ville} : mesure précise de la longueur totale (pi linéaires), description du matériau et du calibre, inclusion des descentes pluviales et des connecteurs, garantie sur la main-d'œuvre (5 ans minimum) et sur le matériau (20 ans pour aluminium), date de début et durée des travaux. Points d'attention dans {region} : méfiance envers les prix anormalement bas (aluminium de faible calibre, travail à la journée sans garantie), importance de comparer 3 soumissions à {ville}, vérifier les avis Google sur les entreprises de gouttières de {region}. Questions à poser : est-ce des gouttières continues de chantier ou des sections préfabriquées ? Les fascias sont-ils inspectés ? La garantie couvre-t-elle les fuites aux joints ?
Suivi d'un tableau (thead style="background:#0369a1;color:#fff") : Critère | Ce qu'il faut vérifier | Pourquoi c'est important
Lignes : Licence RBQ valide / Assurance responsabilité 2 M$ / Gouttières continues vs sections / Calibre de l'aluminium / Garantie main-d'œuvre / Inspection fascias incluse / Avis clients en ligne

---
SECTION 6 — FAQ : Gouttières à {ville}
<h2 class="text-3xl font-bold mb-8">Questions fréquentes sur les gouttières à {ville}</h2>
Génère 6 questions-réponses en accordéon HTML avec ces classes exactes :
<details class="group bg-white rounded-xl border border-gray-200 overflow-hidden mb-3">
<summary class="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50">
<span class="font-semibold text-gray-900 pr-4">QUESTION ICI</span>
<svg class="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
</summary>
<div class="px-6 pb-6 text-gray-600 leading-relaxed">RÉPONSE ICI (100-130 mots, précise, avec données locales)</div>
</details>

Questions à couvrir :
1. Combien coûte l'installation de gouttières à {ville} (utilise les prix fournis)
2. À quelle fréquence faut-il nettoyer ses gouttières à {ville}
3. Vaut-il mieux installer des protège-gouttières ou payer pour le nettoyage annuel à {ville}
4. Quelle est la durée de vie des gouttières aluminium dans le climat de {region}
5. Faut-il une licence RBQ pour installer des gouttières à {ville}
6. Comment savoir si mes gouttières sont à remplacer ou si une réparation suffit à {ville}

---

RÈGLES ABSOLUES :
- Réponds UNIQUEMENT avec le HTML brut, aucun commentaire avant ou après
- NE génère PAS de wrapper extérieur <div> ou <section> global — commence directement par le contenu des sections
- Pour le texte courant utilise text-gray-900 (titres/spans), text-gray-600 (corps FAQ) — pour les prix utilise <strong class="text-sky-600">X $</strong>
- Intègre les prix fournis directement dans les tableaux et le texte
- Mentionne {ville} et {region} naturellement dans chaque section
- Aucune liste à puces <ul><li> — uniquement <p>, tableaux et accordéons
- Chaque section doit apporter une valeur distincte, pas de répétition\
""",

    "cuisine": """\
Génère un bloc de contenu HTML COMPLET et RICHE pour la page "prix rénovation cuisine à {ville}" ({region}, Québec).
Population : {population} habitants.

Contexte régional réel : {context}

Prix locaux fournis (utilise ces données dans le contenu) :
- Réfection partielle (armoires & comptoir) : {service1_min}$ – {service1_max}$
- Rénovation complète clé en main : {service2_min}$ – {service2_max}$
- Cuisine haut de gamme (matériaux premium) : {service3_min}$ – {service3_max}$
- Comptoir granite/quartz / îlot / backsplash : {service4_min}$ – {service4_max}$

STRUCTURE OBLIGATOIRE — génère ces 7 sections dans l'ordre exact :

---
SECTION 1 — Tableau comparatif des niveaux de rénovation
<h2 class="text-3xl font-bold text-gray-900 mb-4">Niveaux de rénovation cuisine à {ville} : lequel vous convient ?</h2>
Suivi d'un <p> de 180-220 mots sur le marché de la rénovation cuisine dans {region} : âge du parc immobilier, proportion de cuisines vieillissantes, tendance à la cuisine ouverte et à l'îlot, impact sur la valeur de revente. Intègre les données du contexte régional.
Suivi d'un tableau HTML Tailwind COMPLET : Niveau | Prix à {ville} | Ce qui est inclus | Durée des travaux | Idéal pour | Retour sur valeur
Lignes : Réfection partielle / Rénovation complète / Cuisine haut de gamme / Remplacement armoires seulement / Comptoir + backsplash seulement / Îlot ajouté à l'existant
Classes tableau : <table class="w-full text-sm border-collapse mt-6 mb-2"> <thead class="bg-gray-900 text-white"> <th class="px-4 py-3 text-left font-semibold"> <tbody> <tr class="border-b border-gray-200 hover:bg-gray-50"> <td class="px-4 py-3">

---
SECTION 2 — Coût selon le format et la superficie de la cuisine à {ville}
<h2> accrocheur ancré dans {ville}
<p> de 180-220 mots : superficie typique des cuisines dans {region} (maisons unifamiliales vs condos vs duplex), impact de la configuration (cuisine fermée, semi-ouverte, ouverte sur le salon), coût additionnel pour abattre un mur porteur, dimensions typiques qui font varier le budget à {ville}.
Suivi d'un tableau : Configuration | Superficie typique | Budget réfection | Budget complet | Facteurs de coût spécifiques
Lignes : Cuisine fermée standard / Cuisine semi-ouverte / Cuisine ouverte (mur abattu) / Cuisine avec îlot central / Condo (espace restreint) / Maison ancestrale (contraintes structurelles)

---
SECTION 3 — Armoires et comptoirs : les matériaux et leurs prix à {ville}
<h2> original mentionnant {region} ou {ville}
<p> de 200-250 mots : comparatif des matériaux d'armoires les plus demandés dans {region} (laminé thermoplastique : économique et résistant, MDF peint : populaire milieu de gamme, bois massif : haut de gamme et durabilité). Pour les comptoirs : stratifié vs quartz vs granite vs bois — prix par pied linéaire, durabilité dans le contexte québécois (gel-dégel, humidité), tendances actuelles dans {region}. Quand vaut-il mieux choisir un matériau plutôt qu'un autre à {ville}.

---
SECTION 4 — Ce qui fait vraiment varier le prix à {ville}
<h2> direct et pratique
<p> de 200-250 mots : déplacement de plomberie (évier, lave-vaisselle), mise à niveau électrique (prise 240V, hotte), ventilation (conduit extérieur obligatoire), accès difficile en condo, mur porteur à abattre, finition du plancher, hauteur des plafonds (armoires jusqu'au plafond), customisation poignées et quincaillerie. Explique pourquoi deux cuisines de même superficie à {ville} peuvent avoir des écarts de prix importants.
Suivi d'un tableau facteurs : Facteur | Impact sur le prix | Détail
Lignes : Déplacement plomberie / Mise à niveau électrique / Abattre un mur porteur / Ventilation hotte extérieure / Armoires jusqu'au plafond / Plancher à refaire / Éclairage encastré / Quincaillerie premium

---
SECTION 5 — Tendances et styles populaires dans {region}
<h2> inspirant et ancré dans {region}
<p> de 180-220 mots : styles de cuisine les plus demandés dans {region} actuellement (cuisine ouverte, style shaker, contemporain épuré, rustique industriel), couleurs tendance (blanc, gris, vert sauge, noir mat), popularité des îlots multifonctions avec rangement et coin repas, importance du backsplash métro ou large format. Adapte au profil socio-économique et aux types de maisons dominants dans {region}. Donne des exemples concrets de ce que les propriétaires de {ville} commandent le plus souvent.

---
SECTION 6 — Comment choisir son entrepreneur cuisine à {ville}
<h2> rassurant et local
<p> de 200-250 mots : ce qu'un bon devis de rénovation cuisine doit obligatoirement inclure (marques exactes des armoires, dimensions précises, devis électricien et plombier séparés si requis, calendrier des travaux, conditions de paiement). Licence RBQ obligatoire (catégorie 1.2.1 ou sous-traitance), vérification des assurances, garantie de 1 an sur la main-d'œuvre. Pourquoi éviter les paiements en argent comptant et les entrepreneurs sans contrat écrit. Délais typiques à {ville} selon la saison (la haute saison printemps-été entraîne des délais de 6-12 semaines dans plusieurs régions du Québec).
Suivi d'un tableau : Critère | Ce qu'il faut vérifier | Pourquoi c'est important
Lignes : Licence RBQ / Assurance RC / Devis détaillé avec marques / Garantie main-d'œuvre / Acompte demandé / Sous-traitants déclarés / Référence de projets similaires

---
SECTION 7 — FAQ : Rénovation cuisine à {ville}
<h2 class="text-3xl font-bold text-gray-900 mb-8">Questions fréquentes sur la rénovation cuisine à {ville}</h2>
Génère 6 questions-réponses en accordéon HTML avec ces classes exactes :
<details class="group bg-white rounded-xl border border-gray-200 overflow-hidden mb-3">
<summary class="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50">
<span class="font-semibold text-gray-900 pr-4">QUESTION ICI</span>
<svg class="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
</summary>
<div class="px-6 pb-6 text-gray-600 leading-relaxed">RÉPONSE ICI (80-120 mots, précise, avec données locales)</div>
</details>

Questions à couvrir :
1. Combien coûte une rénovation cuisine complète à {ville} (utilise les prix fournis)
2. Quelle est la différence entre une réfection partielle et une rénovation complète à {ville}
3. Quels matériaux d'armoires sont les plus populaires dans {region} et pourquoi
4. Peut-on rénover sa cuisine en habitant dans la maison à {ville}
5. Combien de temps dure une rénovation cuisine complète à {ville}
6. Faut-il un permis de construction pour rénover sa cuisine à {ville}

---

RÈGLES ABSOLUES :
- Réponds UNIQUEMENT avec le HTML brut, aucun commentaire avant ou après
- NE génère PAS de wrapper extérieur <div> ou <section> global — commence directement par le contenu des sections
- Utilise les classes Tailwind déjà définies dans le site (text-gray-900, text-gray-600, font-bold, etc.)
- Intègre les prix fournis directement dans les tableaux et le texte
- Mentionne {ville} et {region} naturellement dans chaque section
- Aucune liste à puces <ul><li> — uniquement <p>, tableaux et accordéons
- Chaque section doit apporter une valeur distincte, pas de répétition\
""",
    "ceramique": """\
Génère un bloc de contenu HTML COMPLET et RICHE pour la page "prix céramique à {ville}" ({region}, Québec).
Population : {population} habitants.

Contexte régional réel : {context}

Prix locaux fournis (utilise ces données dans le contenu) :
- Plancher en céramique (pose complète) : {service1_min}$ – {service1_max}$
- Réfection salle de bain (douche + bain + murs) : {service2_min}$ – {service2_max}$
- Dosseret de cuisine (métro, mosaïque, grand format) : {service3_min}$ – {service3_max}$
- Terrasse ou patio extérieur en céramique : {service4_min}$ – {service4_max}$

STRUCTURE OBLIGATOIRE — génère ces 6 sections dans l'ordre exact :

---
SECTION 1 — Tableau comparatif des types de pose et prix à {ville}
<h2 class="text-3xl font-bold text-gray-900 mb-4">Types de céramique à {ville} : formats, prix et applications</h2>
Suivi d'un <p> de 180-220 mots sur le marché de la céramique dans {region} : parc immobilier, âge des salles de bain, tendance grand format, part des projets plancher vs salle de bain vs cuisine, impact de la céramique sur la valeur de revente. Intègre les données du contexte régional.
Suivi d'un tableau HTML Tailwind COMPLET : Type de projet | Prix à {ville} | Format recommandé | Durée des travaux | Idéal pour | Notes
Lignes : Plancher salon/cuisine / Salle de bain complète / Douche à l'italienne / Dosseret cuisine / Terrasse extérieure / Escalier céramique
Classes tableau : <table class="w-full text-sm border-collapse mt-6 mb-2"> <thead class="bg-gray-900 text-white"> <th class="px-4 py-3 text-left font-semibold"> <tbody> <tr class="border-b border-gray-200 hover:bg-gray-50"> <td class="px-4 py-3">

---
SECTION 2 — Formats et matériaux : céramique, porcelaine, pierre naturelle à {ville}
<h2> accrocheur ancré dans {ville}
<p> de 180-220 mots : comparatif des matériaux — céramique standard (économique, intérieur léger), porcelaine rectifiée (plus dense, forte circulation, espaces humides), pierre naturelle (marbre, travertin — luxueux mais entretien), grès cérame grand format (tendance 2024-2025 dans {region}). Pour les formats : mosaïque 2×2 (douche, courbes), métro 3×6 (dosserets, salles de bain), grand format 24×24 ou 12×24 (planchers ouverts, moins de joints). Tendances actuelles dans {region} et ce que les propriétaires de {ville} commandent le plus souvent.
Suivi d'un tableau : Matériau | Prix pose incluse à {ville} | Résistance | Entretien | Applications recommandées

---
SECTION 3 — Ce qui fait vraiment varier le prix à {ville}
<h2> direct et pratique
<p> de 200-250 mots : préparation du sous-plancher (dépose de l'ancien revêtement, ragréage, membrane Schluter Ditra), format de la tuile (grand format = plus lent à poser, joints serrés), type de pose (droite, diagonale, chevron — +15-25% main d'œuvre), sous-plancher flexible (bois) vs béton, dénivelé, accès difficile (condo, escalier). Explique pourquoi deux projets de même superficie à {ville} peuvent avoir des écarts de prix importants.
Suivi d'un tableau facteurs : Facteur | Impact sur le prix | Détail
Lignes : Dépose ancien revêtement / Membrane découplée Ditra / Pose diagonale ou chevron / Grand format 24×24+ / Sous-plancher en bois / Douche à l'italienne (drain linéaire) / Joints époxy / Inégalités importantes

---
SECTION 4 — Salle de bain et douche : guide céramique pour {ville}
<h2> inspirant ancré dans {region}
<p> de 200-250 mots : la salle de bain est le projet céramique le plus complexe à {ville} — combinaison de surfaces verticales (murs de douche, tablier de bain) et horizontales (plancher), imperméabilisation obligatoire derrière la douche (membrane Kerdi ou Red Guard), pente d'écoulement du plancher de douche (min. 2%), choix du drain (classique, linéaire, grille décorative). Format idéal pour les douches : mosaïque 2×2 sur le sol (adhérence), grand format 12×24 ou 24×24 sur les murs (effet épuré). Exemples de budgets typiques dans {region} selon la superficie.
Suivi d'un tableau : Projet salle de bain | Superficie typique | Budget à {ville} | Points d'attention
Lignes : Douche standard 3×3 / Douche italienne sans cloison / Réfection bain complet / Salle de bain complète (plancher + murs) / Petite salle d'eau (2 pièces)

---
SECTION 5 — Comment choisir son poseur de céramique à {ville}
<h2> rassurant et local
<p> de 200-250 mots : licence RBQ obligatoire (sous-catégorie carreleur), vérification des assurances RC, devis qui précise les marques de tuiles et coulis, épaisseur du lit de mortier, type de membrane, garantie main-d'œuvre minimale 1 an. Pourquoi éviter les carreleurs sans contrat écrit. Délais typiques à {ville} selon la saison. Questions à poser avant de signer : le poseur fournit-il les matériaux ou seulement la main-d'œuvre ? Inclut-il la dépose de l'existant ? La préparation du sous-plancher ?
Suivi d'un tableau : Critère | Ce qu'il faut vérifier | Pourquoi c'est important
Lignes : Licence RBQ / Assurance RC / Devis avec marques et références / Membrane imperméabilisation / Garantie pose / Dépose incluse / Préparation sous-plancher

---
SECTION 6 — FAQ : Céramique à {ville}
<h2 class="text-3xl font-bold text-gray-900 mb-8">Questions fréquentes sur la céramique à {ville}</h2>
Génère 6 questions-réponses en accordéon HTML avec ces classes exactes :
<details class="group bg-white rounded-xl border border-gray-200 overflow-hidden mb-3">
<summary class="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50">
<span class="font-semibold text-gray-900 pr-4">QUESTION ICI</span>
<svg class="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
</summary>
<div class="px-6 pb-6 text-gray-600 leading-relaxed">RÉPONSE ICI (80-120 mots, précise, avec données locales)</div>
</details>

Questions à couvrir :
1. Combien coûte la pose de céramique au pied carré à {ville} (utilise les prix fournis)
2. Quelle est la différence entre céramique et porcelaine — laquelle choisir à {ville}
3. Peut-on poser de la céramique par-dessus un ancien plancher à {ville}
4. Combien de temps prend la pose d'une salle de bain complète à {ville}
5. Faut-il une membrane imperméabilisante derrière la douche à {ville}
6. Quel format de tuile choisir pour agrandir visuellement une pièce à {ville}

---

RÈGLES ABSOLUES :
- Réponds UNIQUEMENT avec le HTML brut, aucun commentaire avant ou après
- NE génère PAS de wrapper extérieur <div> ou <section> global — commence directement par le contenu des sections
- Utilise les classes Tailwind déjà définies dans le site (text-gray-900, text-gray-600, font-bold, etc.)
- Intègre les prix fournis directement dans les tableaux et le texte
- Mentionne {ville} et {region} naturellement dans chaque section
- Aucune liste à puces <ul><li> — uniquement <p>, tableaux et accordéons
- Chaque section doit apporter une valeur distincte, pas de répétition\
""",
    "beton": """\
Génère un bloc de contenu HTML COMPLET et RICHE pour la page "prix béton à {ville}" ({region}, Québec).
Population : {population} habitants.

Contexte régional réel : {context}

Prix locaux fournis (utilise ces données dans le contenu) :
- Entrée de garage en béton (400-600 pi2) : {service1_min}$ – {service1_max}$
- Dalle de béton intérieure (sous-sol, garage, patio, 300-500 pi2) : {service2_min}$ – {service2_max}$
- Réparation béton (fissures, affaissement, scellement) : {service3_min}$ – {service3_max}$
- Fondation ou mur de fondation coulé : {service4_min}$ – {service4_max}$

STRUCTURE OBLIGATOIRE — génère ces 6 sections dans l'ordre exact :

---
SECTION 1 — Tableau comparatif des types de projets béton
<h2 class="text-3xl font-bold text-gray-900 mb-4">Prix béton à {ville} — Comparatif des projets 2026</h2>
Suivi d'un <p> de 180-220 mots sur le marché du béton dans {region} : impact du gel-dégel sur les entrées de garage et fondations, proportion de maisons avec entrée bétonnée, popularité du béton estampé vs uni, saison optimale pour couler à {ville}. Intègre les données du contexte régional.
Suivi d'un tableau HTML Tailwind COMPLET : Type de projet | Prix à {ville} | Superficie typique | Durée des travaux | Points clés
Lignes : Entrée de garage (uni) / Entrée de garage (estampée) / Dalle intérieure / Patio béton / Fondation / Mur de soutènement
Classes tableau : <table class="w-full text-sm border-collapse mt-6 mb-2"> <thead class="bg-gray-900 text-white"> <th class="px-4 py-3 text-left font-semibold"> <tbody> <tr class="border-b border-gray-200 hover:bg-gray-50"> <td class="px-4 py-3">

---
SECTION 2 — Ce qui fait vraiment varier le prix du béton à {ville}
<h2> direct et utile ancré dans {ville}
<p> de 200-250 mots : facteurs clés qui font varier le prix — superficie et forme (courbes = main-d'œuvre accrue), épaisseur de la dalle (4 po vs 6 po), excavation et remblai requis, armature (rebar vs fibres vs aucune), finition (lisse, balayée, estampée, colorée, scellée), accès au chantier, saison du coulage. Explique pourquoi deux entrées de même taille à {ville} peuvent avoir des écarts de prix importants.
Suivi d'un tableau facteurs : Facteur | Impact sur le prix | Détail
Lignes : Épaisseur (4 po vs 6 po) / Béton estampé vs uni / Armature rebar / Excavation et remblai / Finition scellée / Accès difficile / Saison (hiver vs été) / Forme irrégulière ou courbes

---
SECTION 3 — Gel-dégel et durabilité du béton dans {region}
<h2> original intégrant une donnée climatique réelle de {region}
<p> de 200-250 mots : le gel-dégel québécois est le principal ennemi du béton — cycles annuels dans {region}, profondeur hors-gel obligatoire pour les fondations, importance de l'agent entraîneur d'air dans le mélange, rapport eau/ciment optimal pour résister au sel de déglaçage, entretien préventif (scellant aux 3-5 ans, éviter le sel de table). Durée de vie réaliste d'une entrée bien vs mal exécutée dans les conditions de {region}. Différence entre béton résidentiel et béton commercial en termes de résistance MPa.

---
SECTION 4 — Béton estampé vs dalle standard : guide pour {ville}
<h2> inspirant ancré dans {region}
<p> de 200-250 mots : comparatif complet — béton estampé (motifs pierre, brique, bois, ardoise — 1.5x à 2x le prix du standard), béton coloré intégral vs colorant de surface, béton poli pour intérieur, béton lavé pour terrasses antidérapantes. Ce que chaque option donne comme résultat visuel et pratique dans une entrée de maison typique à {ville}. ROI de l'estampé sur la valeur de revente selon le marché immobilier de {region}.
Suivi d'un tableau : Type de finition | Prix à {ville} | Apparence | Entretien | Durée de vie
Lignes : Dalle unie lissée / Dalle balayée / Béton coloré intégral / Béton estampé motif pierre / Béton estampé motif brique / Béton poli intérieur

---
SECTION 5 — Comment choisir son entrepreneur béton à {ville}
<h2> rassurant et pratique
<p> de 200-250 mots : licence RBQ obligatoire (sous-catégorie maçonnerie-béton), vérification des assurances RC et cautionnement, devis qui précise la résistance MPa du béton commandé, l'épaisseur, le type d'armature, la finition et la garantie. Pourquoi éviter un entrepreneur qui ne fournit pas de permis ou qui sous-traite le coulage sans supervision. Délais typiques à {ville} en haute saison. Questions à poser avant de signer : inclut-il l'excavation ? Le compactage du gravier de base ? L'enlèvement des déchets ? Le scellant de première couche ?
Suivi d'un tableau : Critère | Ce qu'il faut vérifier | Pourquoi c'est important
Lignes : Licence RBQ / Assurance RC / Résistance MPa spécifiée / Épaisseur garantie / Armature incluse / Permis municipal / Garantie main-d'œuvre

---
SECTION 6 — FAQ : Béton à {ville}
<h2 class="text-3xl font-bold text-gray-900 mb-8">Questions fréquentes sur le béton à {ville}</h2>
Génère 6 questions-réponses en accordéon HTML avec ces classes exactes :
<details class="group bg-white rounded-xl border border-gray-200 overflow-hidden mb-3">
<summary class="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50">
<span class="font-semibold text-gray-900 pr-4">QUESTION ICI</span>
<svg class="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
</summary>
<div class="px-6 pb-6 text-gray-600 leading-relaxed">RÉPONSE ICI (80-120 mots, précise, avec données locales)</div>
</details>

Questions à couvrir :
1. Combien coûte une entrée de garage en béton à {ville} (utilise les prix fournis)
2. Quelle est la différence de prix entre béton estampé et béton standard à {ville}
3. Faut-il un permis pour couler une dalle de béton à {ville}
4. Quelle épaisseur de béton pour une entrée de garage au Québec
5. Quand peut-on couler du béton à {ville} — saison optimale
6. Combien de temps dure un béton bien coulé dans le climat de {region}

---

RÈGLES ABSOLUES :
- Réponds UNIQUEMENT avec le HTML brut, aucun commentaire avant ou après
- NE génère PAS de wrapper extérieur <div> ou <section> global — commence directement par le contenu des sections
- Utilise les classes Tailwind déjà définies dans le site (text-gray-900, text-gray-600, font-bold, etc.)
- Intègre les prix fournis ({service1_min}$–{service1_max}$, etc.) directement dans les tableaux et le texte
- Mentionne {ville} et {region} naturellement dans chaque section
- Aucune liste à puces <ul><li> — uniquement <p>, tableaux et accordéons
- Chaque section doit apporter une valeur distincte, pas de répétition\
""",
    "toiture-plate": """\
Génère un bloc de contenu HTML COMPLET et RICHE pour la page "prix toiture plate à {ville}" ({region}, Québec).
Population : {population} habitants.

Contexte régional réel : {context}

Prix locaux fournis (utilise ces données dans le contenu) :
- Membrane élastomère bicouche (bungalow 1000-1500 pi2) : {service1_min}$ – {service1_max}$
- Membrane TPO ou EPDM (même surface) : {service2_min}$ – {service2_max}$
- Réparation partielle (fuite, bulle, décollement) : {service3_min}$ – {service3_max}$
- Inspection et entretien annuel : {service4_min}$ – {service4_max}$

STRUCTURE OBLIGATOIRE — génère ces 6 sections dans l'ordre exact :

---
SECTION 1 — Tableau comparatif des systèmes de toiture plate
<h2 class="text-3xl font-bold text-gray-900 mb-4">Comparatif des systèmes de toiture plate à {ville}</h2>
Suivi d'un <p> de 180-220 mots sur les enjeux de la toiture plate dans {region} : gel-dégel, charge de neige, drainage, types de bâtiments avec toit plat (bungalows, condos, plex). Intègre les données du contexte régional.
Suivi d'un tableau HTML Tailwind COMPLET : Système | Prix à {ville} | Durée de vie | Résistance gel-dégel | Garantie fabricant | Idéal pour
Lignes : Membrane élastomère bicouche (torchée) / Membrane élastomère bicouche (adhésive) / Membrane TPO (thermoplastique) / Membrane EPDM (caoutchouc) / Système bicouche APP / Toiture verte (végétalisée)
Classes tableau : <table class="w-full text-sm border-collapse mt-6 mb-2"> <thead class="bg-gray-900 text-white"> <th class="px-4 py-3 text-left font-semibold"> <tbody> <tr class="border-b border-gray-200 hover:bg-gray-50"> <td class="px-4 py-3">

---
SECTION 2 — Coût selon le type de bâtiment à {ville}
<h2> accrocheur ancré dans {ville}
<p> de 180-220 mots : superficie de toit plat typique selon le type de bâtiment à {ville}, impact de l'arrachage de l'ancienne membrane, ajout d'isolant rigide, drainage (drain de toit, gouttières), accès difficile — facteurs qui font varier le prix spécifiquement dans {region}.
Suivi d'un tableau : Type de bâtiment | Surface typique | Prix élastomère | Prix TPO/EPDM | Points d'attention
Lignes : Bungalow 1000 pi² / Bungalow 1500 pi² / Duplex ou triplex / Condo (portion unitaire) / Petite surface commerciale / Extension ou solarium

---
SECTION 3 — Gel-dégel, neige et durabilité : toiture plate dans {region}
<h2> original intégrant une donnée climatique réelle de {region}
<p> de 200-250 mots : le toit plat est particulièrement vulnérable dans le climat de {region} — cycles gel-dégel (nombre annuel dans {region}), charge de neige accumulée, drainage insuffisant sous la neige, joints et solins sollicités par les mouvements thermiques. Ce qui distingue un système bien installé d'un qui lâchera en 5 ans. Durée de vie réaliste élastomère vs TPO dans les conditions de {region}. Importance de la pente de drainage (2% minimum).

---
SECTION 4 — Élastomère vs TPO vs EPDM : que choisir à {ville}
<h2> comparatif direct ancré dans {region}
<p> de 200-250 mots : comparaison concrète des trois systèmes pour un propriétaire de {ville} — élastomère bicouche (standard établi, torchée pour étanchéité maximale, coût moyen, réparable facilement), TPO (blanc réfléchissant, économies énergie été, soudure à chaud hermétique, garantie 20-30 ans), EPDM (caoutchouc souple, abordable, absorbe chaleur). Ce que les couvreurs de {region} recommandent le plus souvent. Cas où chaque système s'impose.
Suivi d'un tableau comparatif : Critère | Élastomère bicouche | TPO | EPDM
Lignes : Prix à {ville} / Durée de vie / Résistance UV / Entretien requis / Réparabilité / Garantie fabricant / Recommandé pour

---
SECTION 5 — Comment choisir son couvreur toit plat à {ville}
<h2> rassurant et pratique
<p> de 200-250 mots : licence RBQ spécifique toiture obligatoire, certifications fabricant (couvreur agréé Soprema, Firestone, IKO Commercial — nécessaire pour la garantie), assurance responsabilité civile, devis qui précise le système exact (marque, épaisseur en mm, type de pose), garantie main-d'œuvre séparée de la garantie fabricant. Délais typiques à {ville} en haute saison. Questions à poser avant de signer : le devis inclut-il l'arrachage ? L'isolant ? Les solins ? Le drain de toit ?
Suivi d'un tableau : Critère | Ce qu'il faut vérifier | Pourquoi c'est important
Lignes : Licence RBQ toiture / Certification fabricant / Assurance RC / Système spécifié (marque + mm) / Garantie main-d'œuvre / Arrachage et isolant inclus / Références toit plat

---
SECTION 6 — FAQ : Toiture plate à {ville}
<h2 class="text-3xl font-bold text-gray-900 mb-8">Questions fréquentes sur la toiture plate à {ville}</h2>
Génère 6 questions-réponses en accordéon HTML avec ces classes exactes :
<details class="group bg-white rounded-xl border border-gray-200 overflow-hidden mb-3">
<summary class="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50">
<span class="font-semibold text-gray-900 pr-4">QUESTION ICI</span>
<svg class="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
</summary>
<div class="px-6 pb-6 text-gray-600 leading-relaxed">RÉPONSE ICI (80-120 mots, précise, avec données locales)</div>
</details>

Questions à couvrir :
1. Combien coûte la réfection d'un toit plat à {ville} (utilise les prix fournis)
2. Élastomère ou TPO : lequel choisir pour un bungalow à {ville}
3. Quelle est la durée de vie réaliste d'un toit plat dans le climat de {region}
4. Comment détecter une fuite de toit plat avant qu'elle cause des dommages à {ville}
5. Peut-on réparer plutôt que refaire entièrement un toit plat à {ville}
6. Quel entretien faut-il faire sur un toit plat à {ville}

---

RÈGLES ABSOLUES :
- Réponds UNIQUEMENT avec le HTML brut, aucun commentaire avant ou après
- NE génère PAS de wrapper extérieur <div> ou <section> global — commence directement par le contenu des sections
- Utilise les classes Tailwind déjà définies dans le site (text-gray-900, text-gray-600, font-bold, etc.)
- Intègre les prix fournis ({service1_min}$–{service1_max}$, etc.) directement dans les tableaux et le texte
- Mentionne {ville} et {region} naturellement dans chaque section
- Aucune liste à puces <ul><li> — uniquement <p>, tableaux et accordéons
- Chaque section doit apporter une valeur distincte, pas de répétition\
""",
    "salledebain": """\
Génère un bloc de contenu HTML COMPLET et RICHE pour la page "prix rénovation salle de bain à {ville}" ({region}, Québec).
Population : {population} habitants.

Contexte régional réel : {context}

Prix locaux fournis (utilise ces données dans le contenu) :
- Rénovation partielle (douche ou baignoire, carrelage et accessoires) : {service1_min}$ – {service1_max}$
- Réfection complète de salle de bain (clé en main) : {service2_min}$ – {service2_max}$
- Salle de bain luxe (bain autoportant, douche italienne, matériaux haut de gamme) : {service3_min}$ – {service3_max}$
- Carrelage seul (plancher ou mur, pose + matériaux) : {service4_min}$ – {service4_max}$

STRUCTURE OBLIGATOIRE — génère ces 6 sections dans l'ordre exact :

---
SECTION 1 — Tableau comparatif des niveaux de rénovation à {ville}
<h2 class="text-3xl font-bold text-gray-900 mb-4">Niveaux de rénovation salle de bain à {ville} : quel projet vous correspond ?</h2>
Suivi d'un <p> de 180-220 mots sur le marché de la rénovation salle de bain dans {region} : âge du parc immobilier, proportion de salles de bain vieillissantes, popularité de la douche italienne vs baignoire, impact sur la valeur de revente. Intègre les données du contexte régional.
Suivi d'un tableau HTML Tailwind COMPLET : Niveau | Prix à {ville} | Ce qui est inclus | Durée des travaux | Idéal pour | Retour sur valeur
Lignes : Rénovation partielle (douche ou bain) / Réfection complète clé en main / Salle de bain luxe / Remplacement carrelage seulement / Changement vanité + miroir / Douche italienne ajoutée
Classes tableau : <table class="w-full text-sm border-collapse mt-6 mb-2"> <thead class="bg-gray-900 text-white"> <th class="px-4 py-3 text-left font-semibold"> <tbody> <tr class="border-b border-gray-200 hover:bg-gray-50"> <td class="px-4 py-3">

---
SECTION 2 — Coût selon le type de propriété et la superficie à {ville}
<h2> accrocheur ancré dans {ville}
<p> de 180-220 mots : superficie typique des salles de bain dans {region} (maisons unifamiliales vs condos vs duplex), impact de l'accessibilité en condo (règlements de copropriété, bruit, heures de travaux), coût additionnel pour déplacer la plomberie, superficies qui font varier le budget à {ville}.
Suivi d'un tableau : Type de propriété | Superficie typique | Budget partiel | Budget complet | Points d'attention
Lignes : Maison unifamiliale standard / Condo (accès restreint) / Duplex ou triplex / Maison ancestrale / Salle de bain principale (grande) / Salle de bain d'invités (petite)

---
SECTION 3 — Matériaux et tendances populaires dans {region}
<h2> original mentionnant {region} ou {ville}
<p> de 200-250 mots : carrelage grand format vs mosaïque vs LVT vinyle de luxe — comparatif prix par pi² incluant la pose dans {region}, popularité des douches sans rebord avec vitre semi-frameless, couleurs tendance dans {region} (blanc brillant, gris ardoise, vert sauge, terrazzo), vanités flottantes vs sur pied, robinetterie noire mate vs or brossé. Ce que les propriétaires de {ville} commandent le plus souvent. Impact du choix des matériaux sur le budget total.
Suivi d'un tableau : Matériau | Prix posé à {ville} | Durabilité | Entretien | Tendance dans {region}
Lignes : Carrelage céramique standard / Carrelage grand format (>24po) / Mosaïque / Vinyle de luxe (LVT) / Pierre naturelle / Béton ciré

---
SECTION 4 — Plomberie, électricité et imperméabilisation : ce qui fait varier le prix à {ville}
<h2> direct et pratique
<p> de 200-250 mots : déplacement de plomberie (coût maître plombier CMMTQ sous-traitant à {ville}), mise à niveau électrique (GFCI obligatoire, ventilateur, lumières encastrées), imperméabilisation obligatoire (membrane Schluter-Kerdi, Ditra — coût supplémentaire souvent sous-estimé), surcoût en condo (règlements, heures permises, accès restreint), plancher chauffant sous carrelage (populaire dans {region}). Pourquoi deux salles de bain de même superficie à {ville} peuvent avoir des écarts de prix de {service2_min}$ à {service2_max}$.
Suivi d'un tableau : Facteur | Impact sur le prix | Obligatoire à {ville}
Lignes : Déplacement plomberie / GFCI et électricité / Membrane imperméabilisante / Plancher chauffant / Ventilateur / Accès condo / Bain autoportant (structure)

---
SECTION 5 — Choisir son entrepreneur salle de bain à {ville}
<h2> rassurant et local
<p> de 200-250 mots : entrepreneur général RBQ licencié (catégorie rénovation résidentielle), plombier sous-traitant CMMTQ obligatoire pour tout déplacement de plomberie à {ville}, vérification des assurances RC, devis qui détaille exactement les matériaux (marques, dimensions, quantités), garantie de 1 an main-d'œuvre minimale. Délais typiques à {ville} selon la saison (la haute saison printemps-été entraîne des délais de 6-12 semaines dans {region}). Questions à poser avant de signer : le devis inclut-il l'imperméabilisation ? L'enlèvement des vieux matériaux ? Les permis ?
Suivi d'un tableau : Critère | Ce qu'il faut vérifier | Pourquoi c'est important
Lignes : Licence RBQ rénovation / Plombier CMMTQ / Assurance RC / Devis détaillé matériaux / Garantie main-d'œuvre / Permis inclus / Références salle de bain

---
SECTION 6 — FAQ : Rénovation salle de bain à {ville}
<h2 class="text-3xl font-bold text-gray-900 mb-8">Questions fréquentes sur la rénovation salle de bain à {ville}</h2>
Génère 6 questions-réponses en accordéon HTML avec ces classes exactes :
<details class="group bg-white rounded-xl border border-gray-200 overflow-hidden mb-3">
<summary class="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50">
<span class="font-semibold text-gray-900 pr-4">QUESTION ICI</span>
<svg class="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
</summary>
<div class="px-6 pb-6 text-gray-600 leading-relaxed">RÉPONSE ICI (80-120 mots, précise, avec données locales)</div>
</details>

Questions à couvrir :
1. Combien coûte une rénovation salle de bain complète à {ville} (utilise les prix fournis)
2. Quelle est la différence entre une rénovation partielle et une réfection complète à {ville}
3. Faut-il un permis pour rénover sa salle de bain à {ville}
4. Peut-on rénover sa salle de bain en habitant dans la maison à {ville}
5. Combien de temps dure une rénovation salle de bain complète à {ville}
6. Douche italienne ou baignoire : que choisir pour une salle de bain à {ville}

---

RÈGLES ABSOLUES :
- Réponds UNIQUEMENT avec le HTML brut, aucun commentaire avant ou après
- NE génère PAS de wrapper extérieur <div> ou <section> global — commence directement par le contenu des sections
- Utilise les classes Tailwind déjà définies dans le site (text-gray-900, text-gray-600, font-bold, etc.)
- Intègre les prix fournis directement dans les tableaux et le texte
- Mentionne {ville} et {region} naturellement dans chaque section
- Aucune liste à puces <ul><li> — uniquement <p>, tableaux et accordéons
- Chaque section doit apporter une valeur distincte, pas de répétition\
""",

    "paysagement": """\
Génère un bloc de contenu HTML COMPLET et RICHE pour la page "aménagement paysager à {ville}" ({region}, Québec).
Population : {population} habitants.

Contexte régional réel : {context}

Prix locaux fournis (utilise ces données dans le contenu) :
- Aménagement paysager complet (terrain résidentiel standard) : {service1_min}$ – {service1_max}$
- Gazon en plaques installé (préparation + pose) : {service2_min}$ – {service2_max}$
- Terrasse en bois traité ou composite (20-40 m²) : {service3_min}$ – {service3_max}$
- Projet haut de gamme (piscine, pergola, murets naturels) : {service4_min}$ – {service4_max}$

STRUCTURE OBLIGATOIRE — génère ces 6 sections dans l'ordre exact :

---
SECTION 1 — Tableau comparatif des types de projets de paysagement à {ville}
<h2 class="text-3xl font-bold mb-4">[Titre accrocheur sur le paysagement à {ville} — ex: "Gazon, terrasse ou aménagement complet : quel projet pour votre terrain à {ville} ?"]</h2>
Suivi d'un <p> de 180-220 mots sur le marché du paysagement dans {region} : types de propriétés et de terrains dominants dans {region} (superficie typique, sol, végétation locale), saisonnalité courte mais intense (fenêtre avril-octobre), pourquoi les propriétaires de {region} investissent dans le paysagement (valeur de revente, plaisir de vivre, économies sur entretien gazon), végétaux recommandés pour le climat de {region} (vivaces robustes, arbustes indigènes résistants aux hivers). Intègre les données chiffrées du contexte régional.
Suivi d'un tableau HTML COMPLET : Type de projet | Prix à {ville} | Superficie typique | Durée des travaux | Inclus dans le prix | Durée de vie
Lignes : Aménagement complet / Gazon en plaques / Gazon ensemencé / Terrasse bois traité / Terrasse composite / Allée pavé uni / Pergola ou abri de jardin
Classes tableau : <table class="w-full text-sm border-collapse mt-6 mb-2"> <thead style="background:#059669;color:#fff"> <th class="px-4 py-3 text-left font-semibold"> <tbody> <tr class="border-b border-gray-200 hover:bg-gray-50"> <td class="px-4 py-3">

---
SECTION 2 — Facteurs qui font varier le prix d'un aménagement paysager à {ville}
<h2> accrocheur ancré dans {ville} ou {region}
<p> de 180-220 mots : superficie du terrain et impact direct sur le coût (prix au m² pour gazon, pour terrassement, pour terrasse dans {region}), type de sol (sol argileux = terrassement plus complexe dans {region}, roc affleurant = excavation coûteuse, sable = drainage facile mais peu de rétention), pente du terrain (travaux de nivellement ou murets de soutènement — surcoût important), distance du fournisseur de matériaux (gazon en plaques, pavés, bois traité — facteur important si {region} est éloignée des grands centres), qualité des végétaux et des matériaux choisis (gamme économique vs premium), entretien annuel inclus ou non dans le devis. Pour les montants clés, utilise <strong class="text-emerald-600">X $</strong>.
Suivi d'un tableau (thead style="background:#059669;color:#fff") : Facteur | Impact sur le prix | Détail pour {ville}
Lignes : Superficie du terrain / Type de sol de {region} / Pente et dénivelé / Distance fournisseurs / Qualité des matériaux / Végétaux (annuelles vs vivaces) / Entretien inclus

---
SECTION 3 — Gazon, pavé uni ou terrasse composite : que choisir à {ville} ?
<h2> original mentionnant {ville} ou {region}
<p> de 200-250 mots : GAZON EN PLAQUES — solution rapide (vert immédiatement), coût {service2_min}$–{service2_max}$ à {ville}, entretien annuel (taille, arrosage, fertilisation), durée de vie illimitée si bien entretenu, adapté aux hivers de {region} (gazon dormant en hiver mais résistant). GAZON ENSEMENCÉ — moins cher mais délai de 3-6 semaines avant utilisation, plus sensible à la sécheresse la première saison dans {region}. PLATE-BANDES ET VIVACES — investissement ponctuel avec rendement croissant, les vivaces adaptées au zone de rusticité de {region} (zones 3-5 selon la latitude) reviennent chaque année sans replanter. TERRASSE EN BOIS TRAITÉ vs COMPOSITE — bois traité {service3_min}$–{service3_max}$ à {ville} mais entretien annuel (teinture, nettoyage), composite plus cher à l'achat mais sans entretien (durée de vie 25-30 ans, idéal pour le climat humide de {region}). PAVÉ UNI — allées et patios durables, résistants aux cycles gel-dégel de {region} si fondation granulaire adéquate (10-12 po). Mets les montants en <strong class="text-emerald-600">X $</strong>.
Suivi d'un tableau (thead style="background:#059669;color:#fff") : Option | Prix {ville} | Durée de vie | Entretien annuel | Résistance hiver {region} | Meilleur pour
Lignes : Gazon en plaques / Gazon ensemencé / Plate-bandes vivaces / Terrasse bois traité / Terrasse composite / Pavé uni allée

---
SECTION 4 — Les étapes d'un projet de paysagement réussi à {ville}
<h2> pratique et motivant, ancré dans {ville}
<p> de 200-250 mots : les étapes dans l'ordre — (1) évaluation du terrain et diagnostic (sol, pente, exposition soleil-ombre, drainage existant), (2) plan d'aménagement (dessiner à l'échelle, identifier les zones gazon/terrasse/plate-bandes/allées), (3) demande de 3 soumissions auprès de paysagistes certifiés ASNQ dans {region}, (4) préparation du sol (nivellement, terrassement, amendement de sol si argileux dans {region}), (5) installation des éléments durs (terrasse, allée, murets) avant les éléments souples (gazon, végétaux), (6) plantation et ensemencement ou pose de gazon en plaques, (7) arrosage intensif les 3-4 premières semaines dans les conditions météo de {region}. Fenêtre optimale dans {region} : mai à début juillet pour les plantations (sols réchauffés, risque de gel passé) ou août-septembre pour le gazon (moins de stress hydrique). Mets les montants en <strong class="text-emerald-600">X $</strong>.
Suivi d'un tableau (thead style="background:#059669;color:#fff") : Étape | Durée typique | Coût estimé | Professionnel requis
Lignes : Plan d'aménagement / Terrassement et nivellement / Drainage / Installation terrasse ou allée / Préparation sol et amendement / Pose gazon ou plantation / Arrosage et établissement

---
SECTION 5 — Choisir son paysagiste à {ville}
<h2> pratique et local
<p> de 200-250 mots : paysagiste certifié ASNQ (Association des professionnels en horticulture du Québec) vs jardinier non certifié — la certification garantit des connaissances en horticulture, botanique et aménagement. Licence RBQ requise pour les travaux de construction (terrasses, murets, dalles — travaux de maçonnerie légère). Ce que doit inclure un bon devis de paysagement à {ville} : plan ou croquis d'aménagement, liste des végétaux avec noms latins (garantie de zone de rusticité pour {region}), dimension et essence du gazon en plaques, type de bois traité (classe de rétention UC4 pour contact sol dans {region}), garantie sur les végétaux (1 an standard) et sur les ouvrages (2-5 ans). Points d'attention : méfiance envers les prix trop bas (gazon de mauvaise qualité, mauvaise préparation du sol — le gazon ne tiendra pas le premier hiver de {region}), importance de voir des réalisations antérieures dans {region}. Délais typiques en haute saison (mai-juin — délais 4 à 10 semaines dans {region}).
Suivi d'un tableau (thead style="background:#059669;color:#fff") : Critère | Ce qu'il faut vérifier | Pourquoi c'est important
Lignes : Certification ASNQ / Licence RBQ (ouvrages) / Plan d'aménagement inclus / Noms de végétaux précis / Zone de rusticité adaptée / Garantie végétaux 1 an / Références locales {region}

---
SECTION 6 — FAQ : Aménagement paysager à {ville}
<h2 class="text-3xl font-bold mb-8">Questions fréquentes sur l'aménagement paysager à {ville}</h2>
Génère 6 questions-réponses en accordéon HTML avec ces classes exactes :
<details class="group bg-white rounded-xl border border-gray-200 overflow-hidden mb-3">
<summary class="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50">
<span class="font-semibold text-gray-900 pr-4">QUESTION ICI</span>
<svg class="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
</summary>
<div class="px-6 pb-6 text-gray-600 leading-relaxed">RÉPONSE ICI (100-130 mots, précise, avec données locales)</div>
</details>

Questions à couvrir :
1. Combien coûte un aménagement paysager complet à {ville} (utilise les prix fournis)
2. Quelle est la meilleure période pour aménager son terrain à {ville}
3. Gazon en plaques ou gazon ensemencé : que choisit-on le plus à {ville}
4. Faut-il un permis pour construire une terrasse ou un muret à {ville}
5. Quels végétaux résistent le mieux aux hivers de {region}
6. Comment entretenir son aménagement paysager pour l'hiver à {ville}

---

RÈGLES ABSOLUES :
- Réponds UNIQUEMENT avec le HTML brut, aucun commentaire avant ou après
- NE génère PAS de wrapper extérieur <div> ou <section> global — commence directement par le contenu des sections
- Pour le texte courant utilise text-gray-900 (titres/spans), text-gray-600 (corps FAQ) — pour les prix utilise <strong class="text-emerald-600">X $</strong>
- Intègre les prix fournis directement dans les tableaux et le texte
- Mentionne {ville} et {region} naturellement dans chaque section
- Aucune liste à puces <ul><li> — uniquement <p>, tableaux et accordéons
- Chaque section doit apporter une valeur distincte, pas de répétition\
""",

    "electricien": """\
Génère un bloc de contenu HTML COMPLET et RICHE pour la page "électricien à {ville}" ({region}, Québec).
Population : {population} habitants.

Contexte régional réel : {context}

Prix locaux fournis (utilise ces données dans le contenu) :
- Petits travaux électriques (prises, circuits, luminaires) : {service1_min}$ – {service1_max}$
- Mise aux normes et tableau électrique (100A → 200A) : {service2_min}$ – {service2_max}$
- Grande installation (câblage complet, rénovation majeure) : {service3_min}$ – {service3_max}$
- Urgence et dépannage électrique : {service4_min}$ – {service4_max}$

STRUCTURE OBLIGATOIRE — génère ces 6 sections dans l'ordre exact :

---
SECTION 1 — Tableau comparatif des types de travaux électriques à {ville}
<h2 class="text-3xl font-bold mb-4">[Titre accrocheur sur les travaux électriques à {ville} — ex: "Petits travaux, tableau électrique ou urgence : quel électricien à {ville} pour votre besoin ?"]</h2>
Suivi d'un <p> de 180-220 mots sur le marché électrique dans {region} : proportion de maisons construites avant 1990 avec panneaux vétustes (60A ou 100A — problème de sécurité et de capacité), exigences d'Hydro-Québec pour les raccordements, impact de la transition vers les thermopompes et les véhicules électriques (augmentation de la demande en puissance), types de travaux les plus fréquents dans {region} selon le contexte. Intègre les données chiffrées du contexte régional.
Suivi d'un tableau HTML COMPLET : Type de travaux | Prix à {ville} | Durée typique | Permis requis | Urgence disponible | Maître électricien requis
Lignes : Petits travaux (prises, luminaires) / Mise aux normes panneau 200A / Remplacement tableau électrique / Installation borne VE (niveau 2) / Câblage rénovation complète / Urgence électrique 24h/7j
Classes tableau : <table class="w-full text-sm border-collapse mt-6 mb-2"> <thead style="background:#ca8a04;color:#fff"> <th class="px-4 py-3 text-left font-semibold"> <tbody> <tr class="border-b border-gray-200 hover:bg-gray-50"> <td class="px-4 py-3">

---
SECTION 2 — Facteurs qui font varier le prix des travaux électriques à {ville}
<h2> accrocheur ancré dans {ville} ou {region}
<p> de 180-220 mots : état du panneau électrique existant (panneau à remplacer entièrement vs simple mise à niveau, breakers fédéral pacific ou zinsco = remplacement obligatoire), ancienneté du câblage dans les maisons de {region} (fil aluminium dans les constructions 1965-1980 — nécessite pigtails en cuivre), complexité d'accès (finitions derrière les murs, greniers, sous-sols non finis), nombre de circuits ajoutés, distance entre le panneau et les équipements (thermopompe, borne VE en garage ou extérieur), tarification des urgences (prime nuit et week-end dans {region}), coût des matériaux (panneaux Siemens, Square D ou Eaton, disjoncteurs AFCI/GFCI). Pour les montants clés, utilise <strong class="text-amber-600">X $</strong>.
Suivi d'un tableau (thead style="background:#ca8a04;color:#fff") : Facteur | Impact sur le prix | Détail pour {ville}
Lignes : État panneau actuel / Type de câblage (cuivre vs alu) / Accès au câblage / Nombre de circuits / Distance tableau-équipement / Urgence (nuit/week-end) / Permis Hydro-Québec

---
SECTION 3 — Mise aux normes électrique à {ville} : ce qu'il faut savoir
<h2> original mentionnant {ville} ou {region}
<p> de 200-250 mots : pourquoi un panneau 200A est devenu indispensable dans {region} — thermopompes (15-50A selon la puissance), borne VE niveau 2 (30-50A dédiés), laveuse-sécheuse électrique, cuisinière vitrocéramique ou induction, chauffe-eau électrique — un panneau 100A est souvent insuffisant pour tout alimenter dans une maison moderne de {region}. Critères de sécurité : le panneau fédéral pacific (Stab-lok) et les panneaux Zinsco sont reconnus comme défectueux et refusés par les assureurs dans {region} — leur présence dans une maison de {region} impose un remplacement immédiat. GFCI (disjoncteurs différentiels) obligatoires dans salles de bain, cuisine, garage, extérieur. AFCI obligatoires dans les chambres selon le CCÉ récent. Coût de la mise aux normes complète à {ville} : {service2_min}$–{service2_max}$. Mets les montants en <strong class="text-amber-600">X $</strong>.
Suivi d'un tableau (thead style="background:#ca8a04;color:#fff") : Situation | Obligatoire | Impact prix | Délai à {ville}
Lignes : Panneau 60A à remplacer / Panneau 100A insuffisant / Câblage aluminium 1965-1980 / Panneau Federal Pacific (Stab-lok) / Ajout thermopompe ou VE / GFCI cuisine et sdb / AFCI chambres (CCÉ)

---
SECTION 4 — Les étapes d'un projet électrique à {ville}
<h2> pratique et motivant, ancré dans {ville}
<p> de 200-250 mots : les étapes dans l'ordre — (1) évaluation de la capacité actuelle par un maître électricien licencié CMEQ (vérification charge totale, identification des déficiences), (2) soumission détaillée (matériaux précis, marques, nombre de circuits, permis inclus ou non), (3) demande de permis auprès d'Hydro-Québec et/ou de la municipalité si requis à {ville}, (4) coupure temporaire du courant pendant les travaux (planning selon les besoins du client), (5) travaux d'installation ou de mise aux normes, (6) inspection finale par un inspecteur d'Hydro-Québec ou municipal pour les travaux majeurs, (7) mise en service et test de tous les circuits. Délais typiques dans {region} pour un remplacement de panneau (1-2 jours), pour un câblage complet (1-2 semaines), pour une urgence (moins de 24h en zone urbaine, 1-3 jours en zone rurale de {region}). Mets les montants en <strong class="text-amber-600">X $</strong>.
Suivi d'un tableau (thead style="background:#ca8a04;color:#fff") : Étape | Durée typique | Ce qui est inclus | Intervenant
Lignes : Évaluation et soumission / Permis Hydro-Québec / Coupure et préparation / Installation ou mise aux normes / Test et mise en service / Inspection finale / Raccordement Hydro-Québec

---
SECTION 5 — Choisir son maître électricien à {ville}
<h2> pratique et local
<p> de 200-250 mots : maître électricien licencié CMEQ — vérifier le numéro de licence sur le site de la RBQ, distinction entre maître électricien (peut signer les permis, responsable du travail) et compagnon ou apprenti (travaille sous supervision d'un maître). Assurance responsabilité civile obligatoire minimale 2 M$. Ce que doit inclure une bonne soumission à {ville} : description des travaux avec marques des matériaux (panneau Siemens vs Square D, disjoncteurs AFCI vs standard), permis Hydro-Québec inclus ou non dans le prix, garantie main-d'oeuvre 1 an minimum. Points d'attention dans {region} : méfiance envers les entrepreneurs sans licence CMEQ (travaux électriques sans permis — problèmes d'assurance et de revente immobilière), prix anormalement bas (matériaux de mauvaise qualité, pas de permis, pas de garantie). Dans {region}, les maîtres électriciens sont souvent occupés 4-8 semaines à l'avance au printemps et à l'automne.
Suivi d'un tableau (thead style="background:#ca8a04;color:#fff") : Critère | Ce qu'il faut vérifier | Pourquoi c'est important
Lignes : Licence CMEQ valide / Assurance responsabilité 2 M$ / Permis inclus dans devis / Marques des matériaux / Garantie main-d'oeuvre / Référence locale à {ville} / Délai confirmé par écrit

---
SECTION 6 — FAQ : Électricien à {ville}
<h2 class="text-3xl font-bold mb-8">Questions fréquentes sur les travaux électriques à {ville}</h2>
Génère 6 questions-réponses en accordéon HTML avec ces classes exactes :
<details class="group bg-white rounded-xl border border-gray-200 overflow-hidden mb-3">
<summary class="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50">
<span class="font-semibold text-gray-900 pr-4">QUESTION ICI</span>
<svg class="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
</summary>
<div class="px-6 pb-6 text-gray-600 leading-relaxed">RÉPONSE ICI (100-130 mots, précise, avec données locales)</div>
</details>

Questions à couvrir :
1. Combien coûte une mise aux normes électrique à {ville} (utilise les prix fournis)
2. Mon panneau 100A est-il suffisant pour une thermopompe ou une borne VE à {ville}
3. À quel signe reconnaît-on un panneau électrique dangereux à {ville}
4. Faut-il un permis pour changer son panneau électrique à {ville}
5. Combien de temps dure le remplacement d'un tableau électrique à {ville}
6. Comment choisir un maître électricien fiable à {ville}

---

RÈGLES ABSOLUES :
- Réponds UNIQUEMENT avec le HTML brut, aucun commentaire avant ou après
- NE génère PAS de wrapper extérieur <div> ou <section> global — commence directement par le contenu des sections
- Pour le texte courant utilise text-gray-900 (titres/spans), text-gray-600 (corps FAQ) — pour les prix utilise <strong class="text-amber-600">X $</strong>
- Intègre les prix fournis directement dans les tableaux et le texte
- Mentionne {ville} et {region} naturellement dans chaque section
- Aucune liste à puces <ul><li> — uniquement <p>, tableaux et accordéons
- Chaque section doit apporter une valeur distincte, pas de répétition\
""",

    "portes-fenetres": """\
Génère un bloc de contenu HTML COMPLET et RICHE pour la page "remplacement fenêtres et portes à {ville}" ({region}, Québec).
Population : {population} habitants.

Contexte régional réel : {context}

Prix locaux fournis (utilise ces données dans le contenu) :
- Remplacement d'une fenêtre (PVC double vitrage, installation incluse) : {service1_min}$ – {service1_max}$
- Remplacement d'une porte extérieure (acier ou fibre de verre) : {service2_min}$ – {service2_max}$
- Porte-fenêtre coulissante ou patio : {service3_min}$ – {service3_max}$
- Maison complète (8-14 fenêtres + portes, projet global) : {service4_min}$ – {service4_max}$

STRUCTURE OBLIGATOIRE — génère ces 6 sections dans l'ordre exact :

---
SECTION 1 — Tableau comparatif des types de fenêtres et portes à {ville}
<h2 class="text-3xl font-bold mb-4">[Titre accrocheur sur les fenêtres et portes à {ville} — ex: "Fenêtres PVC, hybrides ou triple vitrage : lequel choisir pour le climat de {region} ?"]</h2>
Suivi d'un <p> de 180-220 mots sur les enjeux des fenêtres et portes dans {region} : proportion de maisons construites avant 1990 avec fenêtres en fin de vie, impact du froid de {region} sur les vitrages de mauvaise qualité (condensation, givre intérieur), cotes ÉnerGuide recommandées pour le climat de {region}, programmes d'aide disponibles (Rénoclimat, RCEE), délais d'approvisionnement typiques dans {region}. Intègre les données chiffrées du contexte régional.
Suivi d'un tableau HTML COMPLET : Type de produit | Prix à {ville} | Cote ER / Performance | Durée de vie | Subvention possible | Idéal pour
Lignes : Fenêtre PVC double vitrage / Fenêtre PVC triple vitrage / Fenêtre hybride bois-PVC / Porte d'entrée acier / Porte fibre de verre / Porte-fenêtre coulissante / Porte de patio à guillotine
Classes tableau : <table class="w-full text-sm border-collapse mt-6 mb-2"> <thead style="background:#2563eb;color:#fff"> <th class="px-4 py-3 text-left font-semibold"> <tbody> <tr class="border-b border-gray-200 hover:bg-gray-50"> <td class="px-4 py-3">

---
SECTION 2 — Facteurs qui font varier le prix des fenêtres à {ville}
<h2> accrocheur ancré dans {ville} ou {region}
<p> de 180-220 mots : taille et style de la fenêtre (fenêtre fixe plus économique vs guillotine ou battant, dimensions hors-standard = prix sur mesure), type de vitrage (double standard vs double haute performance Low-E vs triple vitrage — surcoût de 20-40% pour le triple mais retour sur investissement via économies de chauffage dans le froid de {region}), matériau du cadre (PVC standard vs hybride bois-PVC — surcoût de 30-60% mais look bois intérieur), nombre de fenêtres du projet (économie d'échelle pour une maison complète à {ville} : prix unitaire réduit), retrait des anciens cadres (suppression incluse ou non), type d'installation (rénovation = insertion dans le cadre existant vs remplacement complet cadre et maçonnerie), délais de commande dans {region}. Pour les montants clés, utilise <strong class="text-blue-600">X $</strong>.
Suivi d'un tableau (thead style="background:#2563eb;color:#fff") : Facteur | Impact sur le prix | Détail pour {ville}
Lignes : Type de vitrage (double vs triple) / Matériau du cadre / Taille hors-standard / Retrait ancien cadre / Type d'installation / Nombre de fenêtres / Porte d'entrée vs porte patio

---
SECTION 3 — Subventions et programmes d'aide à {ville}
<h2> original mentionnant {ville} ou {region}
<p> de 200-250 mots : RÉNOCLIMAT — programme provincial pour les propriétaires de {region} : montant disponible pour le remplacement de fenêtres et portes extérieures certifiées (cote ER minimale requise, audit énergétique préalable recommandé), conditions d'admissibilité (maison construite avant 1983 dans {region}), comment s'inscrire. RCEE FÉDÉRAL — crédit d'impôt remboursable 30% + prêt sans intérêt jusqu'à 40 000$ pour des rénovations écoénergétiques incluant les fenêtres dans {region}, conditions et cumul avec Rénoclimat. HYDRO-QUÉBEC LOGISVERT — programmes disponibles pour les fenêtres ENERGY STAR dans {region} si applicable. PROGRAMMES MUNICIPAUX — tout programme spécifique aux MRC de {region} pour l'efficacité énergétique. Total cumulable maximum pour un propriétaire typique de {ville}. Mets les montants en <strong class="text-blue-600">X $</strong>.
Suivi d'un tableau (thead style="background:#2563eb;color:#fff") : Programme | Montant disponible | Conditions | Cumulable avec
Lignes : Rénoclimat — fenêtres / Rénoclimat — portes extérieures / RCEE fédéral / Hydro-Québec LogisVert / Crédit d'impôt provincial / Programme municipal (si applicable)

---
SECTION 4 — Les étapes d'un remplacement de fenêtres à {ville}
<h2> pratique et motivant, ancré dans {ville}
<p> de 200-250 mots : les étapes dans l'ordre — (1) évaluation de l'état des fenêtres existantes (condensation persistante, courants d'air, condensation entre les vitres = scellant défaillant), (2) choix des produits avec un installateur certifié de {region} (essai des mécanismes, vérification des cotes ER pour les programmes d'aide), (3) commande et délais de fabrication (fenêtres fabriquées sur mesure — délais 4-12 semaines selon le fabricant et la saison dans {region}), (4) préparation de l'ouverture et retrait de l'ancien cadre, (5) pose du nouveau cadre avec mousse polyuréthane et calfeutrage, (6) finition intérieure et extérieure (cadrage, moulures), (7) test d'étanchéité et ajustement des mécanismes. Peut-on poser des fenêtres en hiver dans {region} ? Oui si la température est au-dessus de -5°C et les ouvertures sont protégées — mais la haute saison reste printemps-été. Mets les montants en <strong class="text-blue-600">X $</strong>.
Suivi d'un tableau (thead style="background:#2563eb;color:#fff") : Étape | Durée typique | Ce qui est inclus | Astuce pour {ville}
Lignes : Évaluation et choix / Commande et fabrication / Retrait ancienne fenêtre / Pose nouveau cadre / Isolation et calfeutrage / Finition intérieure / Vérification et ajustement

---
SECTION 5 — Choisir son installateur de fenêtres à {ville}
<h2> pratique et local
<p> de 200-250 mots : installateur certifié RBQ (licence 1.2.1 rénovation résidentielle) — vérification obligatoire sur le site de la RBQ avant de signer. Assurance responsabilité civile minimale 2 M$. Ce que doit inclure une bonne soumission à {ville} : marque et modèle exact de la fenêtre (cote ER spécifiée), type de vitrage (Low-E, argon), type de cadre, dimensions confirmées sur place, retrait de l'ancienne fenêtre inclus ou non, finitions incluses (cadrage intérieur, coupe-bise extérieur), garantie fabricant (10-25 ans selon les marques) et garantie main-d'oeuvre (2-5 ans). Points d'attention dans {region} : méfiance envers les soumissions sans inspection en personne ni mesure des ouvertures, fenêtres importées sans certification ÉnerGuide (inéligibles aux subventions de {region}), paiement intégral à l'avance refusé (acompte 30-50% normal). Dans {region}, les installateurs réputés sont souvent bookés 6-12 semaines à l'avance en haute saison.
Suivi d'un tableau (thead style="background:#2563eb;color:#fff") : Critère | Ce qu'il faut vérifier | Pourquoi c'est important
Lignes : Licence RBQ 1.2.1 / Assurance responsabilité 2 M$ / Cote ER spécifiée / Garantie fabricant / Garantie main-d'oeuvre / Retrait inclus / Finitions incluses

---
SECTION 6 — FAQ : Fenêtres et portes à {ville}
<h2 class="text-3xl font-bold mb-8">Questions fréquentes sur le remplacement de fenêtres à {ville}</h2>
Génère 6 questions-réponses en accordéon HTML avec ces classes exactes :
<details class="group bg-white rounded-xl border border-gray-200 overflow-hidden mb-3">
<summary class="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50">
<span class="font-semibold text-gray-900 pr-4">QUESTION ICI</span>
<svg class="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
</summary>
<div class="px-6 pb-6 text-gray-600 leading-relaxed">RÉPONSE ICI (100-130 mots, précise, avec données locales)</div>
</details>

Questions à couvrir :
1. Combien coûte le remplacement d'une fenêtre à {ville} (utilise les prix fournis)
2. Quelle subvention peut-on obtenir pour remplacer ses fenêtres à {ville}
3. Double ou triple vitrage : quel choix pour le climat de {region}
4. Combien de temps faut-il attendre entre la commande et l'installation à {ville}
5. Peut-on changer ses fenêtres en hiver à {ville}
6. Comment savoir si mes fenêtres sont à remplacer ou si un ajustement suffit à {ville}

---

RÈGLES ABSOLUES :
- Réponds UNIQUEMENT avec le HTML brut, aucun commentaire avant ou après
- NE génère PAS de wrapper extérieur <div> ou <section> global — commence directement par le contenu des sections
- Pour le texte courant utilise text-gray-900 (titres/spans), text-gray-600 (corps FAQ) — pour les prix utilise <strong class="text-blue-600">X $</strong>
- Intègre les prix fournis directement dans les tableaux et le texte
- Mentionne {ville} et {region} naturellement dans chaque section
- Aucune liste à puces <ul><li> — uniquement <p>, tableaux et accordéons
- Chaque section doit apporter une valeur distincte, pas de répétition\
""",

    "fosseseptique": """\
Génère un bloc de contenu HTML COMPLET et RICHE pour la page "fosse septique à {ville}" ({region}, Québec).
Population : {population} habitants.

Contexte régional réel : {context}

Prix locaux fournis (utilise ces données dans le contenu) :
- Installation fosse septique complète (fosse + champ d'épuration) : {service1_min}$ – {service1_max}$
- Remplacement fosse septique (échange fosse, champ existant conforme) : {service2_min}$ – {service2_max}$
- Vidange et pompage (entretien régulier) : {service3_min}$ – {service3_max}$
- Inspection, rapport de conformité et entretien : {service4_min}$ – {service4_max}$

STRUCTURE OBLIGATOIRE — génère ces 6 sections dans l'ordre exact :

---
SECTION 1 — Tableau comparatif des types de travaux de fosse septique à {ville}
<h2 class="text-3xl font-bold mb-4">[Titre accrocheur sur les fosses septiques à {ville} — ex: "Fosse septique à {ville} : installation, remplacement ou vidange — ce que vous devez savoir"]</h2>
Suivi d'un <p> de 180-220 mots sur les fosses septiques dans {region} : proportion de propriétés sans accès au réseau d'égout municipal dans {region} (en particulier les zones rurales et les chalets), âge du parc de systèmes septiques (les systèmes d'avant 1990 arrivent en fin de vie), obligations de conformité lors des ventes immobilières (Règlement Q-2 r.22), impact du sol et du climat de {region} sur la durée de vie des systèmes. Intègre les données chiffrées du contexte régional.
Suivi d'un tableau HTML COMPLET : Type de travaux | Prix à {ville} | Durée d'intervention | Permis requis | Garantie typique | Urgence possible
Lignes : Installation système complet / Remplacement fosse seulement / Remplacement champ d'épuration / Vidange et pompage / Inspection de conformité / Réparation d'urgence
Classes tableau : <table class="w-full text-sm border-collapse mt-6 mb-2"> <thead style="background:#0d9488;color:#fff"> <th class="px-4 py-3 text-left font-semibold"> <tbody> <tr class="border-b border-gray-200 hover:bg-gray-50"> <td class="px-4 py-3">

---
SECTION 2 — Facteurs qui font varier le prix d'une fosse septique à {ville}
<h2> accrocheur ancré dans {ville} ou {region}
<p> de 180-220 mots : nombre de chambres à coucher de la résidence (détermine la capacité de la fosse en litres — MELCCFP impose une fosse de 3 000 L minimum pour 3 chambres dans {region}), type de sol et perméabilité (sol argileux de {region} = surface de champ d'épuration plus grande, donc coût plus élevé, sol sablonneux = risque contamination nappe mais installation plus facile), profondeur de la nappe phréatique (systèmes surélevés nécessaires dans les zones basses de {region}), distance de la maison au champ d'épuration, accessibilité du terrain pour la machinerie d'excavation, type de fosse choisie (béton vs polyéthylène). Pour les montants clés, utilise <strong class="text-teal-600">X $</strong>.
Suivi d'un tableau (thead style="background:#0d9488;color:#fff") : Facteur | Impact sur le prix | Détail pour {ville}
Lignes : Nombre de chambres à coucher / Type de sol dans {region} / Nappe phréatique / Accès machinerie / Type de fosse (béton vs PÉ) / Système surélevé requis / Distance maison-champ

---
SECTION 3 — Réglementation fosse septique à {ville} : ce qu'il faut savoir
<h2> original mentionnant {ville} ou la MRC de {region}
<p> de 200-250 mots : RÈGLEMENT Q-2, R.22 — le Règlement sur l'évacuation et le traitement des eaux usées des résidences isolées (MELCCFP) régit toutes les installations septiques au Québec, y compris dans {region}. Les propriétaires de {region} doivent se conformer lors de toute modification, lors d'une vente immobilière (déclaration de conformité obligatoire depuis 2021) ou lors d'une constatation de non-conformité par l'inspecteur municipal. PROCESSUS D'INSTALLATION dans {region} : étude de caractérisation des sols (obligatoire — technicien agronome ou ingénieur civil), plan approuvé par la MRC ou la municipalité de {ville}, excavation et installation, inspection et délivrance du certificat de conformité. NON-CONFORMITÉ : le propriétaire de {region} dont le système est non conforme reçoit un avis municipal et a généralement 2 à 5 ans pour se mettre aux normes, sous peine d'amende. Impact sur la valeur de revente dans {region} : un système non conforme bloque souvent les transactions ou nécessite une retenue de prix. Mets les montants en <strong class="text-teal-600">X $</strong>.
Suivi d'un tableau (thead style="background:#0d9488;color:#fff") : Démarche | Délai typique à {ville} | Ce qu'il faut fournir | Coût estimé
Lignes : Étude de sol / Plan soumis à la MRC / Permis de construction / Excavation et installation / Inspection de conformité / Certificat final / Déclaration de conformité (vente)

---
SECTION 4 — Entretien et vidange : ce que tout propriétaire doit faire à {ville}
<h2> pratique et rassurant, ancré dans {ville}
<p> de 200-250 mots : fréquence de vidange recommandée par le MELCCFP — tous les 2 ans pour les résidences occupées à temps plein à {ville}, plus fréquente pour les chalets ou résidences secondaires de {region} utilisées intensivement en été. Signes qu'une vidange est urgente : reflux dans les drains de la maison, odeurs de sulfure d'hydrogène à l'intérieur ou dans la cour, zone humide ou décolorée au-dessus du champ d'épuration. Ce qu'un vidangeur professionnel fait lors d'une intervention à {ville} : pompage complet de la fosse (matières solides + liquides), nettoyage des filtres et cloisons, inspection visuelle de l'état de la fosse et du raccordement au champ, rapport écrit. Coût à {ville} : {service3_min}$–{service3_max}$ pour un passage standard. Pourquoi l'entretien régulier protège le champ d'épuration — éviter le colmatage prématuré qui force un remplacement à {service1_min}$+ dans {region}. Pour les montants, utilise <strong class="text-teal-600">X $</strong>.
Suivi d'un tableau (thead style="background:#0d9488;color:#fff") : Service d'entretien | Fréquence | Prix {ville} | Ce qui est inclus | Délai urgence {region}
Lignes : Vidange standard / Vidange + inspection complète / Nettoyage filtre sortie / Inspection rapport conformité / Traitement ajout bactéries / Vidange résidence secondaire

---
SECTION 5 — Choisir son entrepreneur en fosse septique à {ville}
<h2> pratique et local
<p> de 200-250 mots : entrepreneur certifié MAMH (Ministère des Affaires municipales et de l'Habitation) et RBQ — vérification obligatoire sur le site de la RBQ avant de signer un contrat à {ville}. Distinction entre l'installateur de système (excavation, pose, certification) et le vidangeur (pompage, entretien — licence MELCCFP). Ce que doit inclure une bonne soumission à {ville} : étude de sol incluse ou séparée (technicien agronome certifié), plan approuvé par la MRC de {region}, marque et modèle de la fosse (polyéthylène Polytite, Bio-Pak, béton préfabriqué), dimensionnement selon le nombre de chambres, superficie du champ d'épuration calculée selon le sol de {region}, permis inclus, garantie sur les travaux (2-5 ans). Méfiance dans {region} envers les entrepreneurs qui proposent d'installer sans étude de sol ou sans permis — risque de non-conformité immédiate lors de l'inspection. Délais typiques dans {region} : printemps et été (sol non gelé — fenêtre d'avril à novembre).
Suivi d'un tableau (thead style="background:#0d9488;color:#fff") : Critère | Ce qu'il faut vérifier | Pourquoi c'est important
Lignes : Licence MAMH + RBQ / Étude de sol incluse / Plan approuvé MRC / Marque et modèle fosse / Dimensionnement certifié / Garantie travaux / Rapport de conformité livré

---
SECTION 6 — FAQ : Fosse septique à {ville}
<h2 class="text-3xl font-bold mb-8">Questions fréquentes sur la fosse septique à {ville}</h2>
Génère 6 questions-réponses en accordéon HTML avec ces classes exactes :
<details class="group bg-white rounded-xl border border-gray-200 overflow-hidden mb-3">
<summary class="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50">
<span class="font-semibold text-gray-900 pr-4">QUESTION ICI</span>
<svg class="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
</summary>
<div class="px-6 pb-6 text-gray-600 leading-relaxed">RÉPONSE ICI (100-130 mots, précise, avec données locales)</div>
</details>

Questions à couvrir :
1. Combien coûte l'installation d'une fosse septique complète à {ville} (utilise les prix fournis)
2. À quelle fréquence faut-il vidanger sa fosse septique à {ville}
3. Mon système septique est non conforme — que dois-je faire à {ville}
4. Quelle fosse septique choisir selon le type de sol dans {region}
5. Faut-il un permis pour remplacer sa fosse septique à {ville}
6. Quels sont les signes qu'il faut remplacer sa fosse septique à {ville}

---

RÈGLES ABSOLUES :
- Réponds UNIQUEMENT avec le HTML brut, aucun commentaire avant ou après
- NE génère PAS de wrapper extérieur <div> ou <section> global — commence directement par le contenu des sections
- Pour le texte courant utilise text-gray-900 (titres/spans), text-gray-600 (corps FAQ) — pour les prix utilise <strong class="text-teal-600">X $</strong>
- Intègre les prix fournis directement dans les tableaux et le texte
- Mentionne {ville} et {region} naturellement dans chaque section
- Aucune liste à puces <ul><li> — uniquement <p>, tableaux et accordéons
- Chaque section doit apporter une valeur distincte, pas de répétition\
""",

    "nettoyage-conduits": """\
Génère un bloc de contenu HTML COMPLET et RICHE pour la page "nettoyage de conduits à {ville}" ({region}, Québec).
Population : {population} habitants.

Contexte régional réel : {context}

Prix locaux fournis (utilise ces données dans le contenu) :
- Nettoyage conduits de ventilation (maison complète) : {service1_min}$ – {service1_max}$
- Ramonage conduit de cheminée (nettoyage + inspection) : {service2_min}$ – {service2_max}$
- Nettoyage conduit de sécheuse (lint + conduit d'évacuation) : {service3_min}$ – {service3_max}$
- Inspection vidéo des conduits (caméra + rapport d'état) : {service4_min}$ – {service4_max}$

STRUCTURE OBLIGATOIRE — génère ces 6 sections dans l'ordre exact :

---
SECTION 1 — Tableau comparatif des services de nettoyage de conduits à {ville}
<h2 class="text-3xl font-bold mb-4">[Titre accrocheur sur le nettoyage de conduits à {ville} — ex: "Conduits de ventilation, cheminée ou sécheuse à {ville} : quand et pourquoi les nettoyer ?"]</h2>
Suivi d'un <p> de 180-220 mots sur les conduits dans {region} : proportion de maisons avec système de conduits (chauffage à air pulsé, thermopompe centrale), impact des longs hivers de {region} sur la qualité de l'air intérieur (maisons fermées 6-8 mois), végétation locale et pollens saisonniers qui s'accumulent dans les filtres et conduits, recommandation de nettoyage tous les 3-5 ans (plus souvent si animaux, rénovations ou dégâts d'eau). Intègre les données chiffrées du contexte régional.
Suivi d'un tableau HTML COMPLET : Type de service | Prix à {ville} | Durée | Fréquence recommandée | Certifié NADCA | Urgence possible
Lignes : Conduits de ventilation (maison) / Conduits de cheminée (ramonage) / Conduit de sécheuse / Inspection vidéo / Traitement antimicrobien / Échangeur d'air (VRC/ERV)
Classes tableau : <table class="w-full text-sm border-collapse mt-6 mb-2"> <thead style="background:#059669;color:#fff"> <th class="px-4 py-3 text-left font-semibold"> <tbody> <tr class="border-b border-gray-200 hover:bg-gray-50"> <td class="px-4 py-3">

---
SECTION 2 — Facteurs qui font varier le prix du nettoyage de conduits à {ville}
<h2> accrocheur ancré dans {ville} ou {region}
<p> de 180-220 mots : superficie de la maison et nombre de bouches d'air (impact direct sur le linéaire de conduits à nettoyer dans {region}), nombre d'étages et longueur des tronçons (conduits plus longs en maison 2 étages = travail plus complexe), état d'encrassement (nettoyage régulier vs première fois depuis 10+ ans), présence d'animaux domestiques (poils et squames = nettoyage plus intensif), rénovations récentes sans protection des conduits (poussière de plâtre et de bois accumulée), type de conduits (métal galvanisé = plus facile à nettoyer vs flexible en plastique = moins efficace), traitement antimicrobien optionnel (recommandé après dégâts d'eau ou moisissures dans {region}), déplacement en zone rurale éloignée de {region} (frais kilométriques). Pour les montants clés, utilise <strong class="text-green-600">X $</strong>.
Suivi d'un tableau (thead style="background:#059669;color:#fff") : Facteur | Impact sur le prix | Détail pour {ville}
Lignes : Superficie maison / Nombre de bouches d'air / Nombre d'étages / État d'encrassement / Animaux domestiques / Type de conduits / Traitement antimicrobien / Zone rurale éloignée

---
SECTION 3 — Conduits de ventilation, cheminée et sécheuse : les risques à {ville}
<h2> original mentionnant {ville} ou {region}
<p> de 200-250 mots : CONDUITS DE VENTILATION SALES dans {region} — accumulation de poussières, allergènes (acariens, pollens, squames), moisissures si humidité mal contrôlée dans les sous-sols de {region} (fréquent avec les hivers humides), perte d'efficacité du système de chauffage (conduits partiellement obstrués = surconsommation d'énergie). Délai après lequel un nettoyage professionnel est recommandé : 3-5 ans (ou après rénovation, infestation, dégâts d'eau). CONDUIT DE CHEMINÉE NON RAMONÉ — risque d'incendie de cheminée (créosote dans les foyers à bois, fréquents dans les résidences secondaires de {region}), accumulation de nids d'oiseaux ou d'écureuils qui bloquent le tirage, intoxication au CO2 si tirage insuffisant. CONDUIT DE SÉCHEUSE OBSTRUÉ — risque #1 d'incendie résidentiel aux États-Unis et au Canada (lint accumulé dans le conduit = combustible), sur-consommation d'énergie (cycle de séchage 30-50% plus long), détérioration prématurée de la sécheuse. Coût d'un nettoyage préventif à {ville} : {service3_min}$–{service3_max}$ vs remplacement d'une sécheuse. Mets les montants en <strong class="text-green-600">X $</strong>.
Suivi d'un tableau (thead style="background:#059669;color:#fff") : Problème | Risque | Symptômes visibles | Action recommandée | Prix {ville}
Lignes : Conduits ventilation obstrués / Moisissures dans conduits / Créosote cheminée (feu) / Nid dans cheminée / Conduit sécheuse bouché / Échangeur d'air encrassé

---
SECTION 4 — Ce que comprend un vrai nettoyage professionnel à {ville}
<h2> pratique et rassurant, ancré dans {ville}
<p> de 200-250 mots : distinction entre le vrai nettoyage certifié NADCA et les services low-cost — un nettoyage professionnel certifié à {ville} comprend : (1) inspection visuelle de tous les conduits et bouches d'air, (2) mise en dépression du système (aspirateur industriel HEPA branché sur le réseau), (3) brossage mécanique de chaque tronçon (brosses rotatives adaptées au diamètre des conduits), (4) nettoyage et désinfection de chaque bouche d'air, (5) nettoyage du serpentin de la fournaise ou de la chambre de refoulement, (6) inspection de l'échangeur de chaleur, (7) rapport d'état avec photos. Ce que le nettoyage low-cost fait à la place : souffleur manuel qui déplace la poussière sans l'extraire — résultat: poussière redistribuée dans la maison de {ville} 24h après le nettoyage. Durée typique pour une maison standard dans {region} : 2-4 heures selon la superficie. Mets les montants en <strong class="text-green-600">X $</strong>.
Suivi d'un tableau (thead style="background:#059669;color:#fff") : Étape | Certifié NADCA | Low-cost | Pourquoi ça compte pour {region}
Lignes : Mise en dépression système / Brossage mécanique conduits / Nettoyage bouches d'air / Nettoyage fournaise/serpentin / Inspection échangeur chaleur / Rapport avec photos / Traitement antimicrobien

---
SECTION 5 — Choisir son entreprise de nettoyage de conduits à {ville}
<h2> pratique et local
<p> de 200-250 mots : certification NADCA (National Air Duct Cleaners Association) — la référence nord-américaine pour le nettoyage de conduits, vérifiable sur le site NADCA.com. Entreprise certifiée NADCA à {ville} = techniciens formés, équipement professionnel (aspirateur HEPA mobile puissant, caméra d'inspection), assurance responsabilité civile. Ce que doit inclure un bon devis pour {ville} : nombre de bouches d'air incluses dans le prix, type d'équipement utilisé (mention HEPA obligatoire), traitement antimicrobien inclus ou optionnel (devis séparé), durée estimée de l'intervention, garantie de résultat. Points d'attention dans {region} : méfiance envers les prix anormalement bas (offre en dessous de {service1_min}$ pour une maison complète à {ville} = souffleur manuel non certifié), vérifier les avis Google, demander le certificat NADCA. Questions à poser : utilisez-vous une aspiration HEPA ? Quel est votre numéro de certification NADCA ? Le rapport est-il inclus ?
Suivi d'un tableau (thead style="background:#059669;color:#fff") : Critère | Ce qu'il faut vérifier | Pourquoi c'est important
Lignes : Certification NADCA / Équipement HEPA / Assurance responsabilité / Nombre de bouches incluses / Rapport d'état fourni / Traitement antimicrobien optionnel / Avis clients locaux {ville}

---
SECTION 6 — FAQ : Nettoyage de conduits à {ville}
<h2 class="text-3xl font-bold mb-8">Questions fréquentes sur le nettoyage de conduits à {ville}</h2>
Génère 6 questions-réponses en accordéon HTML avec ces classes exactes :
<details class="group bg-white rounded-xl border border-gray-200 overflow-hidden mb-3">
<summary class="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50">
<span class="font-semibold text-gray-900 pr-4">QUESTION ICI</span>
<svg class="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
</summary>
<div class="px-6 pb-6 text-gray-600 leading-relaxed">RÉPONSE ICI (100-130 mots, précise, avec données locales)</div>
</details>

Questions à couvrir :
1. Combien coûte un nettoyage de conduits complet à {ville} (utilise les prix fournis)
2. À quelle fréquence faut-il nettoyer ses conduits de ventilation à {ville}
3. Comment savoir si mes conduits ont besoin d'être nettoyés à {ville}
4. Le nettoyage de conduits est-il efficace pour réduire les allergies à {ville}
5. Faut-il nettoyer ses conduits dans une maison neuve à {ville}
6. Quelle est la différence entre un nettoyage certifié NADCA et un service low-cost à {ville}

---

RÈGLES ABSOLUES :
- Réponds UNIQUEMENT avec le HTML brut, aucun commentaire avant ou après
- NE génère PAS de wrapper extérieur <div> ou <section> global — commence directement par le contenu des sections
- Pour le texte courant utilise text-gray-900 (titres/spans), text-gray-600 (corps FAQ) — pour les prix utilise <strong class="text-green-600">X $</strong>
- Intègre les prix fournis directement dans les tableaux et le texte
- Mentionne {ville} et {region} naturellement dans chaque section
- Aucune liste à puces <ul><li> — uniquement <p>, tableaux et accordéons
- Chaque section doit apporter une valeur distincte, pas de répétition\
""",

    "calfeutrage": """\
Génère un bloc de contenu HTML COMPLET et RICHE pour la page "calfeutrage à {ville}" ({region}, Québec).
Population : {population} habitants.

Contexte régional réel : {context}

Prix locaux fournis (utilise ces données dans le contenu) :
- Calfeutrage complet maison (toutes fenêtres + portes extérieures) : {service1_min}$ – {service1_max}$
- Calfeutrage fenêtres et portes seulement (8-12 ouvertures) : {service2_min}$ – {service2_max}$
- Calfeutrage salle de bain (baignoire + douche + joints plancher) : {service3_min}$ – {service3_max}$
- Calfeutrage commercial ou immeuble multi-logements : {service4_min}$ – {service4_max}$

STRUCTURE OBLIGATOIRE — génère ces 6 sections dans l'ordre exact :

---
SECTION 1 — Tableau comparatif des types de calfeutrage à {ville}
<h2 class="text-3xl font-bold mb-4">[Titre accrocheur sur le calfeutrage à {ville} — ex: "Calfeutrage à {ville} : fenêtres, salle de bain ou maison complète — quel projet choisir ?"]</h2>
Suivi d'un <p> de 180-220 mots sur les enjeux du calfeutrage dans {region} : impact des cycles gel-dégel de {region} sur les joints de calfeutrage (silicone qui se fissure après 7-10 cycles), proportion de maisons construites avant 1990 avec calfeutrage d'origine vieilli, perte de chaleur estimée par une étanchéité défaillante (jusqu'à 15-20% de la facture de chauffage dans les maisons non étanches de {region}), types de calfeutrage les plus urgents selon le contexte climatique. Intègre les données chiffrées du contexte régional.
Suivi d'un tableau HTML COMPLET : Type de calfeutrage | Prix à {ville} | Durée de vie | Produit utilisé | Délai d'exécution | Urgent si
Lignes : Maison complète (extérieur) / Fenêtres et portes / Salle de bain (baignoire) / Salle de bain (douche) / Fondation et sous-sol / Maçonnerie et brique / Commercial
Classes tableau : <table class="w-full text-sm border-collapse mt-6 mb-2"> <thead style="background:#d97706;color:#fff"> <th class="px-4 py-3 text-left font-semibold"> <tbody> <tr class="border-b border-gray-200 hover:bg-gray-50"> <td class="px-4 py-3">

---
SECTION 2 — Facteurs qui font varier le prix du calfeutrage à {ville}
<h2> accrocheur ancré dans {ville} ou {region}
<p> de 180-220 mots : nombre d'ouvertures à traiter (fenêtres, portes, baies vitrées — chaque cadre de fenêtre représente 3-4 joints distincts dans une maison de {region}), hauteur et accessibilité (maison plain-pied vs 2 étages — équipement en hauteur nécessaire dans {region}), état du support (enlever et préparer l'ancien calfeutrage vieilli vs nouvelle fenêtre — le retrait prend autant de temps que la pose), type de matériau (silicone pur extérieur premium vs mastic acrylique intérieur — prix et durée de vie très différents), type de surface (PVC, bois, aluminium, brique — adhérence variable), calfeutrage de salle de bain (nécessite un produit antifongique, joints de douche et de baignoire plus complexes à refaire proprement). Pour les montants clés, utilise <strong class="text-orange-600">X $</strong>.
Suivi d'un tableau (thead style="background:#d97706;color:#fff") : Facteur | Impact sur le prix | Détail pour {ville}
Lignes : Nombre d'ouvertures / Hauteur (plain-pied vs 2 étages) / Retrait ancien calfeutrage / Type de produit / Type de surface / Zone intérieure vs extérieure / Urgence (infiltration active)

---
SECTION 3 — Silicone, acrylique ou polyuréthane : quel produit pour {ville} ?
<h2> original mentionnant {ville} ou {region}
<p> de 200-250 mots : SILICONE PUR — le choix standard pour l'extérieur dans {region} : durée de vie 20-25 ans, excellente adhérence sur PVC, aluminium et verre, résistance aux UV et au froid jusqu'à -40°C, imperméable, mais ne se peint pas (rester blanc ou neutre). SILICONE HYBRIDE / POLYURÉTHANE — bonne flexibilité même par grand froid de {region}, se peint après durcissement, idéal pour les cadres de bois et les zones à peindre, durée de vie 10-15 ans. MASTIC ACRYLIQUE — pour usage intérieur uniquement à {ville} (autour des moulures, plinthes, coins de murs), ne supporte pas le gel-dégel de {region}, durée de vie 5-8 ans. CORDE DE CALFEUTRAGE / BACKING ROD — avant d'appliquer le silicone sur les joints larges (maçonnerie, joints de dilatation), pour combler sans gaspillage. Pour la salle de bain : silicone antifongique 100% — obligatoire pour éviter les moisissures dans le contexte humide de {region}. Mets les montants en <strong class="text-orange-600">X $</strong>.
Suivi d'un tableau (thead style="background:#d97706;color:#fff") : Produit | Durée de vie {region} | Usage recommandé | Peinturable | Résistance gel (-40°C) | Prix relatif
Lignes : Silicone pur (extérieur) / Silicone hybride (flexible) / Silicone antifongique (sdb) / Mastic acrylique (intérieur) / Polyuréthane mousse / Corde de calfeutrage

---
SECTION 4 — Les étapes d'un calfeutrage professionnel à {ville}
<h2> pratique et motivant, ancré dans {ville}
<p> de 200-250 mots : les étapes dans l'ordre — (1) inspection des zones à calfeutrer (identifier les fissures actives, les joints dégarnis, les zones avec infiltration d'air ou d'eau), (2) retrait mécanique de l'ancien calfeutrage (outil oscillant ou cutter — étape critique pour une bonne adhérence dans {region}), (3) nettoyage et séchage du support (dégraissage à l'alcool isopropylique pour les surfaces grasses), (4) pose du ruban de masquage pour des joints nets, (5) application du silicone ou du produit adapté (température requise supérieure à -5°C, idéalement 5-25°C dans {region} — travail interdit par grand froid), (6) lissage du joint (outil ou doigt mouillé), (7) retrait du ruban de masquage avant que le silicone sèche, (8) inspection finale et retouches. Fenêtre optimale dans {region} : mai à octobre (chaleur modérée, humidité contrôlée, silicone à la bonne viscosité). Mets les montants en <strong class="text-orange-600">X $</strong>.
Suivi d'un tableau (thead style="background:#d97706;color:#fff") : Étape | Durée typique | Outil utilisé | Astuce pour {ville}
Lignes : Inspection des zones / Retrait ancien calfeutrage / Nettoyage et séchage / Masquage précis / Application silicone / Lissage du joint / Séchage et inspection

---
SECTION 5 — Choisir son calfeutreur à {ville}
<h2> pratique et local
<p> de 200-250 mots : calfeutreur certifié RBQ (licence 1.2.1 rénovation résidentielle — requise si les travaux s'inscrivent dans une rénovation plus large) ou spécialiste calfeutrage (technicien spécialisé sans licence obligatoire pour le calfeutrage pur). Assurance responsabilité civile obligatoire même pour les petits travaux. Ce que doit inclure un bon devis de calfeutrage à {ville} : liste précise des zones à traiter (nombre de fenêtres, zones salle de bain, extérieur), produit utilisé avec marque et type (silicone Tremco, GE, Sikaflex, Loctite), méthode de retrait de l'ancien calfeutrage (inclus ou facturé séparément), garantie sur la main-d'oeuvre (2-5 ans pour un calfeutrage extérieur de qualité). Points d'attention dans {region} : méfiance envers les propositions de calfeutrage par-dessus l'ancien (ne tient pas — recto obligatoire), prix anormalement bas (produit acrylique intérieur appliqué à l'extérieur = défaillance dans le premier hiver de {region}). Délais typiques : 1-3 jours pour une maison complète à {ville}.
Suivi d'un tableau (thead style="background:#d97706;color:#fff") : Critère | Ce qu'il faut vérifier | Pourquoi c'est important
Lignes : Assurance responsabilité / Retrait ancien inclus / Produit et marque précisés / Garantie main-d'oeuvre / Application par temps froid refusée / Prix détaillé par zone / Référence locale {ville}

---
SECTION 6 — FAQ : Calfeutrage à {ville}
<h2 class="text-3xl font-bold mb-8">Questions fréquentes sur le calfeutrage à {ville}</h2>
Génère 6 questions-réponses en accordéon HTML avec ces classes exactes :
<details class="group bg-white rounded-xl border border-gray-200 overflow-hidden mb-3">
<summary class="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50">
<span class="font-semibold text-gray-900 pr-4">QUESTION ICI</span>
<svg class="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
</summary>
<div class="px-6 pb-6 text-gray-600 leading-relaxed">RÉPONSE ICI (100-130 mots, précise, avec données locales)</div>
</details>

Questions à couvrir :
1. Combien coûte un calfeutrage complet à {ville} (utilise les prix fournis)
2. À quelle fréquence faut-il refaire le calfeutrage de sa maison à {ville}
3. Peut-on calfeutrer soi-même ou vaut-il mieux un professionnel à {ville}
4. Quelle est la différence entre calfeutrer et isoler à {ville}
5. Peut-on calfeutrer en hiver à {ville}
6. Comment savoir si le calfeutrage de ma salle de bain doit être refait à {ville}

---

RÈGLES ABSOLUES :
- Réponds UNIQUEMENT avec le HTML brut, aucun commentaire avant ou après
- NE génère PAS de wrapper extérieur <div> ou <section> global — commence directement par le contenu des sections
- Pour le texte courant utilise text-gray-900 (titres/spans), text-gray-600 (corps FAQ) — pour les prix utilise <strong class="text-orange-600">X $</strong>
- Intègre les prix fournis directement dans les tableaux et le texte
- Mentionne {ville} et {region} naturellement dans chaque section
- Aucune liste à puces <ul><li> — uniquement <p>, tableaux et accordéons
- Chaque section doit apporter une valeur distincte, pas de répétition\
""",

    "cloture": """\
Génère un bloc de contenu HTML COMPLET et RICHE pour la page "prix clôture à {ville}" ({region}, Québec).
Population : {population} habitants.

Contexte régional réel : {context}

Prix locaux fournis (utilise ces données dans le contenu) :
- Clôture en bois traité (installation complète, ~100 pi linéaires) : {service1_min}$ – {service1_max}$
- Clôture en vinyle (installation complète, ~100 pi linéaires) : {service2_min}$ – {service2_max}$
- Clôture en aluminium (installation complète, ~100 pi linéaires) : {service3_min}$ – {service3_max}$
- Clôture composite ou chaîne maillée (installation complète, ~100 pi linéaires) : {service4_min}$ – {service4_max}$

STRUCTURE OBLIGATOIRE — génère ces 6 sections dans l'ordre exact :

---
SECTION 1 — Tableau comparatif des matériaux de clôture à {ville}
<h2 class="text-3xl font-bold text-gray-900 mb-4">Prix clôture à {ville} : bois, vinyle ou aluminium — lequel choisir ?</h2>
Suivi d'un <p> de 180-220 mots sur le marché de la clôture dans {region} : types de propriétés dominantes et leurs besoins (cour arrière, piscine, chien, intimité), popularité du bois vs vinyle vs aluminium dans {region}, impact du climat québécois (gel-dégel) sur le choix du matériau, réglementations municipales typiques sur la hauteur. Intègre les données du contexte régional.
Suivi d'un tableau HTML Tailwind COMPLET : Matériau | Prix à {ville} | Durée de vie | Entretien | Résistance gel-dégel | Idéal pour | Permis requis
Lignes : Bois traité sous-pression / Vinyle PVC / Aluminium décoratif / Chaîne maillée / Composite bois-plastique / Cèdre naturel
Classes tableau : <table class="w-full text-sm border-collapse mt-6 mb-2"> <thead class="bg-gray-900 text-white"> <th class="px-4 py-3 text-left font-semibold"> <tbody> <tr class="border-b border-gray-200 hover:bg-gray-50"> <td class="px-4 py-3">

---
SECTION 2 — Coût au pied linéaire et facteurs qui font varier le prix à {ville}
<h2> accrocheur ancré dans {ville}
<p> de 180-220 mots : coût moyen au pied linéaire selon le matériau dans {region} (main-d'œuvre + matériaux), impact de la longueur totale sur le prix unitaire, surcoût pour terrain en pente ou sol rocheux dans {region}, coût de retrait de l'ancienne clôture, coût des portails (simple, double, coulissant), profondeur de gel dans {region} et son impact sur le béton de scellement des poteaux.
Suivi d'un tableau : Facteur | Impact sur le prix | Détail à {ville}
Lignes : Longueur totale (economies d'échelle) / Terrain en pente / Sol rocheux ou argileux / Retrait ancienne clôture / Portail simple / Portail double / Profondeur gel ({region})

---
SECTION 3 — Bois traité vs vinyle vs aluminium : comparatif détaillé pour {ville}
<h2> original mentionnant {region} ou {ville}
<p> de 200-250 mots : bois traité (CCA sous-pression) — avantages naturels, entretien (teinture tous les 2-3 ans), durée 15-25 ans dans le climat de {region} ; vinyle PVC — sans entretien, résistant au gel, durée 20-30 ans, gamme de prix à {ville} ; aluminium décoratif — esthétique, idéal pour cour avant et côté rue, durée 30+ ans, coût plus élevé ; composite — compromis esthétique/durabilité. Ce que les propriétaires de {ville} choisissent le plus souvent selon leur projet.
Suivi d'un tableau : Critère | Bois traité | Vinyle | Aluminium | Composite
Lignes : Prix à {ville} | Durée de vie | Entretien annuel | Résistance UV | Résistance gel | Aspect esthétique | Valeur de revente

---
SECTION 4 — Règlements et permis de clôture à {ville}
<h2> direct et pratique
<p> de 200-250 mots : réglementation typique dans les municipalités de {region} (hauteur maximale en cour avant vs arrière, distance de reculement par rapport aux lignes de propriété, zones de visibilité aux intersections), obligation de permis selon les municipalités de {region} (coût typique 50-200$), règles de copropriété pour les condos, règlements sur les matériaux acceptés (certaines municipalités interdisent la chaîne maillée en cour avant), importance de vérifier les servitudes et droits de passage avant installation à {ville}. Conséquences du non-respect : amende, démolition, litiges avec voisins.
Suivi d'un tableau : Règlement | Cour avant | Cour arrière | Source à vérifier
Lignes : Hauteur maximale / Reculement ligne de propriété / Permis requis / Matériaux interdits / Règles piscine / Délais d'approbation

---
SECTION 5 — Choisir son entrepreneur en clôture à {ville}
<h2> rassurant et local
<p> de 200-250 mots : entrepreneur licencié RBQ (catégorie construction résidentielle ou travaux spécialisés), vérification que le devis inclut : démolition ancienne clôture, béton de scellement, quincaillerie (fixations, charnières, poignées), finition des bouts de poteaux. Délais typiques dans {region} en haute saison (mai à septembre — délais de 4-10 semaines). Importance de comparer 3 soumissions à {ville}. Garanties : main-d'œuvre 1 an minimum, matériaux selon fabricant. Questions à poser : le devis inclut-il le permit ? Les poteaux sont-ils coulés dans le béton à la bonne profondeur pour {region} ? L'ancienne clôture est-elle comprise ?
Suivi d'un tableau : Critère | Ce qu'il faut vérifier | Pourquoi c'est important
Lignes : Licence RBQ / Devis inclut retrait ancienne clôture / Profondeur des poteaux / Béton inclus / Garantie main-d'œuvre / Permis inclus / Références locales

---
SECTION 6 — FAQ : Clôture à {ville}
<h2 class="text-3xl font-bold text-gray-900 mb-8">Questions fréquentes sur l'installation de clôture à {ville}</h2>
Génère 6 questions-réponses en accordéon HTML avec ces classes exactes :
<details class="group bg-white rounded-xl border border-gray-200 overflow-hidden mb-3">
<summary class="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50">
<span class="font-semibold text-gray-900 pr-4">QUESTION ICI</span>
<svg class="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
</summary>
<div class="px-6 pb-6 text-gray-600 leading-relaxed">RÉPONSE ICI (80-120 mots, précise, avec données locales)</div>
</details>

Questions à couvrir :
1. Combien coûte une clôture en bois à {ville} (utilise les prix fournis)
2. Quelle est la meilleure clôture pour le climat de {region} — bois, vinyle ou aluminium
3. Faut-il un permis pour installer une clôture à {ville}
4. À quelle profondeur doit-on couler les poteaux dans {region}
5. Combien de temps dure l'installation d'une clôture à {ville}
6. Peut-on installer une clôture soi-même ou faut-il un entrepreneur à {ville}

---

RÈGLES ABSOLUES :
- Réponds UNIQUEMENT avec le HTML brut, aucun commentaire avant ou après
- NE génère PAS de wrapper extérieur <div> ou <section> global — commence directement par le contenu des sections
- Utilise les classes Tailwind déjà définies dans le site (text-gray-900, text-gray-600, font-bold, etc.)
- Intègre les prix fournis directement dans les tableaux et le texte
- Mentionne {ville} et {region} naturellement dans chaque section
- Aucune liste à puces <ul><li> — uniquement <p>, tableaux et accordéons
- Chaque section doit apporter une valeur distincte, pas de répétition\
""",
}


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def load_cities(csv_path: Path) -> list:
    cities = []
    encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            with open(csv_path, encoding=enc) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ville = row.get("munnom", "").strip()
                    region = row.get("regadm", "").strip()
                    if ville and region:
                        cities.append({
                            "ville": ville,
                            "region": region,
                            "slug": slugify(ville),
                            "population": int(row.get("mpopul", 0) or 0),
                        })
            break
        except (UnicodeDecodeError, KeyError):
            continue
    return cities


def main():
    parser = argparse.ArgumentParser(description="Generate per-city content via Claude Haiku")
    parser.add_argument("--niche", required=True, help="Niche slug (couvreur, bardeau, etc.)")
    parser.add_argument("--csv", default=None, help="Path to MUN.csv")
    parser.add_argument("--resume", action="store_true", help="Resume from existing output file")
    parser.add_argument("--limit", type=int, default=0, help="Limit to N cities (0 = all, for testing)")
    parser.add_argument("--workers", type=int, default=30, help="Nombre de workers parallèles (défaut: 30)")
    args = parser.parse_args()

    base = Path(__file__).parent.parent
    csv_path = Path(args.csv) if args.csv else base / "MUN.csv"
    # sites standalone dans Sites_relateds/, pas engine_qc/
    SITES_RELATEDS_NICHES = ("prix-toiture", "prix-thermopompe", "prix-drain", "prix-fissure", "prix-fenetres", "prix-revetement", "prix-gouttieres")
    if args.niche in SITES_RELATEDS_NICHES:
        niche_dir = base.parent / "Sites_relateds"
    else:
        niche_dir = base / "engine_qc"
    context_path = niche_dir / f"regional_context_{args.niche}.json"
    output_path = niche_dir / f"city_content_{args.niche}.json"

    if not context_path.exists():
        print(f"ERROR: {context_path} introuvable. Lance fetch_regional_context.py d'abord.")
        return

    regional_context = json.loads(context_path.read_text(encoding="utf-8"))

    # Pour prix-drain : extraire les prix Perplexity depuis le contexte régional
    # Priorité des prix : cache ville > Perplexity région > fallback population
    drain_region_prices = {}
    if args.niche == "prix-drain":
        for region_name, ctx_text in regional_context.items():
            if "---PRIX---" in ctx_text:
                try:
                    prix_bloc = ctx_text.split("---PRIX---", 1)[1].strip()
                    # Prendre la première ligne JSON valide
                    for line in prix_bloc.splitlines():
                        line = line.strip()
                        if line.startswith("{"):
                            parsed = json.loads(line)
                            # Valider que les clés attendues sont présentes et cohérentes
                            required = {"drain_min", "drain_max", "fissure_min", "fissure_max", "impermea_min"}
                            if required.issubset(parsed.keys()):
                                # Sanity check : valeurs dans plages réalistes QC
                                if (8000 <= int(parsed["drain_min"]) <= 60000
                                        and int(parsed["fissure_min"]) >= 500):
                                    drain_region_prices[region_name] = {k: int(v) for k, v in parsed.items() if k in required}
                            break
                except Exception:
                    pass
        if drain_region_prices:
            print(f"Prix Perplexity chargés pour {len(drain_region_prices)}/{len(regional_context)} régions")
        else:
            print("Aucun prix Perplexity trouvé — utilisation des fallbacks population")

    fissure_region_prices = {}
    if args.niche == "prix-fissure":
        for region_name, ctx_text in regional_context.items():
            if "---PRIX---" in ctx_text:
                try:
                    prix_bloc = ctx_text.split("---PRIX---", 1)[1].strip()
                    for line in prix_bloc.splitlines():
                        line = line.strip()
                        if line.startswith("{"):
                            parsed = json.loads(line)
                            required = {"simple_min", "simple_max", "infiltration_min", "infiltration_max", "struct_min", "struct_max"}
                            if required.issubset(parsed.keys()):
                                if (400 <= int(parsed["simple_min"]) <= 5000
                                        and int(parsed["infiltration_min"]) >= 500):
                                    fissure_region_prices[region_name] = {k: int(v) for k, v in parsed.items() if k in required}
                            break
                except Exception:
                    pass
        if fissure_region_prices:
            print(f"Prix fissure Perplexity chargés : {len(fissure_region_prices)}/{len(regional_context)} régions")
        else:
            print("Aucun prix fissure Perplexity — fallbacks population")

    gouttieres_region_prices = {}
    if args.niche == "prix-gouttieres":
        for region_name, ctx_text in regional_context.items():
            if "---PRIX---" in ctx_text:
                try:
                    prix_bloc = ctx_text.split("---PRIX---", 1)[1].strip()
                    for line in prix_bloc.splitlines():
                        line = line.strip()
                        if line.startswith("{"):
                            parsed = json.loads(line)
                            required = {"service1_min", "service1_max", "service2_min", "service2_max", "service3_min", "service3_max", "service4_min", "service4_max"}
                            if required.issubset(parsed.keys()):
                                gouttieres_region_prices[region_name] = {k: int(v) for k, v in parsed.items() if k in required}
                            break
                except Exception:
                    pass
        if gouttieres_region_prices:
            print(f"Prix gouttières Perplexity chargés : {len(gouttieres_region_prices)}/{len(regional_context)} régions")
        else:
            print("Aucun prix gouttières Perplexity — fallbacks population")

    ceramique_region_prices = {}
    if args.niche == "ceramique":
        for region_name, ctx_text in regional_context.items():
            if "---PRIX---" in ctx_text:
                try:
                    prix_bloc = ctx_text.split("---PRIX---", 1)[1].strip()
                    for line in prix_bloc.splitlines():
                        line = line.strip()
                        if line.startswith("{"):
                            parsed = json.loads(line)
                            required = {"service1_min", "service1_max", "service2_min", "service2_max", "service3_min", "service3_max"}
                            if required.issubset(parsed.keys()):
                                ceramique_region_prices[region_name] = {k: int(v) for k, v in parsed.items() if k in required}
                            break
                except Exception:
                    pass
        if ceramique_region_prices:
            print(f"Prix céramique Perplexity chargés : {len(ceramique_region_prices)}/{len(regional_context)} régions")
        else:
            print("Aucun prix céramique Perplexity — fallbacks population")

    beton_region_prices = {}
    if args.niche == "beton":
        for region_name, ctx_text in regional_context.items():
            if "---PRIX---" in ctx_text:
                try:
                    prix_bloc = ctx_text.split("---PRIX---", 1)[1].strip()
                    for line in prix_bloc.splitlines():
                        line = line.strip()
                        if line.startswith("{"):
                            parsed = json.loads(line)
                            required = {"service1_min", "service1_max", "service2_min", "service2_max",
                                        "service3_min", "service3_max", "service4_min", "service4_max"}
                            if required.issubset(parsed.keys()):
                                beton_region_prices[region_name] = {k: int(v) for k, v in parsed.items() if k in required}
                            break
                except Exception:
                    pass
        if beton_region_prices:
            print(f"Prix béton Perplexity chargés : {len(beton_region_prices)}/{len(regional_context)} régions")
        else:
            print("Aucun prix béton Perplexity — fallbacks population")

    toiture_plate_region_prices = {}
    if args.niche == "toiture-plate":
        for region_name, ctx_text in regional_context.items():
            if "---PRIX---" in ctx_text:
                try:
                    prix_bloc = ctx_text.split("---PRIX---", 1)[1].strip()
                    for line in prix_bloc.splitlines():
                        line = line.strip()
                        if line.startswith("{"):
                            parsed = json.loads(line)
                            required = {"service1_min", "service1_max", "service2_min", "service2_max",
                                        "service3_min", "service3_max", "service4_min", "service4_max"}
                            if required.issubset(parsed.keys()):
                                toiture_plate_region_prices[region_name] = {k: int(v) for k, v in parsed.items() if k in required}
                            break
                except Exception:
                    pass
        if toiture_plate_region_prices:
            print(f"Prix toiture plate Perplexity chargés : {len(toiture_plate_region_prices)}/{len(regional_context)} régions")
        else:
            print("Aucun prix toiture plate Perplexity — fallbacks population")

    cloture_region_prices = {}
    if args.niche == "cloture":
        for region_name, ctx_text in regional_context.items():
            if "---PRIX---" in ctx_text:
                try:
                    prix_bloc = ctx_text.split("---PRIX---", 1)[1].strip()
                    for line in prix_bloc.splitlines():
                        line = line.strip()
                        if line.startswith("{"):
                            parsed = json.loads(line)
                            required = {"service1_min", "service1_max", "service2_min", "service2_max",
                                        "service3_min", "service3_max", "service4_min", "service4_max"}
                            if required.issubset(parsed.keys()):
                                cloture_region_prices[region_name] = {k: int(v) for k, v in parsed.items() if k in required}
                            break
                except Exception:
                    pass
        if cloture_region_prices:
            print(f"Prix clôture Perplexity chargés : {len(cloture_region_prices)}/{len(regional_context)} régions")
        else:
            print("Aucun prix clôture Perplexity — fallbacks population")

    salledebain_region_prices = {}
    if args.niche == "salledebain":
        for region_name, ctx_text in regional_context.items():
            if "---PRIX---" in ctx_text:
                try:
                    prix_bloc = ctx_text.split("---PRIX---", 1)[1].strip()
                    for line in prix_bloc.splitlines():
                        line = line.strip()
                        if line.startswith("{"):
                            parsed = json.loads(line)
                            required = {"service1_min", "service1_max", "service2_min", "service2_max",
                                        "service3_min", "service3_max", "service4_min", "service4_max"}
                            if required.issubset(parsed.keys()):
                                salledebain_region_prices[region_name] = {k: int(v) for k, v in parsed.items() if k in required}
                            break
                except Exception:
                    pass
        if salledebain_region_prices:
            print(f"Prix salle de bain Perplexity chargés : {len(salledebain_region_prices)}/{len(regional_context)} régions")
        else:
            print("Aucun prix salle de bain Perplexity — fallbacks population")

    decontamination_region_prices = {}
    if args.niche == "decontamination":
        for region_name, ctx_text in regional_context.items():
            if "---PRIX---" in ctx_text:
                try:
                    for line in ctx_text.split("---PRIX---")[1].strip().splitlines():
                        line = line.strip()
                        if line.startswith("{"):
                            parsed = json.loads(line)
                            required = {"service1_min", "service1_max", "service2_min", "service2_max",
                                        "service3_min", "service3_max", "service4_min", "service4_max"}
                            if required.issubset(parsed.keys()):
                                decontamination_region_prices[region_name] = {k: int(v) for k, v in parsed.items() if k in required}
                            break
                except Exception:
                    pass
        if decontamination_region_prices:
            print(f"Prix décontamination Perplexity chargés : {len(decontamination_region_prices)}/{len(regional_context)} régions")
        else:
            print("Aucun prix décontamination Perplexity — fallbacks population")

    peinture_region_prices = {}
    if args.niche == "peinture":
        for region_name, ctx_text in regional_context.items():
            if "---PRIX---" in ctx_text:
                try:
                    for line in ctx_text.split("---PRIX---")[1].strip().splitlines():
                        line = line.strip()
                        if line.startswith("{"):
                            parsed = json.loads(line)
                            required = {"service1_min", "service1_max", "service2_min", "service2_max",
                                        "service3_min", "service3_max", "service4_min", "service4_max"}
                            if required.issubset(parsed.keys()):
                                peinture_region_prices[region_name] = {k: int(v) for k, v in parsed.items() if k in required}
                            break
                except Exception:
                    pass
        if peinture_region_prices:
            print(f"Prix peinture Perplexity chargés : {len(peinture_region_prices)}/{len(regional_context)} régions")
        else:
            print("Aucun prix peinture Perplexity — fallbacks population")

    # Generic niche_research loader — auto-load prompts + prices for research-driven niches
    research_region_prices = {}
    research_price_tiers = {}
    niche_research_path = base / "engine_qc" / f"niche_research_{args.niche}.json"
    if niche_research_path.exists() and args.niche not in SYSTEM_PROMPTS:
        try:
            nr = json.loads(niche_research_path.read_text(encoding="utf-8"))
            if "system_prompt" in nr:
                SYSTEM_PROMPTS[args.niche] = nr["system_prompt"]
            if "user_prompt_template" in nr:
                USER_PROMPT_TEMPLATES[args.niche] = nr["user_prompt_template"]
            if "price_tiers" in nr:
                research_price_tiers = nr["price_tiers"]
            print(f"Prompts + prix charges depuis niche_research_{args.niche}.json")
        except Exception as e:
            print(f"Avertissement niche_research load: {e}")
        # Parse regional prices from regional_context
        for region_name, ctx_text in regional_context.items():
            if "---PRIX---" in ctx_text:
                try:
                    prix_bloc = ctx_text.split("---PRIX---", 1)[1].strip()
                    for line in prix_bloc.splitlines():
                        line = line.strip()
                        if line.startswith("{"):
                            # Handle both {"key": val} and {key: val} formats
                            try:
                                parsed = json.loads(line)
                            except json.JSONDecodeError:
                                import re as _re
                                fixed = _re.sub(r'([{,])\s*(\w+)\s*:', r'\1 "\2":', line)
                                parsed = json.loads(fixed)
                            required = {"service1_min", "service1_max", "service2_min", "service2_max",
                                        "service3_min", "service3_max", "service4_min", "service4_max"}
                            if required.issubset(parsed.keys()):
                                research_region_prices[region_name] = {k: int(v) for k, v in parsed.items() if k in required}
                            break
                except Exception:
                    pass
        if research_region_prices:
            print(f"Prix regionaux charges : {len(research_region_prices)}/{len(regional_context)} regions")

    cities = load_cities(csv_path)
    print(f"{len(cities)} villes chargées")

    # Resume support
    existing = {}
    if args.resume and output_path.exists():
        existing = json.loads(output_path.read_text(encoding="utf-8"))
        print(f"Reprise : {len(existing)} villes déjà générées")

    # Charge les caches de prix par ville selon la niche
    toiture_cache = {}
    drain_cache = {}
    fissure_cache = {}
    sites_dir = base.parent / "Sites_relateds"
    if args.niche == "prix-toiture":
        p = sites_dir / "_cache_toiture.json"
        if p.exists():
            toiture_cache = json.loads(p.read_text(encoding="utf-8", errors="replace"))
            print(f"Cache toiture chargé : {len(toiture_cache)} villes")
    elif args.niche == "prix-drain":
        p = sites_dir / "_cache_drain.json"
        if p.exists():
            drain_cache = json.loads(p.read_text(encoding="utf-8", errors="replace"))
            print(f"Cache drain chargé : {len(drain_cache)} villes")
    elif args.niche == "prix-fissure":
        p = sites_dir / "_cache_fissure.json"
        if p.exists():
            fissure_cache = json.loads(p.read_text(encoding="utf-8", errors="replace"))
            print(f"Cache fissure chargé : {len(fissure_cache)} villes")

    LARGE_NICHES = ("prix-toiture", "prix-thermopompe", "prix-drain", "prix-fissure", "prix-fenetres", "prix-revetement", "prix-gouttieres", "excavation", "cuisine", "ceramique", "beton", "toiture-plate", "salledebain", "cloture", "porte-garage", "chauffage", "agrandissement", "peinture", "decontamination", "paysagement", "electricien", "portes-fenetres", "fosseseptique", "nettoyage-conduits", "calfeutrage")
    max_tokens = 16000 if args.niche in LARGE_NICHES else 1500

    client = anthropic.Anthropic()
    system = SYSTEM_PROMPTS.get(args.niche, SYSTEM_PROMPTS["couvreur"])
    user_tpl = USER_PROMPT_TEMPLATES.get(args.niche, USER_PROMPT_TEMPLATES["couvreur"])

    output = dict(existing)
    total = len(cities)
    lock = threading.Lock()
    done_count = [0]

    if args.limit:
        cities = cities[:args.limit]

    # Filtrer les villes déjà générées
    cities_todo = []
    for i, city in enumerate(cities, 1):
        key = f"{slugify(city['ville'])}|{slugify(city['region'])}"
        if not existing.get(key):
            cities_todo.append((i, city))
    print(f"À générer : {len(cities_todo)} villes ({len(existing)} déjà faites)")
    _openai_key_present = bool(os.environ.get("OPENAI_API_KEY", ""))
    if _openai_key_present:
        print(f"Modèle : gpt-5.4-nano (OpenAI)" + (" — Section 7 pour villes >= 50k hab" if args.niche == "chauffage" else ""))
    else:
        print(f"Modèle : claude-haiku-4-5")

    def build_extra_kwargs(city):
        slug = slugify(city["ville"])
        if args.niche == "prix-toiture":
            cached = toiture_cache.get(slug, {})
            return {
                "population": city.get("population", 0),
                "bard_min": cached.get("bard_min", 7500),
                "bard_max": cached.get("bard_max", 12000),
                "metal_min": cached.get("metal_min", 14000),
                "metal_max": cached.get("metal_max", 20000),
                "tpo_min": cached.get("tpo_min", 8000),
                "tpo_max": cached.get("tpo_max", 14000),
                "rep_min": cached.get("rep_min", 300),
                "rep_max": cached.get("rep_max", 2000),
            }
        elif args.niche == "prix-thermopompe":
            pop = city.get("population", 0)
            if pop >= 50000:
                kw = {"mini_min": 2200, "mini_max": 4500, "multi_min": 4500, "multi_max": 8500,
                      "centrale_min": 6000, "centrale_max": 12000, "aero_min": 8000, "aero_max": 18000,
                      "entretien_min": 150, "entretien_max": 350}
            elif pop >= 15000:
                kw = {"mini_min": 2000, "mini_max": 4200, "multi_min": 4200, "multi_max": 8000,
                      "centrale_min": 5500, "centrale_max": 11000, "aero_min": 7500, "aero_max": 17000,
                      "entretien_min": 130, "entretien_max": 300}
            elif pop >= 5000:
                kw = {"mini_min": 1900, "mini_max": 4000, "multi_min": 4000, "multi_max": 7500,
                      "centrale_min": 5000, "centrale_max": 10000, "aero_min": 7000, "aero_max": 16000,
                      "entretien_min": 120, "entretien_max": 280}
            else:
                kw = {"mini_min": 1800, "mini_max": 3800, "multi_min": 3800, "multi_max": 7000,
                      "centrale_min": 4500, "centrale_max": 9500, "aero_min": 6500, "aero_max": 15000,
                      "entretien_min": 110, "entretien_max": 260}
            kw["population"] = pop
            return kw
        elif args.niche == "prix-drain":
            slug = slugify(city["ville"])
            pop = city.get("population", 0)
            region_name = city.get("region", "")
            cached = drain_cache.get(slug, {})

            # Niveau 3 — fallback population (dernier recours)
            if pop >= 50000:
                fb = {"drain_min": 22000, "drain_max": 32000, "fissure_min": 7000, "fissure_max": 12000, "impermea_min": 27000}
            elif pop >= 15000:
                fb = {"drain_min": 19000, "drain_max": 28000, "fissure_min": 6000, "fissure_max": 10000, "impermea_min": 23000}
            elif pop >= 3000:
                fb = {"drain_min": 16500, "drain_max": 25000, "fissure_min": 5000, "fissure_max": 9000, "impermea_min": 20000}
            else:
                fb = {"drain_min": 14500, "drain_max": 22000, "fissure_min": 4500, "fissure_max": 8000, "impermea_min": 18000}

            # Niveau 2 — prix Perplexity par région (réel, 17 régions)
            rp = drain_region_prices.get(region_name, {})

            # Niveau 1 — cache ville individuel (plus précis) > région Perplexity > fallback pop
            def pick(key):
                return cached.get(key) or rp.get(key) or fb[key]

            return {
                "population": pop,
                "drain_min":    pick("drain_min"),
                "drain_max":    pick("drain_max"),
                "fissure_min":  pick("fissure_min"),
                "fissure_max":  pick("fissure_max"),
                "impermea_min": pick("impermea_min"),
            }
        elif args.niche == "prix-fissure":
            slug = slugify(city["ville"])
            pop = city.get("population", 0)
            region_name = city.get("region", "")
            cached = fissure_cache.get(slug, {})
            # Niveau 3 — fallback population
            if pop >= 50000:
                fb = {"simple_min": 900, "simple_max": 2200, "infiltration_min": 1800, "infiltration_max": 4000, "struct_min": 3000, "struct_max": 6500}
            elif pop >= 15000:
                fb = {"simple_min": 800, "simple_max": 2000, "infiltration_min": 1500, "infiltration_max": 3500, "struct_min": 2500, "struct_max": 5500}
            elif pop >= 3000:
                fb = {"simple_min": 700, "simple_max": 1800, "infiltration_min": 1300, "infiltration_max": 3000, "struct_min": 2200, "struct_max": 5000}
            else:
                fb = {"simple_min": 650, "simple_max": 1600, "infiltration_min": 1200, "infiltration_max": 2800, "struct_min": 2000, "struct_max": 4500}
            # Niveau 2 — prix Perplexity par région
            rp = fissure_region_prices.get(region_name, {})
            def pick_f(key): return cached.get(key) or rp.get(key) or fb[key]
            return {
                "population": pop,
                "simple_min":       pick_f("simple_min"),
                "simple_max":       pick_f("simple_max"),
                "infiltration_min": pick_f("infiltration_min"),
                "infiltration_max": pick_f("infiltration_max"),
                "struct_min":       pick_f("struct_min"),
                "struct_max":       pick_f("struct_max"),
            }
        elif args.niche == "prix-fenetres":
            pop = city.get("population", 0)
            if pop >= 50000:
                kw = {"pvc_min": 540, "pvc_max": 830, "hyb_min": 885, "hyb_max": 1285, "pf_min": 2125, "pf_max": 5325}
            elif pop >= 15000:
                kw = {"pvc_min": 575, "pvc_max": 860, "hyb_min": 920, "hyb_max": 1325, "pf_min": 2235, "pf_max": 5525}
            elif pop >= 3000:
                kw = {"pvc_min": 600, "pvc_max": 895, "hyb_min": 960, "hyb_max": 1375, "pf_min": 2350, "pf_max": 5825}
            else:
                kw = {"pvc_min": 630, "pvc_max": 935, "hyb_min": 1005, "hyb_max": 1435, "pf_min": 2515, "pf_max": 6175}
            kw["population"] = pop
            return kw
        elif args.niche == "prix-revetement":
            pop = city.get("population", 0)
            if pop >= 50000:
                kw = {"vinyle_min": 8900, "vinyle_max": 15250, "canexel_min": 16250, "canexel_max": 25500,
                      "fibrociment_min": 21750, "fibrociment_max": 39500, "aluminium_min": 10750, "aluminium_max": 18250}
            elif pop >= 15000:
                kw = {"vinyle_min": 9500, "vinyle_max": 16300, "canexel_min": 17350, "canexel_max": 27250,
                      "fibrociment_min": 23200, "fibrociment_max": 42200, "aluminium_min": 11450, "aluminium_max": 19500}
            elif pop >= 3000:
                kw = {"vinyle_min": 9950, "vinyle_max": 17050, "canexel_min": 18150, "canexel_max": 28550,
                      "fibrociment_min": 24300, "fibrociment_max": 44250, "aluminium_min": 12000, "aluminium_max": 20450}
            else:
                kw = {"vinyle_min": 10400, "vinyle_max": 17850, "canexel_min": 19000, "canexel_max": 29850,
                      "fibrociment_min": 25450, "fibrociment_max": 46350, "aluminium_min": 12550, "aluminium_max": 21550}
            kw["population"] = pop
            return kw
        elif args.niche == "prix-gouttieres":
            pop = city.get("population", 0)
            region_name = city.get("region", "")
            if pop >= 50000:
                fb = {"service1_min": 1248, "service1_max": 3329, "service2_min": 832, "service2_max": 2600,
                      "service3_min": 156, "service3_max": 416, "service4_min": 208, "service4_max": 832}
            elif pop >= 15000:
                fb = {"service1_min": 1144, "service1_max": 3016, "service2_min": 780, "service2_max": 2340,
                      "service3_min": 143, "service3_max": 390, "service4_min": 195, "service4_max": 780}
            elif pop >= 5000:
                fb = {"service1_min": 1014, "service1_max": 2704, "service2_min": 728, "service2_max": 2184,
                      "service3_min": 130, "service3_max": 364, "service4_min": 182, "service4_max": 728}
            else:
                fb = {"service1_min": 910, "service1_max": 2392, "service2_min": 676, "service2_max": 2028,
                      "service3_min": 117, "service3_max": 338, "service4_min": 169, "service4_max": 676}
            rp = gouttieres_region_prices.get(region_name, {})
            def pick_g(key): return rp.get(key) or fb[key]
            return {
                "population": pop,
                "service1_min": pick_g("service1_min"), "service1_max": pick_g("service1_max"),
                "service2_min": pick_g("service2_min"), "service2_max": pick_g("service2_max"),
                "service3_min": pick_g("service3_min"), "service3_max": pick_g("service3_max"),
                "service4_min": pick_g("service4_min"), "service4_max": pick_g("service4_max"),
            }
        elif args.niche == "excavation":
            pop = city.get("population", 0)
            if pop >= 50000:
                kw = {"excav_min": 4500, "excav_max": 28000, "terras_min": 2000, "terras_max": 9500,
                      "drain_min": 2500, "drain_max": 8000, "fondation_min": 14000, "fondation_max": 48000}
            elif pop >= 15000:
                kw = {"excav_min": 3500, "excav_max": 22000, "terras_min": 1600, "terras_max": 7500,
                      "drain_min": 2000, "drain_max": 6500, "fondation_min": 11000, "fondation_max": 40000}
            elif pop >= 5000:
                kw = {"excav_min": 2800, "excav_max": 18000, "terras_min": 1200, "terras_max": 6000,
                      "drain_min": 1800, "drain_max": 5500, "fondation_min": 9000, "fondation_max": 34000}
            else:
                kw = {"excav_min": 2200, "excav_max": 14000, "terras_min": 1000, "terras_max": 4800,
                      "drain_min": 1500, "drain_max": 4500, "fondation_min": 7500, "fondation_max": 28000}
            kw["population"] = pop
            return kw
        elif args.niche == "cuisine":
            pop = city.get("population", 0)
            if pop >= 50000:
                kw = {"service1_min": 3500, "service1_max": 18000, "service2_min": 5000, "service2_max": 30000,
                      "service3_min": 15000, "service3_max": 65000, "service4_min": 1200, "service4_max": 6000}
            elif pop >= 15000:
                kw = {"service1_min": 3000, "service1_max": 15000, "service2_min": 4500, "service2_max": 25000,
                      "service3_min": 12000, "service3_max": 55000, "service4_min": 1000, "service4_max": 5000}
            elif pop >= 5000:
                kw = {"service1_min": 2500, "service1_max": 12000, "service2_min": 4000, "service2_max": 20000,
                      "service3_min": 10000, "service3_max": 45000, "service4_min": 900, "service4_max": 4000}
            else:
                kw = {"service1_min": 2000, "service1_max": 10000, "service2_min": 3500, "service2_max": 18000,
                      "service3_min": 8000, "service3_max": 38000, "service4_min": 800, "service4_max": 3500}
            kw["population"] = pop
            return kw
        elif args.niche == "ceramique":
            pop = city.get("population", 0)
            region_name = city.get("region", "")
            # Niveau 3 — fallback population (config_ceramique.json tiers)
            if pop >= 50000:
                fb = {"service1_min": 1500, "service1_max": 6000, "service2_min": 800, "service2_max": 3500, "service3_min": 1200, "service3_max": 5000}
            elif pop >= 15000:
                fb = {"service1_min": 1230, "service1_max": 4920, "service2_min": 656, "service2_max": 2870, "service3_min": 983, "service3_max": 4100}
            elif pop >= 5000:
                fb = {"service1_min": 1050, "service1_max": 4200, "service2_min": 560, "service2_max": 2450, "service3_min": 840, "service3_max": 3500}
            else:
                fb = {"service1_min": 869, "service1_max": 3479, "service2_min": 463, "service2_max": 2029, "service3_min": 696, "service3_max": 2900}
            # Niveau 2 — prix Perplexity par région (plus précis)
            rp = ceramique_region_prices.get(region_name, {})
            def pick_c(key): return rp.get(key) or fb[key]
            s1_min = pick_c("service1_min")
            s1_max = pick_c("service1_max")
            return {
                "population": pop,
                "service1_min": s1_min,
                "service1_max": s1_max,
                "service2_min": pick_c("service2_min"),
                "service2_max": pick_c("service2_max"),
                "service3_min": pick_c("service3_min"),
                "service3_max": pick_c("service3_max"),
                "service4_min": int(s1_min * 1.3),
                "service4_max": int(s1_max * 1.6),
            }
        elif args.niche == "beton":
            pop = city.get("population", 0)
            region_name = city.get("region", "")
            # Niveau 3 — fallback population (config_beton.json tiers)
            if pop >= 50000:
                fb = {"service1_min": 5000, "service1_max": 20000, "service2_min": 3500, "service2_max": 14000,
                      "service3_min": 2000, "service3_max": 9000, "service4_min": 4000, "service4_max": 18000}
            elif pop >= 15000:
                fb = {"service1_min": 4100, "service1_max": 16400, "service2_min": 2870, "service2_max": 11480,
                      "service3_min": 1640, "service3_max": 7380, "service4_min": 3280, "service4_max": 14760}
            elif pop >= 5000:
                fb = {"service1_min": 3500, "service1_max": 14000, "service2_min": 2450, "service2_max": 9800,
                      "service3_min": 1400, "service3_max": 6300, "service4_min": 2800, "service4_max": 12600}
            else:
                fb = {"service1_min": 2900, "service1_max": 11600, "service2_min": 2029, "service2_max": 8119,
                      "service3_min": 1160, "service3_max": 5220, "service4_min": 2320, "service4_max": 10440}
            # Niveau 2 — prix Perplexity par région
            rp = beton_region_prices.get(region_name, {})
            def pick_b(key): return rp.get(key) or fb[key]
            return {
                "population": pop,
                "service1_min": pick_b("service1_min"), "service1_max": pick_b("service1_max"),
                "service2_min": pick_b("service2_min"), "service2_max": pick_b("service2_max"),
                "service3_min": pick_b("service3_min"), "service3_max": pick_b("service3_max"),
                "service4_min": pick_b("service4_min"), "service4_max": pick_b("service4_max"),
            }
        elif args.niche == "toiture-plate":
            pop = city.get("population", 0)
            region_name = city.get("region", "")
            # Niveau 3 — fallback population (config_toiture-plate.json tiers)
            if pop >= 50000:
                fb = {"service1_min": 8000, "service1_max": 30000, "service2_min": 5000, "service2_max": 20000,
                      "service3_min": 12000, "service3_max": 45000, "service4_min": 3000, "service4_max": 12000}
            elif pop >= 15000:
                fb = {"service1_min": 6560, "service1_max": 24600, "service2_min": 4100, "service2_max": 16400,
                      "service3_min": 9840, "service3_max": 36900, "service4_min": 2460, "service4_max": 9840}
            elif pop >= 5000:
                fb = {"service1_min": 5600, "service1_max": 21000, "service2_min": 3500, "service2_max": 14000,
                      "service3_min": 8400, "service3_max": 31499, "service4_min": 2100, "service4_max": 8400}
            else:
                fb = {"service1_min": 4640, "service1_max": 17400, "service2_min": 2900, "service2_max": 11600,
                      "service3_min": 6959, "service3_max": 26100, "service4_min": 1739, "service4_max": 6959}
            # Niveau 2 — prix Perplexity par région
            rp = toiture_plate_region_prices.get(region_name, {})
            def pick_tp(key): return rp.get(key) or fb[key]
            return {
                "population": pop,
                "service1_min": pick_tp("service1_min"), "service1_max": pick_tp("service1_max"),
                "service2_min": pick_tp("service2_min"), "service2_max": pick_tp("service2_max"),
                "service3_min": pick_tp("service3_min"), "service3_max": pick_tp("service3_max"),
                "service4_min": pick_tp("service4_min"), "service4_max": pick_tp("service4_max"),
            }
        elif args.niche == "cloture":
            pop = city.get("population", 0)
            region_name = city.get("region", "")
            if pop >= 50000:
                fb = {"service1_min": 3500, "service1_max": 12000, "service2_min": 1800, "service2_max": 6000,
                      "service3_min": 1200, "service3_max": 4500, "service4_min": 2500, "service4_max": 8000}
            elif pop >= 15000:
                fb = {"service1_min": 2900, "service1_max": 9800, "service2_min": 1500, "service2_max": 4900,
                      "service3_min": 1000, "service3_max": 3700, "service4_min": 2100, "service4_max": 6600}
            elif pop >= 5000:
                fb = {"service1_min": 2450, "service1_max": 8400, "service2_min": 1260, "service2_max": 4200,
                      "service3_min": 840, "service3_max": 3150, "service4_min": 1750, "service4_max": 5600}
            else:
                fb = {"service1_min": 2030, "service1_max": 6960, "service2_min": 1040, "service2_max": 3480,
                      "service3_min": 700, "service3_max": 2610, "service4_min": 1450, "service4_max": 4640}
            rp = cloture_region_prices.get(region_name, {})
            def pick_cl(key): return rp.get(key) or fb[key]
            return {
                "population": pop,
                "service1_min": pick_cl("service1_min"), "service1_max": pick_cl("service1_max"),
                "service2_min": pick_cl("service2_min"), "service2_max": pick_cl("service2_max"),
                "service3_min": pick_cl("service3_min"), "service3_max": pick_cl("service3_max"),
                "service4_min": pick_cl("service4_min"), "service4_max": pick_cl("service4_max"),
            }
        elif args.niche == "decontamination":
            pop = city.get("population", 0)
            region_name = city.get("region", "")
            if pop >= 50000:
                fb = {"service1_min": 1200, "service1_max": 5500, "service2_min": 400, "service2_max": 1500,
                      "service3_min": 200, "service3_max": 800, "service4_min": 800, "service4_max": 3500}
            elif pop >= 15000:
                fb = {"service1_min": 900, "service1_max": 4500, "service2_min": 350, "service2_max": 1200,
                      "service3_min": 175, "service3_max": 700, "service4_min": 700, "service4_max": 3000}
            elif pop >= 5000:
                fb = {"service1_min": 750, "service1_max": 3800, "service2_min": 300, "service2_max": 1000,
                      "service3_min": 150, "service3_max": 600, "service4_min": 600, "service4_max": 2500}
            else:
                fb = {"service1_min": 600, "service1_max": 3200, "service2_min": 250, "service2_max": 850,
                      "service3_min": 125, "service3_max": 500, "service4_min": 500, "service4_max": 2200}
            rp = decontamination_region_prices.get(region_name, {})
            def pick_dc(key): return rp.get(key) or fb[key]
            return {
                "population": pop,
                "service1_min": pick_dc("service1_min"), "service1_max": pick_dc("service1_max"),
                "service2_min": pick_dc("service2_min"), "service2_max": pick_dc("service2_max"),
                "service3_min": pick_dc("service3_min"), "service3_max": pick_dc("service3_max"),
                "service4_min": pick_dc("service4_min"), "service4_max": pick_dc("service4_max"),
            }
        elif args.niche == "peinture":
            pop = city.get("population", 0)
            region_name = city.get("region", "")
            if pop >= 50000:
                fb = {"service1_min": 3500, "service1_max": 12000, "service2_min": 3000, "service2_max": 10000,
                      "service3_min": 500, "service3_max": 2000, "service4_min": 600, "service4_max": 2500}
            elif pop >= 15000:
                fb = {"service1_min": 2800, "service1_max": 9500, "service2_min": 2400, "service2_max": 8000,
                      "service3_min": 400, "service3_max": 1600, "service4_min": 480, "service4_max": 2000}
            elif pop >= 5000:
                fb = {"service1_min": 2300, "service1_max": 7800, "service2_min": 2000, "service2_max": 6500,
                      "service3_min": 340, "service3_max": 1350, "service4_min": 400, "service4_max": 1650}
            else:
                fb = {"service1_min": 1900, "service1_max": 6400, "service2_min": 1650, "service2_max": 5400,
                      "service3_min": 280, "service3_max": 1100, "service4_min": 330, "service4_max": 1350}
            rp = peinture_region_prices.get(region_name, {})
            def pick_p(key): return rp.get(key) or fb[key]
            return {
                "population": pop,
                "service1_min": pick_p("service1_min"), "service1_max": pick_p("service1_max"),
                "service2_min": pick_p("service2_min"), "service2_max": pick_p("service2_max"),
                "service3_min": pick_p("service3_min"), "service3_max": pick_p("service3_max"),
                "service4_min": pick_p("service4_min"), "service4_max": pick_p("service4_max"),
            }
        elif args.niche == "agrandissement":
            pop = city.get("population", 0)
            if pop >= 50000:
                fb = {"service1_min": 45000, "service1_max": 150000, "service2_min": 30000, "service2_max": 90000,
                      "service3_min": 20000, "service3_max": 70000, "service4_min": 35000, "service4_max": 120000}
            elif pop >= 15000:
                fb = {"service1_min": 36900, "service1_max": 122999, "service2_min": 24600, "service2_max": 73800,
                      "service3_min": 16400, "service3_max": 57400, "service4_min": 28700, "service4_max": 98400}
            elif pop >= 5000:
                fb = {"service1_min": 31499, "service1_max": 105000, "service2_min": 21000, "service2_max": 62999,
                      "service3_min": 14000, "service3_max": 49000, "service4_min": 24500, "service4_max": 84000}
            else:
                fb = {"service1_min": 26100, "service1_max": 87000, "service2_min": 17400, "service2_max": 52200,
                      "service3_min": 11600, "service3_max": 40600, "service4_min": 20300, "service4_max": 69600}
            return {"population": pop, **fb}
        elif args.niche == "chauffage":
            pop = city.get("population", 0)
            if pop >= 50000:
                fb = {"service1_min": 4500, "service1_max": 16000, "service2_min": 3000, "service2_max": 12000,
                      "service3_min": 2500, "service3_max": 9000, "service4_min": 1800, "service4_max": 7000}
            elif pop >= 15000:
                fb = {"service1_min": 3690, "service1_max": 13120, "service2_min": 2460, "service2_max": 9840,
                      "service3_min": 2050, "service3_max": 7380, "service4_min": 1476, "service4_max": 5740}
            elif pop >= 5000:
                fb = {"service1_min": 3150, "service1_max": 11200, "service2_min": 2100, "service2_max": 8400,
                      "service3_min": 1750, "service3_max": 6300, "service4_min": 1260, "service4_max": 4900}
            else:
                fb = {"service1_min": 2610, "service1_max": 9280, "service2_min": 1739, "service2_max": 6959,
                      "service3_min": 1450, "service3_max": 5220, "service4_min": 1044, "service4_max": 4059}
            return {"population": pop, **fb}
        elif args.niche == "salledebain":
            pop = city.get("population", 0)
            region_name = city.get("region", "")
            # Niveau 3 — fallback population (config_salledebain.json tiers)
            if pop >= 50000:
                fb = {"service1_min": 3500, "service1_max": 12000, "service2_min": 8000, "service2_max": 28000,
                      "service3_min": 18000, "service3_max": 45000, "service4_min": 1500, "service4_max": 6000}
            elif pop >= 15000:
                fb = {"service1_min": 3000, "service1_max": 10000, "service2_min": 7000, "service2_max": 24000,
                      "service3_min": 15000, "service3_max": 38000, "service4_min": 1200, "service4_max": 5000}
            elif pop >= 5000:
                fb = {"service1_min": 2500, "service1_max": 8500, "service2_min": 6000, "service2_max": 20000,
                      "service3_min": 12000, "service3_max": 32000, "service4_min": 1000, "service4_max": 4000}
            else:
                fb = {"service1_min": 2000, "service1_max": 7000, "service2_min": 5000, "service2_max": 17000,
                      "service3_min": 10000, "service3_max": 26000, "service4_min": 900, "service4_max": 3500}
            # Niveau 2 — prix Perplexity par région
            rp = salledebain_region_prices.get(region_name, {})
            def pick_sb(key): return rp.get(key) or fb[key]
            return {
                "population": pop,
                "service1_min": pick_sb("service1_min"), "service1_max": pick_sb("service1_max"),
                "service2_min": pick_sb("service2_min"), "service2_max": pick_sb("service2_max"),
                "service3_min": pick_sb("service3_min"), "service3_max": pick_sb("service3_max"),
                "service4_min": pick_sb("service4_min"), "service4_max": pick_sb("service4_max"),
            }
        elif args.niche == "paysagement":
            pop = city.get("population", 0)
            region_name = city.get("region", "")
            if pop >= 50000:
                fb = {"service1_min": 5000, "service1_max": 45000, "service2_min": 800, "service2_max": 6500,
                      "service3_min": 1500, "service3_max": 12000, "service4_min": 12000, "service4_max": 55000}
            elif pop >= 15000:
                fb = {"service1_min": 4000, "service1_max": 35000, "service2_min": 650, "service2_max": 5500,
                      "service3_min": 1200, "service3_max": 10000, "service4_min": 10000, "service4_max": 45000}
            elif pop >= 5000:
                fb = {"service1_min": 3000, "service1_max": 25000, "service2_min": 500, "service2_max": 4500,
                      "service3_min": 900, "service3_max": 8000, "service4_min": 8000, "service4_max": 38000}
            else:
                fb = {"service1_min": 2500, "service1_max": 18000, "service2_min": 400, "service2_max": 3500,
                      "service3_min": 700, "service3_max": 6000, "service4_min": 6500, "service4_max": 30000}
            rp = {}
            for r_name, ctx_text in regional_context.items():
                if r_name == region_name and "---PRIX---" in ctx_text:
                    try:
                        for line in ctx_text.split("---PRIX---", 1)[1].strip().splitlines():
                            line = line.strip()
                            if line.startswith("{"):
                                parsed = json.loads(line)
                                required = {"service1_min", "service1_max", "service2_min", "service2_max",
                                            "service3_min", "service3_max", "service4_min", "service4_max"}
                                if required.issubset(parsed.keys()):
                                    rp = {k: int(v) for k, v in parsed.items() if k in required}
                                break
                    except Exception:
                        pass
            def pick_pay(key): return rp.get(key) or fb[key]
            return {
                "population": pop,
                "service1_min": pick_pay("service1_min"), "service1_max": pick_pay("service1_max"),
                "service2_min": pick_pay("service2_min"), "service2_max": pick_pay("service2_max"),
                "service3_min": pick_pay("service3_min"), "service3_max": pick_pay("service3_max"),
                "service4_min": pick_pay("service4_min"), "service4_max": pick_pay("service4_max"),
            }
        elif args.niche == "electricien":
            pop = city.get("population", 0)
            region_name = city.get("region", "")
            if pop >= 50000:
                fb = {"service1_min": 150, "service1_max": 1200, "service2_min": 1500, "service2_max": 6000,
                      "service3_min": 3500, "service3_max": 9000, "service4_min": 300, "service4_max": 2500}
            elif pop >= 15000:
                fb = {"service1_min": 120, "service1_max": 1000, "service2_min": 1200, "service2_max": 5000,
                      "service3_min": 3000, "service3_max": 7500, "service4_min": 250, "service4_max": 2000}
            elif pop >= 5000:
                fb = {"service1_min": 100, "service1_max": 900, "service2_min": 1000, "service2_max": 4500,
                      "service3_min": 2500, "service3_max": 6500, "service4_min": 200, "service4_max": 1800}
            else:
                fb = {"service1_min": 90, "service1_max": 800, "service2_min": 900, "service2_max": 4000,
                      "service3_min": 2000, "service3_max": 5500, "service4_min": 175, "service4_max": 1500}
            rp = {}
            for r_name, ctx_text in regional_context.items():
                if r_name == region_name and "---PRIX---" in ctx_text:
                    try:
                        for line in ctx_text.split("---PRIX---", 1)[1].strip().splitlines():
                            line = line.strip()
                            if line.startswith("{"):
                                parsed = json.loads(line)
                                required = {"service1_min", "service1_max", "service2_min", "service2_max",
                                            "service3_min", "service3_max", "service4_min", "service4_max"}
                                if required.issubset(parsed.keys()):
                                    rp = {k: int(v) for k, v in parsed.items() if k in required}
                                break
                    except Exception:
                        pass
            def pick_el(key): return rp.get(key) or fb[key]
            return {
                "population": pop,
                "service1_min": pick_el("service1_min"), "service1_max": pick_el("service1_max"),
                "service2_min": pick_el("service2_min"), "service2_max": pick_el("service2_max"),
                "service3_min": pick_el("service3_min"), "service3_max": pick_el("service3_max"),
                "service4_min": pick_el("service4_min"), "service4_max": pick_el("service4_max"),
            }
        elif args.niche == "portes-fenetres":
            pop = city.get("population", 0)
            region_name = city.get("region", "")
            if pop >= 50000:
                fb = {"service1_min": 800, "service1_max": 3500, "service2_min": 400, "service2_max": 2000,
                      "service3_min": 1200, "service3_max": 5000, "service4_min": 2500, "service4_max": 12000}
            elif pop >= 15000:
                fb = {"service1_min": 656, "service1_max": 2870, "service2_min": 328, "service2_max": 1640,
                      "service3_min": 983, "service3_max": 4100, "service4_min": 2050, "service4_max": 9840}
            elif pop >= 5000:
                fb = {"service1_min": 560, "service1_max": 2450, "service2_min": 280, "service2_max": 1400,
                      "service3_min": 840, "service3_max": 3500, "service4_min": 1750, "service4_max": 8400}
            else:
                fb = {"service1_min": 463, "service1_max": 2029, "service2_min": 231, "service2_max": 1160,
                      "service3_min": 696, "service3_max": 2900, "service4_min": 1450, "service4_max": 6959}
            rp = {}
            for r_name, ctx_text in regional_context.items():
                if r_name == region_name and "---PRIX---" in ctx_text:
                    try:
                        for line in ctx_text.split("---PRIX---", 1)[1].strip().splitlines():
                            line = line.strip()
                            if line.startswith("{"):
                                parsed = json.loads(line)
                                required = {"service1_min", "service1_max", "service2_min", "service2_max",
                                            "service3_min", "service3_max", "service4_min", "service4_max"}
                                if required.issubset(parsed.keys()):
                                    rp = {k: int(v) for k, v in parsed.items() if k in required}
                                break
                    except Exception:
                        pass
            def pick_pf(key): return rp.get(key) or fb[key]
            return {
                "population": pop,
                "service1_min": pick_pf("service1_min"), "service1_max": pick_pf("service1_max"),
                "service2_min": pick_pf("service2_min"), "service2_max": pick_pf("service2_max"),
                "service3_min": pick_pf("service3_min"), "service3_max": pick_pf("service3_max"),
                "service4_min": pick_pf("service4_min"), "service4_max": pick_pf("service4_max"),
            }
        elif args.niche == "fosseseptique":
            pop = city.get("population", 0)
            region_name = city.get("region", "")
            if pop >= 50000:
                fb = {"service1_min": 12000, "service1_max": 30000, "service2_min": 8000, "service2_max": 22000,
                      "service3_min": 250, "service3_max": 550, "service4_min": 300, "service4_max": 700}
            elif pop >= 15000:
                fb = {"service1_min": 10000, "service1_max": 25000, "service2_min": 7000, "service2_max": 18000,
                      "service3_min": 220, "service3_max": 480, "service4_min": 250, "service4_max": 600}
            elif pop >= 5000:
                fb = {"service1_min": 9000, "service1_max": 22000, "service2_min": 6000, "service2_max": 16000,
                      "service3_min": 190, "service3_max": 430, "service4_min": 220, "service4_max": 550}
            else:
                fb = {"service1_min": 8000, "service1_max": 18000, "service2_min": 5500, "service2_max": 14000,
                      "service3_min": 170, "service3_max": 380, "service4_min": 200, "service4_max": 480}
            rp = {}
            for r_name, ctx_text in regional_context.items():
                if r_name == region_name and "---PRIX---" in ctx_text:
                    try:
                        for line in ctx_text.split("---PRIX---", 1)[1].strip().splitlines():
                            line = line.strip()
                            if line.startswith("{"):
                                parsed = json.loads(line)
                                required = {"service1_min", "service1_max", "service2_min", "service2_max",
                                            "service3_min", "service3_max", "service4_min", "service4_max"}
                                if required.issubset(parsed.keys()):
                                    rp = {k: int(v) for k, v in parsed.items() if k in required}
                                break
                    except Exception:
                        pass
            def pick_fs(key): return rp.get(key) or fb[key]
            return {
                "population": pop,
                "service1_min": pick_fs("service1_min"), "service1_max": pick_fs("service1_max"),
                "service2_min": pick_fs("service2_min"), "service2_max": pick_fs("service2_max"),
                "service3_min": pick_fs("service3_min"), "service3_max": pick_fs("service3_max"),
                "service4_min": pick_fs("service4_min"), "service4_max": pick_fs("service4_max"),
            }
        elif args.niche == "nettoyage-conduits":
            pop = city.get("population", 0)
            region_name = city.get("region", "")
            if pop >= 50000:
                fb = {"service1_min": 250, "service1_max": 600, "service2_min": 150, "service2_max": 400,
                      "service3_min": 350, "service3_max": 800, "service4_min": 200, "service4_max": 500}
            elif pop >= 15000:
                fb = {"service1_min": 205, "service1_max": 491, "service2_min": 122, "service2_max": 328,
                      "service3_min": 287, "service3_max": 656, "service4_min": 164, "service4_max": 410}
            elif pop >= 5000:
                fb = {"service1_min": 175, "service1_max": 420, "service2_min": 105, "service2_max": 280,
                      "service3_min": 244, "service3_max": 560, "service4_min": 140, "service4_max": 350}
            else:
                fb = {"service1_min": 145, "service1_max": 348, "service2_min": 87, "service2_max": 231,
                      "service3_min": 203, "service3_max": 463, "service4_min": 115, "service4_max": 290}
            rp = {}
            for r_name, ctx_text in regional_context.items():
                if r_name == region_name and "---PRIX---" in ctx_text:
                    try:
                        for line in ctx_text.split("---PRIX---", 1)[1].strip().splitlines():
                            line = line.strip()
                            if line.startswith("{"):
                                parsed = json.loads(line)
                                required = {"service1_min", "service1_max", "service2_min", "service2_max",
                                            "service3_min", "service3_max", "service4_min", "service4_max"}
                                if required.issubset(parsed.keys()):
                                    rp = {k: int(v) for k, v in parsed.items() if k in required}
                                break
                    except Exception:
                        pass
            def pick_nc(key): return rp.get(key) or fb[key]
            return {
                "population": pop,
                "service1_min": pick_nc("service1_min"), "service1_max": pick_nc("service1_max"),
                "service2_min": pick_nc("service2_min"), "service2_max": pick_nc("service2_max"),
                "service3_min": pick_nc("service3_min"), "service3_max": pick_nc("service3_max"),
                "service4_min": pick_nc("service4_min"), "service4_max": pick_nc("service4_max"),
            }
        elif args.niche == "calfeutrage":
            pop = city.get("population", 0)
            region_name = city.get("region", "")
            if pop >= 50000:
                fb = {"service1_min": 800, "service1_max": 3500, "service2_min": 350, "service2_max": 1500,
                      "service3_min": 250, "service3_max": 900, "service4_min": 400, "service4_max": 1800}
            elif pop >= 15000:
                fb = {"service1_min": 650, "service1_max": 2800, "service2_min": 280, "service2_max": 1200,
                      "service3_min": 200, "service3_max": 750, "service4_min": 320, "service4_max": 1500}
            elif pop >= 5000:
                fb = {"service1_min": 550, "service1_max": 2200, "service2_min": 230, "service2_max": 1000,
                      "service3_min": 160, "service3_max": 600, "service4_min": 260, "service4_max": 1200}
            else:
                fb = {"service1_min": 450, "service1_max": 1800, "service2_min": 180, "service2_max": 800,
                      "service3_min": 130, "service3_max": 500, "service4_min": 220, "service4_max": 950}
            rp = {}
            for r_name, ctx_text in regional_context.items():
                if r_name == region_name and "---PRIX---" in ctx_text:
                    try:
                        for line in ctx_text.split("---PRIX---", 1)[1].strip().splitlines():
                            line = line.strip()
                            if line.startswith("{"):
                                parsed = json.loads(line)
                                required = {"service1_min", "service1_max", "service2_min", "service2_max",
                                            "service3_min", "service3_max", "service4_min", "service4_max"}
                                if required.issubset(parsed.keys()):
                                    rp = {k: int(v) for k, v in parsed.items() if k in required}
                                break
                    except Exception:
                        pass
            def pick_calf(key): return rp.get(key) or fb[key]
            return {
                "population": pop,
                "service1_min": pick_calf("service1_min"), "service1_max": pick_calf("service1_max"),
                "service2_min": pick_calf("service2_min"), "service2_max": pick_calf("service2_max"),
                "service3_min": pick_calf("service3_min"), "service3_max": pick_calf("service3_max"),
                "service4_min": pick_calf("service4_min"), "service4_max": pick_calf("service4_max"),
            }
        # Generic research-driven niche handler
        elif research_price_tiers:
            pop = city.get("population", 0)
            region_name = city.get("region", "")
            if pop >= 50000:
                tier = "grande_ville"
            elif pop >= 15000:
                tier = "moyenne_ville"
            elif pop >= 5000:
                tier = "petite_ville"
            else:
                tier = "village"
            fb = research_price_tiers.get(tier, research_price_tiers.get("grande_ville", {}))
            rp = research_region_prices.get(region_name, {})
            def pick_r(key): return rp.get(key) or fb.get(key, 0)
            return {
                "population": pop,
                "service1_min": pick_r("service1_min"), "service1_max": pick_r("service1_max"),
                "service2_min": pick_r("service2_min"), "service2_max": pick_r("service2_max"),
                "service3_min": pick_r("service3_min"), "service3_max": pick_r("service3_max"),
                "service4_min": pick_r("service4_min"), "service4_max": pick_r("service4_max"),
            }
        return {}

    CHAUFFAGE_SECTION7 = """

---
SECTION 7 — Coût mensuel de chauffage à {ville} (grande ville uniquement)
<h2> accrocheur sur le coût réel mensuel de chauffage à {ville}
<p> de 180-220 mots : en utilisant les degrés-jours de chauffage de {region} et les tarifs Hydro-Québec actuels (tarif D résidentiel), calcule le coût mensuel réaliste pour une maison de référence de 1 500 pi² (140 m²) à {ville} selon chaque système. Explique pourquoi les coûts varient selon la rigueur du climat de {region} vs la moyenne québécoise. Mentionne l'impact des thermopompes haute performance (SEER 18+ / COP 3.5+) sur la facture hivernale. Pour les montants mensuels, utilise <strong class="text-orange-600">X $</strong>.
Suivi d'un tableau (thead style="background:#ea580c;color:#fff") : Système | kWh/mois (déc-fév) | Coût mensuel hiver | Coût mensuel mi-saison | Coût annuel estimé | Économie vs plinthes
Lignes : Thermopompe murale SEER 18 / Thermopompe centrale SEER 16 / Fournaise électrique / Fournaise gaz naturel / Fournaise propane / Plinthes électriques (référence)
Note : les chiffres doivent être cohérents avec le contexte régional de {region} (degrés-jours, accès gaz naturel, etc.)
"""

    def process_city(args_tuple):
        i, city = args_tuple
        slug = slugify(city["ville"])
        region_slug = slugify(city["region"])
        key = f"{slug}|{region_slug}"
        raw_context = regional_context.get(city["region"], "Région du Québec.")
        # Striper le bloc PRIX pour ne passer que le texte narratif au prompt Claude
        context = raw_context.split("---PRIX---", 1)[0].strip() if "---PRIX---" in raw_context else raw_context
        start_angle = (i % 6) + 1
        extra_kwargs = build_extra_kwargs(city)

        try:
            user_prompt = user_tpl.format(
                ville=city["ville"], region=city["region"],
                context=context, start_angle=start_angle, **extra_kwargs,
            )
        except KeyError:
            user_prompt = user_tpl.format(
                ville=city["ville"], region=city["region"], context=context,
            )

        # Section 7 — grandes villes chauffage uniquement
        pop = extra_kwargs.get("population", 0)
        if args.niche == "chauffage" and pop >= 50000:
            user_prompt += CHAUFFAGE_SECTION7.format(ville=city["ville"], region=city["region"])

        openai_key = os.environ.get("OPENAI_API_KEY", "")
        use_openai = bool(openai_key)
        model_used = "gpt-5.4-nano" if use_openai else "claude-haiku-4-5"
        sections_count = 7 if (args.niche == "chauffage" and pop >= 50000) else 6

        for attempt in range(5):
            try:
                if use_openai:
                    payload = json.dumps({
                        "model": "gpt-5.4-nano",
                        "max_completion_tokens": max_tokens,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user_prompt},
                        ],
                    }).encode("utf-8")
                    req = _urllib_request.Request(
                        "https://api.openai.com/v1/chat/completions",
                        data=payload,
                        headers={"Content-Type": "application/json", "Authorization": f"Bearer {openai_key}"},
                        method="POST",
                    )
                    with _urllib_request.urlopen(req, timeout=120) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                    text = data["choices"][0]["message"]["content"].strip()
                else:
                    msg = client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=max_tokens,
                        system=system,
                        messages=[{"role": "user", "content": user_prompt}],
                    )
                    text = msg.content[0].text.strip()
                if text.startswith("```"):
                    text = re.sub(r"^```[a-z]*\n?", "", text)
                    text = re.sub(r"\n?```$", "", text)
                    text = text.strip()
                # Strip full HTML wrapper if AI returned a complete page
                if text.lower().startswith(("<!doctype", "<html")):
                    m = re.search(r"<body[^>]*>(.*?)</body>", text, re.DOTALL | re.IGNORECASE)
                    if m:
                        text = m.group(1).strip()
                    else:
                        text = re.sub(r"<!doctype[^>]*>", "", text, flags=re.IGNORECASE)
                        text = re.sub(r"<head[^>]*>.*?</head>", "", text, flags=re.DOTALL | re.IGNORECASE)
                        text = re.sub(r"</?html[^>]*>|</?body[^>]*>", "", text, flags=re.IGNORECASE)
                        text = text.strip()

                with lock:
                    output[key] = text
                    done_count[0] += 1
                    n = done_count[0]
                    if n <= 3 or n % 10 == 0:
                        print(f"[{n}/{len(cities_todo)}] {city['ville']} [{model_used} · {sections_count}s]: {text[:50]}...")
                    if n % 10 == 0:
                        output_path.write_text(
                            json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
                        )
                        print(f"  → Checkpoint ({len(output)} villes)")
                return key, True

            except Exception as e:
                err_str = str(e)
                is_overloaded = "529" in err_str or "overloaded" in err_str.lower()
                if is_overloaded and attempt < 4:
                    wait = 30 * (2 ** attempt)
                    print(f"  OVERLOADED {city['ville']} (tentative {attempt+1}/5) — attente {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"  ERR {city['ville']}: {e}")
                    with lock:
                        output[key] = ""
                    return key, False

    workers = args.workers
    print(f"Workers : {workers}")
    if workers == 1:
        for item in cities_todo:
            process_city(item)
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(process_city, item): item for item in cities_todo}
            for future in as_completed(futures):
                future.result()

    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nTerminé ! {len(output)} villes → {output_path}")


if __name__ == "__main__":
    main()
