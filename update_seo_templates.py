#!/usr/bin/env python3
"""Add 10 title templates + 6 desc templates with price vars to all 8 QC V3 configs."""
import json, os

BASE = os.path.join(os.path.dirname(__file__), '..', 'engine_qc')

SEO = {
    'config_cloture.json': {
        'title_templates': [
            "Cloture {ville} — Prix {annee} & Soumissions Gratuites | {site_name}",
            "Prix Cloture {ville} {annee} : Bois, Vinyle, Aluminium",
            "Installateur de Cloture a {ville} — Experts Certifies | {site_name}",
            "{ville} : Cloture {annee} — Jusqu'a 5 Soumissions Gratuites",
            "Cloture {ville} {annee} — Bois des {service1_min}$ | {site_name}",
            "Soumission Cloture {ville} — Comparez 5 Installateurs Locaux",
            "{ville} Cloture {annee} : Bois, Vinyle, Aluminium, Maille | {site_name}",
            "Cloture {ville} : Obtenez 5 Prix d'Installateurs Certifies {annee}",
            "{ville} : Meilleur Prix Cloture {annee} — Reponse en 24h | {site_name}",
            "Prix Installation Cloture {ville} — Bois des {service1_min}$, Vinyle des {service2_min}$",
        ],
        'desc_templates': [
            "Comparez jusqu'a 5 soumissions gratuites d'installateurs de clotures a {ville}. Bois, vinyle, aluminium, maille. Reponse en 24h.",
            "Installation de cloture professionnelle a {ville} — bois, vinyle, aluminium. Experts certifies. Devis gratuit.",
            "Prix cloture {ville} {annee} : bois des {service1_min}$, vinyle des {service2_min}$. Comparez 5 soumissions locales.",
            "Vous cherchez un installateur de cloture a {ville} ? Obtenez 5 soumissions gratuites de pros verifies. Reponse rapide.",
            "Cloture bois des {service1_min}$ ou vinyle des {service2_min}$ a {ville} — 5 soumissions gratuites d'experts locaux certifies.",
            "Besoin d'une cloture a {ville} ? Nos specialistes certifies vous offrent 5 devis gratuits en moins de 24 heures.",
        ],
    },
    'config_chauffage.json': {
        'title_templates': [
            "Chauffage {ville} — Prix {annee} & Soumissions Gratuites | {site_name}",
            "Prix Fournaise & Thermopompe {ville} {annee} | {site_name}",
            "Installation Chauffage {ville} — Experts Certifies {annee}",
            "{ville} : Fournaise & Thermopompe {annee} — 5 Soumissions Gratuites",
            "Chauffage {ville} {annee} — Fournaise des {service1_min}$ | {site_name}",
            "Soumission Chauffage {ville} — Comparez 5 Techniciens Locaux",
            "Remplacement Fournaise {ville} {annee} : Prix & Experts | {site_name}",
            "{ville} : Meilleur Prix Chauffage {annee} — Reponse en 24h | {site_name}",
            "Thermopompe {ville} {annee} — Des {service2_min}$ | Subventions Disponibles",
            "Prix Installation Fournaise {ville} — Des {service1_min}$, Thermopompe des {service2_min}$",
        ],
        'desc_templates': [
            "Comparez jusqu'a 5 soumissions gratuites de techniciens en chauffage a {ville}. Fournaise des {service1_min}$. Reponse en 24h.",
            "Installation fournaise et thermopompe a {ville} — techniciens certifies, subventions Renoclimat disponibles. Devis gratuit.",
            "Prix chauffage {ville} {annee} : fournaise des {service1_min}$, thermopompe des {service2_min}$. Comparez 5 soumissions.",
            "Remplacement de fournaise a {ville} ? Obtenez 5 soumissions gratuites de techniciens verifies. Reponse rapide garantie.",
            "Fournaise des {service1_min}$ ou thermopompe des {service2_min}$ a {ville} — 5 soumissions gratuites, subventions incluses.",
            "Besoin d'un nouveau systeme de chauffage a {ville} ? Comparez les prix et economisez avec les subventions Hydro-Quebec.",
        ],
    },
    'config_beton.json': {
        'title_templates': [
            "Beton {ville} — Prix {annee} & Soumissions Gratuites | {site_name}",
            "Prix Dalle Beton {ville} {annee} : Entree, Patio, Garage",
            "Entrepreneur Beton {ville} — Experts Certifies {annee} | {site_name}",
            "{ville} : Beton {annee} — Jusqu'a 5 Soumissions Gratuites",
            "Beton {ville} {annee} — Dalle des {service1_min}$ | {site_name}",
            "Soumission Beton {ville} — Comparez 5 Entrepreneurs Locaux",
            "Dalle & Beton Estampe {ville} {annee} : Prix & Experts | {site_name}",
            "{ville} : Meilleur Prix Beton {annee} — Reponse en 24h | {site_name}",
            "Coulage Beton {ville} {annee} — Entree de Garage des {service1_min}$",
            "Prix Beton Estampe {ville} — Des {service2_min}$, Dalle Standard des {service1_min}$",
        ],
        'desc_templates': [
            "Comparez jusqu'a 5 soumissions gratuites d'entrepreneurs en beton a {ville}. Dalle des {service1_min}$. Reponse en 24h.",
            "Coulage de beton professionnel a {ville} — entree de garage, patio, fondation. Entrepreneurs certifies. Devis gratuit.",
            "Prix beton {ville} {annee} : dalle des {service1_min}$, beton estampe des {service2_min}$. Comparez 5 soumissions.",
            "Vous cherchez un entrepreneur en beton a {ville} ? Obtenez 5 soumissions gratuites de pros certifies RBQ.",
            "Dalle beton des {service1_min}$ ou beton estampe des {service2_min}$ a {ville} — 5 soumissions gratuites d'experts.",
            "Besoin de beton a {ville} ? Nos entrepreneurs certifies RBQ vous offrent 5 devis gratuits en moins de 24 heures.",
        ],
    },
    'config_portes-fenetres.json': {
        'title_templates': [
            "Portes & Fenetres {ville} — Prix {annee} & Soumissions | {site_name}",
            "Prix Fenetres {ville} {annee} : PVC, Bois, Aluminium | {site_name}",
            "Installation Fenetres {ville} — Experts Certifies {annee}",
            "{ville} : Fenetres & Portes {annee} — 5 Soumissions Gratuites",
            "Fenetres {ville} {annee} — PVC des {service1_min}$ par Unite | {site_name}",
            "Soumission Fenetres {ville} — Comparez 5 Poseurs Locaux",
            "Remplacement Fenetres {ville} {annee} : ENERGY STAR | {site_name}",
            "{ville} : Meilleur Prix Fenetres {annee} — Reponse en 24h | {site_name}",
            "Fenetres PVC {ville} {annee} — Des {service1_min}$ | Subventions Renoclimat",
            "Prix Portes & Fenetres {ville} — PVC des {service1_min}$, Triple Vitrage des {service3_min}$",
        ],
        'desc_templates': [
            "Comparez jusqu'a 5 soumissions gratuites de poseurs de fenetres a {ville}. PVC des {service1_min}$ par unite. Reponse en 24h.",
            "Remplacement de fenetres et portes a {ville} — PVC, bois, aluminium. ENERGY STAR. Subventions Renoclimat. Devis gratuit.",
            "Prix fenetres {ville} {annee} : PVC des {service1_min}$, triple vitrage des {service3_min}$. Comparez 5 soumissions locales.",
            "Vous cherchez un poseur de fenetres a {ville} ? Obtenez 5 soumissions gratuites de pros ENERGY STAR verifies.",
            "Fenetres PVC des {service1_min}$ a {ville} — ENERGY STAR, subventions jusqu'a 1 500$, 5 soumissions gratuites.",
            "Besoin de nouvelles fenetres a {ville} ? Nos experts certifies gèrent subventions Renoclimat et pose. Devis gratuit.",
        ],
    },
    'config_agrandissement.json': {
        'title_templates': [
            "Agrandissement {ville} — Prix {annee} & Soumissions Gratuites | {site_name}",
            "Prix Agrandissement Maison {ville} {annee} | {site_name}",
            "Entrepreneur Agrandissement {ville} — Experts Certifies {annee}",
            "{ville} : Agrandissement {annee} — 5 Soumissions Gratuites",
            "Agrandissement {ville} {annee} — Des {service1_min}$ le pi2 | {site_name}",
            "Soumission Agrandissement {ville} — Comparez 5 Entrepreneurs",
            "Extension Maison {ville} {annee} : Plans & Permis Inclus | {site_name}",
            "{ville} : Meilleur Prix Agrandissement {annee} | {site_name}",
            "Ajout de Piece {ville} {annee} — Des {service1_min}$ le pi2 | {site_name}",
            "Prix Agrandissement {ville} — Ajout de Piece des {service1_min}$, 2e Etage des {service2_min}$",
        ],
        'desc_templates': [
            "Comparez jusqu'a 5 soumissions gratuites d'entrepreneurs en agrandissement a {ville}. Des {service1_min}$ le pi2. Reponse en 24h.",
            "Agrandissement de maison a {ville} — ajout de piece, extension arriere, deuxieme etage. Entrepreneurs certifies RBQ.",
            "Prix agrandissement {ville} {annee} : des {service1_min}$ le pi2 tout inclus. Plans, permis. Comparez 5 soumissions.",
            "Vous voulez agrandir votre maison a {ville} ? Obtenez 5 soumissions gratuites d'entrepreneurs verifies et certifies.",
            "Extension maison des {service1_min}$ le pi2 a {ville} — permis inclus, entrepreneurs certifies RBQ, devis gratuit.",
            "Agrandir votre maison a {ville} ? Nos entrepreneurs certifies gèrent permis, plans et construction. Devis gratuit.",
        ],
    },
    'config_ceramique.json': {
        'title_templates': [
            "Ceramique {ville} — Prix {annee} & Soumissions Gratuites | {site_name}",
            "Prix Pose Ceramique {ville} {annee} : Plancher, Douche, Mur",
            "Poseur de Ceramique {ville} — Experts Certifies {annee} | {site_name}",
            "{ville} : Ceramique {annee} — 5 Soumissions Gratuites",
            "Ceramique {ville} {annee} — Pose des {service1_min}$ le pi2 | {site_name}",
            "Soumission Ceramique {ville} — Comparez 5 Carreleurs Locaux",
            "Carrelage & Ceramique {ville} {annee} : Plancher, Salle de Bain",
            "{ville} : Meilleur Prix Ceramique {annee} — Reponse en 24h",
            "Pose Ceramique {ville} {annee} — Des {service1_min}$ le pi2 | {site_name}",
            "Prix Ceramique {ville} — Plancher des {service1_min}$ pi2, Porcelaine des {service2_min}$ pi2",
        ],
        'desc_templates': [
            "Comparez jusqu'a 5 soumissions gratuites de poseurs de ceramique a {ville}. Pose des {service1_min}$ le pi2. Reponse en 24h.",
            "Pose de ceramique professionnelle a {ville} — plancher, salle de bain, cuisine, douche. Carreleurs certifies. Devis gratuit.",
            "Prix ceramique {ville} {annee} : pose des {service1_min}$, porcelaine des {service2_min}$ le pi2. Comparez 5 soumissions.",
            "Vous cherchez un poseur de ceramique a {ville} ? Obtenez 5 soumissions gratuites de carreleurs verifies. Reponse rapide.",
            "Ceramique des {service1_min}$ le pi2 a {ville} — plancher, salle de bain, douche. 5 soumissions gratuites d'experts.",
            "Besoin d'un carreleur a {ville} ? Nos experts certifies posent ceramique et porcelaine. Devis gratuit en 24h.",
        ],
    },
    'config_toiture-plate.json': {
        'title_templates': [
            "Toit Plat {ville} — Prix {annee} & Soumissions Gratuites | {site_name}",
            "Prix Toit Plat {ville} {annee} : TPO, EPDM, Bitume | {site_name}",
            "Refection Toit Plat {ville} — Experts Certifies {annee}",
            "{ville} : Toit Plat {annee} — 5 Soumissions Gratuites",
            "Toit Plat {ville} {annee} — Membrane des {service1_min}$ | {site_name}",
            "Soumission Toit Plat {ville} — Comparez 5 Couvreurs Locaux",
            "Membrane Toit Plat {ville} {annee} : TPO, EPDM | {site_name}",
            "{ville} : Meilleur Prix Toit Plat {annee} — Reponse en 24h",
            "Refection Toit Plat {ville} {annee} — TPO des {service1_min}$ | {site_name}",
            "Prix Toit Plat {ville} — TPO des {service1_min}$, EPDM des {service2_min}$ | {site_name}",
        ],
        'desc_templates': [
            "Comparez jusqu'a 5 soumissions gratuites de couvreurs en toit plat a {ville}. TPO des {service1_min}$. Reponse en 24h.",
            "Refection de toit plat a {ville} — membrane TPO, EPDM, bitume. Couvreurs certifies RBQ, garantie fabricant. Devis gratuit.",
            "Prix toit plat {ville} {annee} : TPO des {service1_min}$, EPDM des {service2_min}$. Comparez 5 soumissions de couvreurs.",
            "Vous cherchez un couvreur pour toit plat a {ville} ? Obtenez 5 soumissions gratuites de pros certifies RBQ.",
            "Membrane TPO des {service1_min}$ ou EPDM des {service2_min}$ a {ville} — 5 soumissions gratuites, garantie 20 ans.",
            "Besoin de refaire votre toit plat a {ville} ? Couvreurs certifies RBQ, 5 devis gratuits en 24 heures.",
        ],
    },
    'config_nettoyage-conduits.json': {
        'title_templates': [
            "Nettoyage Conduits {ville} — Prix {annee} & Soumissions | {site_name}",
            "Prix Nettoyage Conduits Ventilation {ville} {annee} | {site_name}",
            "Nettoyage Conduits {ville} — Experts Certifies {annee}",
            "{ville} : Nettoyage Conduits {annee} — 5 Soumissions Gratuites",
            "Conduits {ville} {annee} — Nettoyage des {service1_min}$ | {site_name}",
            "Soumission Nettoyage Conduits {ville} — Comparez 5 Techniciens",
            "Ventilation & Conduits {ville} {annee} : Qualite de l'Air | {site_name}",
            "{ville} : Meilleur Prix Nettoyage Conduits {annee} | {site_name}",
            "Nettoyage Conduits {ville} {annee} — Maison des {service1_min}$ | {site_name}",
            "Prix Nettoyage Conduits {ville} — Maison des {service1_min}$, Fournaise des {service2_min}$",
        ],
        'desc_templates': [
            "Comparez jusqu'a 5 soumissions gratuites de techniciens en nettoyage de conduits a {ville}. Des {service1_min}$. Reponse en 24h.",
            "Nettoyage de conduits de ventilation a {ville} — inspection video, aspiration industrielle. Techniciens certifies. Devis gratuit.",
            "Prix nettoyage conduits {ville} {annee} : maison des {service1_min}$. Comparez 5 soumissions de techniciens locaux.",
            "Vous cherchez un technicien en nettoyage de conduits a {ville} ? Obtenez 5 soumissions gratuites de pros verifies.",
            "Conduits des {service1_min}$ a {ville} — inspection video incluse, aspiration industrielle, rapport complet. Devis gratuit.",
            "Ameliorez la qualite de l'air a {ville} — nettoyage professionnel de conduits par techniciens certifies. Devis gratuit.",
        ],
    },
}

updated = []
for filename, seo_data in SEO.items():
    path = os.path.join(BASE, filename)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data['seo']['title_templates'] = seo_data['title_templates']
    data['seo']['desc_templates'] = seo_data['desc_templates']
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    updated.append(filename)
    print(f'{filename}: {len(seo_data["title_templates"])} titres, {len(seo_data["desc_templates"])} descs')

print(f'\nDone: {len(updated)}/8')
