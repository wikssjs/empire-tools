"""
Generate 13 new V3 config JSON files (8 QC + 5 EN).
Run from Empire-PSEO root: python tools/create_v3_configs.py
"""
import json, os, copy

BASE = r"C:/Users/bellj/OneDrive/Desktop/Programmatic seo/Empire-PSEO"

# ─── SHARED BOILERPLATE ───────────────────────────────────────────────────────
SECTION_ORDER = [
    ["reassurance","prices","services","faq"],
    ["prices","reassurance","services","faq"],
    ["reassurance","services","faq","prices"],
    ["services","reassurance","prices","faq"],
]
DEPLOY = {"target": "netlify", "clean_urls": True}
CSV    = {"file": "MUN.csv", "col_city": "munnom", "col_region": "regadm", "col_population": "mpopul"}
PERF   = {"max_workers": 12}
SP     = {"min":4,"max":16,"min_petite":9,"max_petite":30,"min_moyenne":22,"max_moyenne":70,"min_grande":50,"max_grande":140}
PREMIUM_CITIES = [
    "Montreal","Quebec","Laval","Gatineau","Longueuil","Sherbrooke","Saguenay",
    "Levis","Trois-Rivieres","Terrebonne","Brossard","Saint-Jerome","Drummondville",
    "Granby","Blainville","Repentigny","Saint-Hyacinthe","Mirabel","Chateauguay",
    "Mascouche","Rimouski","Saint-Eustache","Sorel-Tracy","Victoriaville",
    "Sept-Iles","Rouyn-Noranda"
]
IMAGES_BASE = {
    "use_local": False,
    "local_pool": [],
    "pexels_pool": [
        "https://images.pexels.com/photos/3815588/pexels-photo-3815588.jpeg?auto=compress&cs=tinysrgb&w=1200&h=600&fit=crop",
        "https://images.pexels.com/photos/2219024/pexels-photo-2219024.jpeg?auto=compress&cs=tinysrgb&w=1200&h=600&fit=crop",
        "https://images.pexels.com/photos/1109541/pexels-photo-1109541.jpeg?auto=compress&cs=tinysrgb&w=1200&h=600&fit=crop",
        "https://images.pexels.com/photos/5582867/pexels-photo-5582867.jpeg?auto=compress&cs=tinysrgb&w=1200&h=600&fit=crop",
        "https://images.pexels.com/photos/5025639/pexels-photo-5025639.jpeg?auto=compress&cs=tinysrgb&w=1200&h=600&fit=crop",
    ]
}

def make_images(alt_templates):
    d = copy.deepcopy(IMAGES_BASE)
    d["alt_templates"] = alt_templates
    return d

def make_prices(s1min,s1max,s2min,s2max,s3min,s3max,s4min,s4max):
    factor = {"grande_ville":(50000,1.0),"moyenne_ville":(15000,0.82),"petite_ville":(5000,0.70),"village":(0,0.58)}
    out = {}
    for tier,(seuil,f) in factor.items():
        out[tier] = {
            "seuil": seuil,
            "service1_min": int(s1min*f), "service1_max": int(s1max*f),
            "service2_min": int(s2min*f), "service2_max": int(s2max*f),
            "service3_min": int(s3min*f), "service3_max": int(s3max*f),
            "service4_min": int(s4min*f), "service4_max": int(s4max*f),
        }
    return out

def qc_authority(ville_keyword):
    return [
        {"url":"https://fr.wikipedia.org/wiki/{ville}","ancre":"{ville} — Wikipedia",
         "hook":f"Informations sur {{ville}} : histoire, population et contexte regional pertinent pour vos projets de {ville_keyword}."},
        {"url":"https://www.rbq.gouv.qc.ca/","ancre":"Regie du batiment du Quebec — Licences RBQ",
         "hook":f"La RBQ encadre les entrepreneurs en {ville_keyword} au Quebec. Verifiez la licence de votre entrepreneur avant de signer un contrat."},
        {"url":"https://www.cnesst.gouv.qc.ca/fr","ancre":"CNESST — Sante et securite en construction",
         "hook":f"Normes quebecoises de securite pour les travailleurs en {ville_keyword}. Assurez-vous que votre entrepreneur respecte les regles CNESST."},
        {"url":"https://www.apchq.com/","ancre":"APCHQ — Association professionnelle des constructeurs",
         "hook":f"L'APCHQ regroupe les entrepreneurs professionnels en renovation et construction au Quebec, dont les specialistes en {ville_keyword}."},
        {"url":"https://www.mamh.gouv.qc.ca/","ancre":"MAMH — Reglements municipaux et permis",
         "hook":f"Certains travaux de {ville_keyword} requierent un permis municipal a {{ville}}. Consultez les exigences locales avant de commencer."},
    ]

def qc_network(niche_slug, current_domain):
    """Generic sister sites for any QC niche."""
    return {
        "sister_sites": [
            {
                "url_format": f"https://experts-excavation.ca/{{slug}}",
                "ancres": ["Excavation {ville}", "Entrepreneur en excavation {ville}"],
                "hook": "Travaux d'excavation et terrassement a {ville} — demandez vos soumissions gratuites."
            },
            {
                "url_format": f"https://expertcalfeutrage.ca/{{slug}}",
                "ancres": ["Calfeutrage {ville}", "Expert calfeutrage {ville}"],
                "hook": "Calfeutrage professionnel a {ville} — fenetres, portes, fondation."
            },
        ]
    }

def four_step_form_qc(service_label, options_step1):
    return {
        "netlify_name": f"soumission-{service_label.lower().replace(' ','-').replace('é','e').replace('è','e').replace('â','a').replace('ô','o').replace('î','i').replace('ê','e').replace('û','u').replace('à','a')}",
        "submit_text": "Recevoir mes soumissions gratuites",
        "confirmation_title": "Demande recue !",
        "confirmation_body": f"Nos experts en {service_label.lower()} a <strong>{{ville}}</strong> vous contacteront dans les <strong>24 prochaines heures</strong>.",
        "confirmation_stats": [
            {"value":"24h","label":"Reponse max"},
            {"value":"100%","label":"Gratuit"},
            {"value":"5","label":"Soumissions"},
        ],
        "steps": [
            {
                "title": "Type de projet",
                "button_text": "Continuer",
                "fields": [{"type":"radio_cards","name":"type-projet","label":f"Quel type de {service_label.lower()} ?","required":True,"error_id":"projet-error","options":options_step1}]
            },
            {
                "title": "Votre propriete",
                "button_text": "Continuer",
                "fields": [
                    {"type":"select","name":"type-propriete","label":"Type de propriete","required":True,"options":[
                        {"value":"maison","label":"Maison unifamiliale"},
                        {"value":"condo","label":"Condo / Appartement"},
                        {"value":"multi","label":"Duplex / Triplex / Plex"},
                        {"value":"commercial","label":"Local commercial / Bureau"},
                        {"value":"chalet","label":"Chalet / Villegiature"},
                    ]},
                    {"type":"select","name":"anciennete","label":"Annee de construction approximative","required":True,"options":[
                        {"value":"avant-1980","label":"Avant 1980"},
                        {"value":"1980-2000","label":"1980 a 2000"},
                        {"value":"2000-2015","label":"2000 a 2015"},
                        {"value":"apres-2015","label":"Apres 2015"},
                        {"value":"inconnue","label":"Je ne sais pas"},
                    ]},
                ]
            },
            {
                "title": "Delai souhaite",
                "button_text": "Continuer",
                "fields": [{"type":"radio_cards","name":"delai","label":"Quand souhaitez-vous les travaux ?","required":True,"error_id":"delai-error","options":[
                    {"value":"urgent","emoji":"🚨","label":"Des que possible"},
                    {"value":"printemps","emoji":"🌸","label":"Ce printemps"},
                    {"value":"ete","emoji":"☀️","label":"Cet ete"},
                    {"value":"planifie","emoji":"📅","label":"Je planifie"},
                ]}]
            },
            {
                "title": "Vos coordonnees",
                "button_text": None,
                "fields": [
                    {"type":"text","name":"nom","label":"Prenom et nom","placeholder":"Jean Tremblay","required":True},
                    {"type":"email","name":"courriel","label":"Courriel","placeholder":"jean@exemple.com","required":True},
                    {"type":"tel","name":"telephone","label":"Telephone","placeholder":"514 000-0000","required":True},
                ]
            }
        ]
    }

# ─── QC NICHE DEFINITIONS ─────────────────────────────────────────────────────
QC_NICHES = [
    {
        "niche": "cloture",
        "comment": "Cloture et clotures residentielles et commerciales Quebec",
        "prices_main_cards": [
            {"label":"Clôture en bois","sublabel":"Pin · Cèdre · Traité","emoji":"🌲","key_min":"service1_min","key_max":"service1_max","featured":False},
            {"label":"Clôture en vinyle","sublabel":"PVC · Blanc · Beige · Gris","emoji":"🏡","key_min":"service2_min","key_max":"service2_max","featured":True},
            {"label":"Clôture en aluminium","sublabel":"Ornementale · Galvanisée","emoji":"⚙️","key_min":"service3_min","key_max":"service3_max","featured":False},
        ],
        "site": {
            "name": "Expert Cloture",
            "niche": "cloture",
            "domain": "https://soumission-cloture.ca",
            "phone": "",
            "service_label": "Clôture",
            "schema_type": "HomeAndConstructionBusiness",
            "schema_description": "Installation et remplacement de clotures a {ville}. Clotures en bois, vinyle, aluminium et mailles. Entrepreneurs certifies RBQ.",
            "price_range": "$$",
            "ga_id": "G-XXXXXXXXXX",
            "form_name": "soumission-cloture",
            "lead_system": "external_link",
        },
        "affiliate": {
            "base_url": "https://soumissionrenovation.ca/fr/formulaire/service/cloture?utm_campaign=jb",
            "aff_id": "",
            "redirect_path": "/soumission-cloture/",
            "badge": "Soumission 100% gratuite",
            "button_text": "Obtenir mes soumissions gratuites",
            "sublabel": "3 a 5 soumissions - Installateurs locaux - Reponse en 24h",
        },
        "css_prefix": "cl-",
        "colors": {"50":"#f0fdf4","100":"#dcfce7","200":"#bbf7d0","300":"#86efac","400":"#4ade80","500":"#22c55e","600":"#16a34a","700":"#15803d","800":"#166534","900":"#14532d","shadow":"rgba(22,163,74,0.35)","shadow_hover":"rgba(22,163,74,0.50)"},
        "prices": make_prices(3500,12000,1800,6000,1200,4500,2500,8000),
        "images_alts": [
            "Installation de cloture en bois a {ville}, Quebec",
            "Cloture en vinyle blanc installee a {ville}",
            "Entrepreneur en cloture au travail a {ville}",
            "Cloture en aluminium — {ville} et region",
            "Nouvelle cloture en maille installee a {ville}",
        ],
        "seo_titles": [
            "Clôture {ville} — Prix {annee} & Soumissions Gratuites | {site_name}",
            "Prix Clôture {ville} {annee} : Bois, Vinyle, Aluminium",
            "Installateur de clôture à {ville} — Experts Certifiés | {site_name}",
            "{ville} : Clôture {annee} — Jusqu'à 5 Soumissions Gratuites",
        ],
        "seo_descs": [
            "Comparez jusqu'a 5 soumissions gratuites d'installateurs de clotures a {ville}. Bois, vinyle, aluminium, maille. Reponse en 24h.",
            "Installation de cloture professionnelle a {ville} — bois, vinyle, aluminium, maille. Experts certifies. Devis gratuit.",
            "Prix cloture {ville} {annee} : bois des {service1_min}$, vinyle des {service2_min}$. Comparez 5 soumissions locales.",
        ],
        "banner_text": "{nb} projets de cloture soumis cette semaine",
        "service_label_lc": "cloture",
        "service_label_pl": "clotures",
        "intro": "Vous {cherchez un installateur de cloture|planifiez une cloture} a {ville}? {Obtenez|Recevez} jusqu'a 5 {soumissions gratuites|devis personnalises} de {specialistes en cloture|entrepreneurs locaux} en moins de {24 heures|24h}. {Bois|Vinyle|Aluminium|Maille} — {travaux garantis|resultats durables}.",
        "form_options": [
            {"value":"bois","emoji":"🌲","label":"Cloture en bois"},
            {"value":"vinyle","emoji":"🏡","label":"Cloture en vinyle"},
            {"value":"aluminium","emoji":"⚙️","label":"Cloture en aluminium"},
            {"value":"maille","emoji":"🔗","label":"Cloture en maille de chaine"},
            {"value":"composite","emoji":"✅","label":"Cloture composite / autre"},
        ],
        "section_headings": {
            "reassurance": "Pourquoi choisir {site_name} pour votre cloture a {ville} ?",
            "prices": "Prix cloture a {ville} — {annee}",
            "services": "Types de clotures disponibles a {ville}",
            "faq": "Questions frequentes — Cloture a {ville}",
            "cta_title": "Pret a installer votre cloture a {ville} ?",
            "cta_subtitle": "Soumission gratuite · Reponse en 24h · Installateurs locaux verifies",
            "cta_button": "Obtenir mes soumissions gratuites",
            "cta_note": "Gratuit · Sans engagement · Reponse en 24h",
            "footer_tagline": "{nb_villes_total} municipalites couvertes. Installateurs de clotures partout au Quebec.",
            "footer_region_title": "Cloture en {region}",
            "nav_badge": "Soumission gratuite",
            "nav_cta": "Obtenir un prix",
        },
    },
    {
        "niche": "chauffage",
        "comment": "Chauffage et systemes de chauffage Quebec",
        "prices_main_cards": [
            {"label":"Thermopompe murale","sublabel":"Chauffage + climatisation","emoji":"🌡️","key_min":"service1_min","key_max":"service1_max","featured":False},
            {"label":"Remplacement fournaise","sublabel":"Gaz · Propane · Mazout","emoji":"🔥","key_min":"service2_min","key_max":"service2_max","featured":True},
            {"label":"Chauffage radiant","sublabel":"Plancher chauffant à l'eau","emoji":"♨️","key_min":"service3_min","key_max":"service3_max","featured":False},
        ],
        "site": {
            "name": "Experts Chauffage",
            "niche": "chauffage",
            "domain": "https://experts-chauffage.ca",
            "phone": "",
            "service_label": "Chauffage",
            "schema_type": "HomeAndConstructionBusiness",
            "schema_description": "Installation et remplacement de systemes de chauffage a {ville}. Thermopompes, fournaises, radiateurs, plinthes. Experts certifies RBQ.",
            "price_range": "$$",
            "ga_id": "G-XXXXXXXXXX",
            "form_name": "soumission-chauffage",
            "lead_system": "external_link",
        },
        "affiliate": {
            "base_url": "https://soumissionrenovation.ca/fr/formulaire/service/chauffage?utm_campaign=jb",
            "aff_id": "",
            "redirect_path": "/soumission-chauffage/",
            "badge": "Soumission 100% gratuite",
            "button_text": "Obtenir mes soumissions gratuites",
            "sublabel": "3 a 5 soumissions - Specialistes locaux - Reponse en 24h",
        },
        "css_prefix": "ch-",
        "colors": {"50":"#fff7ed","100":"#ffedd5","200":"#fed7aa","300":"#fdba74","400":"#fb923c","500":"#f97316","600":"#ea580c","700":"#c2410c","800":"#9a3412","900":"#7c2d12","shadow":"rgba(234,88,12,0.35)","shadow_hover":"rgba(234,88,12,0.50)"},
        "prices": make_prices(4500,16000,3000,12000,2500,9000,1800,7000),
        "images_alts": [
            "Technicien installant une thermopompe a {ville}, Quebec",
            "Installation de fournaise au gaz a {ville}",
            "Systeme de chauffage radiant — {ville} et region",
            "Expert en chauffage au travail a {ville}",
            "Nouvelle thermopompe murale installee a {ville}",
        ],
        "seo_titles": [
            "Chauffage {ville} — Prix {annee} & Soumissions Gratuites | {site_name}",
            "Prix Chauffage {ville} {annee} : Thermopompe, Fournaise, Radiant",
            "Specialiste Chauffage à {ville} — Experts Certifiés | {site_name}",
            "{ville} : Chauffage {annee} — Jusqu'à 5 Soumissions Gratuites",
        ],
        "seo_descs": [
            "Comparez jusqu'a 5 soumissions gratuites de specialistes en chauffage a {ville}. Thermopompes, fournaises, radiant. Reponse en 24h.",
            "Installation de systeme de chauffage professionnel a {ville} — thermopompe, fournaise, radiant. Experts certifies.",
            "Prix chauffage {ville} {annee} : thermopompe des {service1_min}$, fournaise des {service2_min}$. Comparez 5 soumissions.",
        ],
        "banner_text": "{nb} projets de chauffage soumis cette semaine",
        "service_label_lc": "chauffage",
        "service_label_pl": "systemes de chauffage",
        "intro": "Vous {cherchez un specialiste en chauffage|planifiez le remplacement de votre systeme de chauffage} a {ville}? {Obtenez|Recevez} jusqu'a 5 {soumissions gratuites|devis personnalises} de {specialistes en chauffage|entrepreneurs certifies} en moins de {24 heures|24h}. {Thermopompe|Fournaise|Chauffage radiant|Plinthes} — {travaux garantis|economisez sur votre chauffage}.",
        "form_options": [
            {"value":"thermopompe","emoji":"🌡️","label":"Thermopompe (mural / central)"},
            {"value":"fournaise","emoji":"🔥","label":"Fournaise au gaz / propane"},
            {"value":"radiant","emoji":"♨️","label":"Chauffage radiant plancher"},
            {"value":"plinthes","emoji":"🏠","label":"Plinthes electriques"},
            {"value":"autre","emoji":"⚙️","label":"Autre systeme de chauffage"},
        ],
        "section_headings": {
            "reassurance": "Pourquoi choisir {site_name} pour votre chauffage a {ville} ?",
            "prices": "Prix chauffage a {ville} — {annee}",
            "services": "Systemes de chauffage disponibles a {ville}",
            "faq": "Questions frequentes — Chauffage a {ville}",
            "cta_title": "Pret a optimiser votre chauffage a {ville} ?",
            "cta_subtitle": "Soumission gratuite · Reponse en 24h · Specialistes locaux verifies",
            "cta_button": "Obtenir mes soumissions gratuites",
            "cta_note": "Gratuit · Sans engagement · Reponse en 24h",
            "footer_tagline": "{nb_villes_total} municipalites couvertes. Specialistes en chauffage partout au Quebec.",
            "footer_region_title": "Chauffage en {region}",
            "nav_badge": "Soumission gratuite",
            "nav_cta": "Obtenir un prix",
        },
    },
    {
        "niche": "beton",
        "comment": "Travaux de beton residentiels et commerciaux Quebec",
        "prices_main_cards": [
            {"label":"Entrée de garage","sublabel":"Béton estampé · Coloré · Uni","emoji":"🚗","key_min":"service1_min","key_max":"service1_max","featured":True},
            {"label":"Dalle de béton","sublabel":"Sous-sol · Garage · Patio","emoji":"🏠","key_min":"service2_min","key_max":"service2_max","featured":False},
            {"label":"Réparation béton","sublabel":"Fissures · Affaissement · Scellement","emoji":"🔧","key_min":"service3_min","key_max":"service3_max","featured":False},
        ],
        "site": {
            "name": "Prix Béton",
            "niche": "beton",
            "domain": "https://prix-beton.ca",
            "phone": "",
            "service_label": "Béton",
            "schema_type": "HomeAndConstructionBusiness",
            "schema_description": "Travaux de beton a {ville}. Entrees, patios, fondations, dalles. Entrepreneurs en beton certifies RBQ.",
            "price_range": "$$",
            "ga_id": "G-XXXXXXXXXX",
            "form_name": "soumission-beton",
            "lead_system": "external_link",
        },
        "affiliate": {
            "base_url": "https://soumissionrenovation.ca/fr/formulaire/service/beton?utm_campaign=jb",
            "aff_id": "",
            "redirect_path": "/soumission-beton/",
            "badge": "Soumission 100% gratuite",
            "button_text": "Obtenir mes soumissions gratuites",
            "sublabel": "3 a 5 soumissions - Entrepreneurs locaux - Reponse en 24h",
        },
        "css_prefix": "bt-",
        "colors": {"50":"#fafaf9","100":"#f5f5f4","200":"#e7e5e4","300":"#d6d3d1","400":"#a8a29e","500":"#78716c","600":"#57534e","700":"#44403c","800":"#292524","900":"#1c1917","shadow":"rgba(87,83,78,0.35)","shadow_hover":"rgba(87,83,78,0.50)"},
        "prices": make_prices(5000,20000,3500,14000,2000,9000,4000,18000),
        "images_alts": [
            "Coule de beton pour entree de maison a {ville}, Quebec",
            "Patio en beton estampe installe a {ville}",
            "Fondation en beton — {ville} et region",
            "Entrepreneur en beton au travail a {ville}",
            "Nouvelle dalle de beton installee a {ville}",
        ],
        "seo_titles": [
            "Béton {ville} — Prix {annee} & Soumissions Gratuites | {site_name}",
            "Prix Béton {ville} {annee} : Entrée, Patio, Fondation",
            "Entrepreneur Béton à {ville} — Experts Certifiés | {site_name}",
            "{ville} : Béton {annee} — Jusqu'à 5 Soumissions Gratuites",
        ],
        "seo_descs": [
            "Comparez jusqu'a 5 soumissions gratuites d'entrepreneurs en beton a {ville}. Entrees, patios, fondations, dalles. Reponse en 24h.",
            "Travaux de beton professionnels a {ville} — entree, patio, fondation, dalle. Experts certifies RBQ.",
            "Prix beton {ville} {annee} : entree des {service1_min}$, patio des {service2_min}$. Comparez 5 soumissions.",
        ],
        "banner_text": "{nb} projets de beton soumis cette semaine",
        "service_label_lc": "beton",
        "service_label_pl": "travaux de beton",
        "intro": "Vous {cherchez un entrepreneur en beton|planifiez des travaux de beton} a {ville}? {Obtenez|Recevez} jusqu'a 5 {soumissions gratuites|devis personnalises} de {entrepreneurs en beton|specialistes locaux} en moins de {24 heures|24h}. {Entree|Patio|Fondation|Dalle} — {travaux garantis|resultats durables}.",
        "form_options": [
            {"value":"entree","emoji":"🚗","label":"Entree de maison / garage"},
            {"value":"patio","emoji":"🏡","label":"Patio ou terrasse en beton"},
            {"value":"fondation","emoji":"🏗️","label":"Fondation ou mur de fondation"},
            {"value":"dalle","emoji":"⬜","label":"Dalle interieure / sous-sol"},
            {"value":"autre","emoji":"🔧","label":"Autre travail en beton"},
        ],
        "section_headings": {
            "reassurance": "Pourquoi choisir {site_name} pour vos travaux de beton a {ville} ?",
            "prices": "Prix beton a {ville} — {annee}",
            "services": "Services en beton disponibles a {ville}",
            "faq": "Questions frequentes — Beton a {ville}",
            "cta_title": "Pret a demarrer vos travaux de beton a {ville} ?",
            "cta_subtitle": "Soumission gratuite · Reponse en 24h · Entrepreneurs locaux verifies",
            "cta_button": "Obtenir mes soumissions gratuites",
            "cta_note": "Gratuit · Sans engagement · Reponse en 24h",
            "footer_tagline": "{nb_villes_total} municipalites couvertes. Entrepreneurs en beton partout au Quebec.",
            "footer_region_title": "Beton en {region}",
            "nav_badge": "Soumission gratuite",
            "nav_cta": "Obtenir un prix",
        },
    },
    {
        "niche": "portes-fenetres",
        "comment": "Portes et fenetres — remplacement et installation Quebec",
        "prices_main_cards": [
            {"label":"Remplacement fenêtres","sublabel":"PVC · Bois · Aluminium","emoji":"🪟","key_min":"service1_min","key_max":"service1_max","featured":True},
            {"label":"Porte extérieure","sublabel":"Acier · Fibre de verre · Bois","emoji":"🚪","key_min":"service2_min","key_max":"service2_max","featured":False},
            {"label":"Porte-fenêtre / Patio","sublabel":"Coulissante · Française","emoji":"🏡","key_min":"service3_min","key_max":"service3_max","featured":False},
        ],
        "site": {
            "name": "Experts Fenêtres",
            "niche": "portes-fenetres",
            "domain": "https://experts-fenetres.ca",
            "phone": "",
            "service_label": "Portes et Fenêtres",
            "schema_type": "HomeAndConstructionBusiness",
            "schema_description": "Remplacement de portes et fenetres a {ville}. Fenetres triple vitrage, portes entrees, patio. Experts certifies RBQ.",
            "price_range": "$$",
            "ga_id": "G-XXXXXXXXXX",
            "form_name": "soumission-fenetres",
            "lead_system": "external_link",
        },
        "affiliate": {
            "base_url": "https://soumissionrenovation.ca/fr/formulaire/service/portes-et-fenetres?utm_campaign=jb",
            "aff_id": "",
            "redirect_path": "/soumission-fenetres/",
            "badge": "Soumission 100% gratuite",
            "button_text": "Obtenir mes soumissions gratuites",
            "sublabel": "3 a 5 soumissions - Poseurs locaux certifies - Reponse en 24h",
        },
        "css_prefix": "pf-",
        "colors": {"50":"#eff6ff","100":"#dbeafe","200":"#bfdbfe","300":"#93c5fd","400":"#60a5fa","500":"#3b82f6","600":"#2563eb","700":"#1d4ed8","800":"#1e40af","900":"#1e3a8a","shadow":"rgba(37,99,235,0.35)","shadow_hover":"rgba(37,99,235,0.50)"},
        "prices": make_prices(800,3500,400,2000,1200,5000,2500,12000),
        "images_alts": [
            "Installation de fenetres triple vitrage a {ville}, Quebec",
            "Remplacement de porte d'entree a {ville}",
            "Nouvelles fenetres energetiques — {ville} et region",
            "Poseur de fenetres au travail a {ville}",
            "Porte-patio en vinyle installee a {ville}",
        ],
        "seo_titles": [
            "Portes et Fenêtres {ville} — Prix {annee} & Soumissions Gratuites | {site_name}",
            "Prix Fenêtres {ville} {annee} : Triple Vitrage, PVC, Bois",
            "Remplacement Fenêtres à {ville} — Experts Certifiés | {site_name}",
            "{ville} : Portes & Fenêtres {annee} — Jusqu'à 5 Soumissions Gratuites",
        ],
        "seo_descs": [
            "Comparez jusqu'a 5 soumissions gratuites de poseurs de fenetres a {ville}. Triple vitrage, PVC, aluminium, bois. Reponse en 24h.",
            "Remplacement de portes et fenetres professionnel a {ville} — triple vitrage, PVC, bois. Experts certifies.",
            "Prix fenetres {ville} {annee} : fenetre des {service1_min}$, porte entree des {service2_min}$. Comparez 5 soumissions.",
        ],
        "banner_text": "{nb} projets de portes et fenetres soumis cette semaine",
        "service_label_lc": "portes et fenetres",
        "service_label_pl": "portes et fenetres",
        "intro": "Vous {cherchez un poseur de fenetres|planifiez le remplacement de vos fenetres} a {ville}? {Obtenez|Recevez} jusqu'a 5 {soumissions gratuites|devis personnalises} de {specialistes en fenetres|entrepreneurs locaux} en moins de {24 heures|24h}. {Fenetres triple vitrage|Portes d'entree|Portes-patio|Velux} — {travaux garantis|economisez sur votre chauffage}.",
        "form_options": [
            {"value":"fenetres","emoji":"🪟","label":"Fenetres (remplacement)"},
            {"value":"porte-entree","emoji":"🚪","label":"Porte d'entree principale"},
            {"value":"porte-patio","emoji":"🏡","label":"Porte-patio / coulissante"},
            {"value":"porte-garage","emoji":"🚗","label":"Porte de garage"},
            {"value":"complet","emoji":"✅","label":"Projet complet portes + fenetres"},
        ],
        "section_headings": {
            "reassurance": "Pourquoi choisir {site_name} pour vos portes et fenetres a {ville} ?",
            "prices": "Prix portes et fenetres a {ville} — {annee}",
            "services": "Types de portes et fenetres disponibles a {ville}",
            "faq": "Questions frequentes — Portes et fenetres a {ville}",
            "cta_title": "Pret a remplacer vos portes et fenetres a {ville} ?",
            "cta_subtitle": "Soumission gratuite · Reponse en 24h · Poseurs locaux certifies",
            "cta_button": "Obtenir mes soumissions gratuites",
            "cta_note": "Gratuit · Sans engagement · Reponse en 24h",
            "footer_tagline": "{nb_villes_total} municipalites couvertes. Experts portes et fenetres partout au Quebec.",
            "footer_region_title": "Portes et fenetres en {region}",
            "nav_badge": "Soumission gratuite",
            "nav_cta": "Obtenir un prix",
        },
    },
    {
        "niche": "agrandissement",
        "comment": "Agrandissement de maison et ajout de pieces Quebec",
        "prices_main_cards": [
            {"label":"Agrandissement maison","sublabel":"Extension latérale · Arrière","emoji":"🏗️","key_min":"service1_min","key_max":"service1_max","featured":True},
            {"label":"Ajout d'étage","sublabel":"Mansarde · Deuxième étage","emoji":"🏠","key_min":"service2_min","key_max":"service2_max","featured":False},
            {"label":"Garage attenant","sublabel":"Simple · Double · Avec logement","emoji":"🚗","key_min":"service3_min","key_max":"service3_max","featured":False},
        ],
        "site": {
            "name": "Soumission Agrandissement",
            "niche": "agrandissement",
            "domain": "https://soumission-agrandissement.ca",
            "phone": "",
            "service_label": "Agrandissement",
            "schema_type": "GeneralContractor",
            "schema_description": "Agrandissement de maison a {ville}. Ajout de pieces, extensions, garage, annexe. Entrepreneurs generaux certifies RBQ.",
            "price_range": "$$$",
            "ga_id": "G-XXXXXXXXXX",
            "form_name": "soumission-agrandissement",
            "lead_system": "external_link",
        },
        "affiliate": {
            "base_url": "https://soumissionrenovation.ca/fr/formulaire/service/agrandissement?utm_campaign=jb",
            "aff_id": "",
            "redirect_path": "/soumission-agrandissement/",
            "badge": "Soumission 100% gratuite",
            "button_text": "Obtenir mes soumissions gratuites",
            "sublabel": "3 a 5 soumissions - Entrepreneurs generaux - Reponse en 24h",
        },
        "css_prefix": "ag-",
        "colors": {"50":"#f0fdfa","100":"#ccfbf1","200":"#99f6e4","300":"#5eead4","400":"#2dd4bf","500":"#14b8a6","600":"#0d9488","700":"#0f766e","800":"#115e59","900":"#134e4a","shadow":"rgba(13,148,136,0.35)","shadow_hover":"rgba(13,148,136,0.50)"},
        "prices": make_prices(45000,150000,30000,90000,20000,70000,35000,120000),
        "images_alts": [
            "Agrandissement de maison en cours a {ville}, Quebec",
            "Extension de maison avec nouvelle facade a {ville}",
            "Ajout d'une piece sur une maison a {ville}",
            "Entrepreneur en agrandissement au travail a {ville}",
            "Maison agrandie avec nouvelle annexe a {ville}",
        ],
        "seo_titles": [
            "Agrandissement Maison {ville} — Prix {annee} & Soumissions Gratuites | {site_name}",
            "Prix Agrandissement {ville} {annee} : Extension, Ajout de Pièce",
            "Entrepreneur Agrandissement à {ville} — Experts Certifiés | {site_name}",
            "{ville} : Agrandissement {annee} — Jusqu'à 5 Soumissions Gratuites",
        ],
        "seo_descs": [
            "Comparez jusqu'a 5 soumissions gratuites d'entrepreneurs en agrandissement a {ville}. Extensions, ajouts de pieces, garages. Reponse en 24h.",
            "Agrandissement de maison professionnel a {ville} — extension, ajout de pieces, garage, annexe. Experts certifies RBQ.",
            "Prix agrandissement {ville} {annee} : extension des {service1_min}$. Comparez 5 soumissions d'entrepreneurs generaux.",
        ],
        "banner_text": "{nb} projets d'agrandissement soumis cette semaine",
        "service_label_lc": "agrandissement",
        "service_label_pl": "agrandissements",
        "intro": "Vous {cherchez un entrepreneur pour agrandir votre maison|planifiez un agrandissement} a {ville}? {Obtenez|Recevez} jusqu'a 5 {soumissions gratuites|devis personnalises} de {entrepreneurs generaux|specialistes en agrandissement} en moins de {24 heures|24h}. {Extension laterale|Ajout d'etage|Garage|Annexe} — {projet cle en main|travaux garantis}.",
        "form_options": [
            {"value":"extension-laterale","emoji":"↔️","label":"Extension laterale (cote maison)"},
            {"value":"ajout-etage","emoji":"🏗️","label":"Ajout d'un etage ou demi-etage"},
            {"value":"garage","emoji":"🚗","label":"Garage attache ou detache"},
            {"value":"solarium","emoji":"🌿","label":"Solarium ou veranda"},
            {"value":"annexe","emoji":"🏠","label":"Annexe / logement supplementaire"},
        ],
        "section_headings": {
            "reassurance": "Pourquoi choisir {site_name} pour votre agrandissement a {ville} ?",
            "prices": "Prix agrandissement a {ville} — {annee}",
            "services": "Types d'agrandissements disponibles a {ville}",
            "faq": "Questions frequentes — Agrandissement a {ville}",
            "cta_title": "Pret a agrandir votre maison a {ville} ?",
            "cta_subtitle": "Soumission gratuite · Reponse en 24h · Entrepreneurs generaux verifies",
            "cta_button": "Obtenir mes soumissions gratuites",
            "cta_note": "Gratuit · Sans engagement · Reponse en 24h",
            "footer_tagline": "{nb_villes_total} municipalites couvertes. Entrepreneurs en agrandissement partout au Quebec.",
            "footer_region_title": "Agrandissement en {region}",
            "nav_badge": "Soumission gratuite",
            "nav_cta": "Obtenir un prix",
        },
    },
    {
        "niche": "ceramique",
        "comment": "Pose de ceramique et carrelage Quebec",
        "prices_main_cards": [
            {"label":"Plancher en céramique","sublabel":"Salle de bain · Cuisine · Salon","emoji":"🏠","key_min":"service1_min","key_max":"service1_max","featured":True},
            {"label":"Réfection salle de bain","sublabel":"Douche · Bain · Murs carrelés","emoji":"🚿","key_min":"service2_min","key_max":"service2_max","featured":False},
            {"label":"Dosseret cuisine","sublabel":"Métro · Mosaïque · Grand format","emoji":"🍽️","key_min":"service3_min","key_max":"service3_max","featured":False},
        ],
        "site": {
            "name": "Prix Céramique",
            "niche": "ceramique",
            "domain": "https://prix-ceramique.ca",
            "phone": "",
            "service_label": "Céramique",
            "schema_type": "HomeAndConstructionBusiness",
            "schema_description": "Pose de ceramique et carrelage a {ville}. Plancher, salle de bain, cuisine, mosaique. Carreleurs certifies.",
            "price_range": "$$",
            "ga_id": "G-XXXXXXXXXX",
            "form_name": "soumission-ceramique",
            "lead_system": "external_link",
        },
        "affiliate": {
            "base_url": "https://soumissionrenovation.ca/fr/formulaire/service/ceramique?utm_campaign=jb",
            "aff_id": "",
            "redirect_path": "/soumission-ceramique/",
            "badge": "Soumission 100% gratuite",
            "button_text": "Obtenir mes soumissions gratuites",
            "sublabel": "3 a 5 soumissions - Carreleurs locaux - Reponse en 24h",
        },
        "css_prefix": "cr-",
        "colors": {"50":"#fdf4ff","100":"#fae8ff","200":"#f5d0fe","300":"#f0abfc","400":"#e879f9","500":"#d946ef","600":"#c026d3","700":"#a21caf","800":"#86198f","900":"#701a75","shadow":"rgba(192,38,211,0.35)","shadow_hover":"rgba(192,38,211,0.50)"},
        "prices": make_prices(1500,6000,800,3500,1200,5000,2000,8000),
        "images_alts": [
            "Pose de ceramique dans une salle de bain a {ville}, Quebec",
            "Carreleur installant un plancher en ceramique a {ville}",
            "Ceramique grand format installee — {ville} et region",
            "Carreleur professionnel au travail a {ville}",
            "Nouvelle ceramique de douche italienne a {ville}",
        ],
        "seo_titles": [
            "Céramique {ville} — Prix {annee} & Soumissions Gratuites | {site_name}",
            "Prix Céramique {ville} {annee} : Plancher, Salle de Bain, Cuisine",
            "Carreleur à {ville} — Experts Certifiés | {site_name}",
            "{ville} : Céramique {annee} — Jusqu'à 5 Soumissions Gratuites",
        ],
        "seo_descs": [
            "Comparez jusqu'a 5 soumissions gratuites de carreleurs a {ville}. Plancher, salle de bain, cuisine, douche. Reponse en 24h.",
            "Pose de ceramique professionnelle a {ville} — plancher, salle de bain, cuisine, mosaique. Carreleurs certifies.",
            "Prix ceramique {ville} {annee} : plancher des {service2_min}$/pi2. Comparez 5 soumissions locales.",
        ],
        "banner_text": "{nb} projets de ceramique soumis cette semaine",
        "service_label_lc": "ceramique",
        "service_label_pl": "travaux de ceramique",
        "intro": "Vous {cherchez un carreleur|planifiez une pose de ceramique} a {ville}? {Obtenez|Recevez} jusqu'a 5 {soumissions gratuites|devis personnalises} de {carreleurs professionnels|specialistes locaux} en moins de {24 heures|24h}. {Plancher|Salle de bain|Douche|Cuisine} — {travaux garantis|finition impeccable}.",
        "form_options": [
            {"value":"plancher","emoji":"🏠","label":"Plancher (salon, cuisine, couloir)"},
            {"value":"salle-de-bain","emoji":"🚿","label":"Salle de bain complete"},
            {"value":"douche","emoji":"🛁","label":"Douche en ceramique"},
            {"value":"cuisine","emoji":"🍳","label":"Dosseret de cuisine"},
            {"value":"exterieur","emoji":"🌞","label":"Patio ou terrasse exterieure"},
        ],
        "section_headings": {
            "reassurance": "Pourquoi choisir {site_name} pour votre ceramique a {ville} ?",
            "prices": "Prix ceramique a {ville} — {annee}",
            "services": "Services de ceramique disponibles a {ville}",
            "faq": "Questions frequentes — Ceramique a {ville}",
            "cta_title": "Pret a transformer votre interieur a {ville} ?",
            "cta_subtitle": "Soumission gratuite · Reponse en 24h · Carreleurs locaux verifies",
            "cta_button": "Obtenir mes soumissions gratuites",
            "cta_note": "Gratuit · Sans engagement · Reponse en 24h",
            "footer_tagline": "{nb_villes_total} municipalites couvertes. Carreleurs professionnels partout au Quebec.",
            "footer_region_title": "Ceramique en {region}",
            "nav_badge": "Soumission gratuite",
            "nav_cta": "Obtenir un prix",
        },
    },
    {
        "niche": "toiture-plate",
        "comment": "Toiture plate et membrane elastomerique Quebec",
        "prices_main_cards": [
            {"label":"Membrane élastomère","sublabel":"Bicouche · Torchée · Adhésive","emoji":"🏢","key_min":"service1_min","key_max":"service1_max","featured":True},
            {"label":"TPO / EPDM","sublabel":"Membrane thermoplastique","emoji":"🏗️","key_min":"service2_min","key_max":"service2_max","featured":False},
            {"label":"Réparation toit plat","sublabel":"Fuite · Bulle · Décollement","emoji":"🔧","key_min":"service3_min","key_max":"service3_max","featured":False},
        ],
        "site": {
            "name": "Experts Toiture Plate",
            "niche": "toiture-plate",
            "domain": "https://experts-toiture-plate.ca",
            "phone": "",
            "service_label": "Toiture Plate",
            "schema_type": "HomeAndConstructionBusiness",
            "schema_description": "Toiture plate et membrane a {ville}. TPO, elastomere, EPDM, toiture verte. Couvreurs certifies RBQ.",
            "price_range": "$$",
            "ga_id": "G-XXXXXXXXXX",
            "form_name": "soumission-toiture-plate",
            "lead_system": "external_link",
        },
        "affiliate": {
            "base_url": "https://soumissionrenovation.ca/fr/formulaire/service/toiture-plate?utm_campaign=jb",
            "aff_id": "",
            "redirect_path": "/soumission-toiture-plate/",
            "badge": "Soumission 100% gratuite",
            "button_text": "Obtenir mes soumissions gratuites",
            "sublabel": "3 a 5 soumissions - Couvreurs locaux - Reponse en 24h",
        },
        "css_prefix": "tp-",
        "colors": {"50":"#f0f9ff","100":"#e0f2fe","200":"#bae6fd","300":"#7dd3fc","400":"#38bdf8","500":"#0ea5e9","600":"#0284c7","700":"#0369a1","800":"#075985","900":"#0c4a6e","shadow":"rgba(2,132,199,0.35)","shadow_hover":"rgba(2,132,199,0.50)"},
        "prices": make_prices(8000,30000,5000,20000,12000,45000,3000,12000),
        "images_alts": [
            "Couvreur appliquant une membrane elastomere sur une toiture plate a {ville}, Quebec",
            "Installation de membrane TPO sur toit plat a {ville}",
            "Toiture plate recuperee — {ville} et region",
            "Couvreur au travail sur une toiture plate a {ville}",
            "Nouvelle membrane de toiture plate installee a {ville}",
        ],
        "seo_titles": [
            "Toiture Plate {ville} — Prix {annee} & Soumissions Gratuites | {site_name}",
            "Prix Toiture Plate {ville} {annee} : Membrane, TPO, Elastomere",
            "Couvreur Toiture Plate à {ville} — Experts Certifiés | {site_name}",
            "{ville} : Toiture Plate {annee} — Jusqu'à 5 Soumissions Gratuites",
        ],
        "seo_descs": [
            "Comparez jusqu'a 5 soumissions gratuites de couvreurs en toiture plate a {ville}. Membrane, TPO, elastomere, EPDM. Reponse en 24h.",
            "Toiture plate professionnelle a {ville} — membrane elastomere, TPO, EPDM, toiture verte. Couvreurs certifies RBQ.",
            "Prix toiture plate {ville} {annee} : refection des {service1_min}$. Comparez 5 soumissions de couvreurs locaux.",
        ],
        "banner_text": "{nb} projets de toiture plate soumis cette semaine",
        "service_label_lc": "toiture plate",
        "service_label_pl": "toitures plates",
        "intro": "Vous {cherchez un couvreur pour votre toiture plate|planifiez la refection de votre toiture plate} a {ville}? {Obtenez|Recevez} jusqu'a 5 {soumissions gratuites|devis personnalises} de {couvreurs specialises|entrepreneurs certifies} en moins de {24 heures|24h}. {Membrane elastomere|TPO|EPDM|Toiture verte} — {etancheite garantie|travaux durables}.",
        "form_options": [
            {"value":"elastomere","emoji":"🔧","label":"Membrane elastomere (bicouche)"},
            {"value":"tpo","emoji":"⬜","label":"Membrane TPO (blanc, energetique)"},
            {"value":"epdm","emoji":"⬛","label":"Membrane EPDM (caoutchouc)"},
            {"value":"verte","emoji":"🌿","label":"Toiture verte / vegetalisee"},
            {"value":"inspection","emoji":"🔍","label":"Inspection et reparation locale"},
        ],
        "section_headings": {
            "reassurance": "Pourquoi choisir {site_name} pour votre toiture plate a {ville} ?",
            "prices": "Prix toiture plate a {ville} — {annee}",
            "services": "Types de toitures plates disponibles a {ville}",
            "faq": "Questions frequentes — Toiture plate a {ville}",
            "cta_title": "Pret a proteger votre toiture plate a {ville} ?",
            "cta_subtitle": "Soumission gratuite · Reponse en 24h · Couvreurs locaux certifies",
            "cta_button": "Obtenir mes soumissions gratuites",
            "cta_note": "Gratuit · Sans engagement · Reponse en 24h",
            "footer_tagline": "{nb_villes_total} municipalites couvertes. Couvreurs en toiture plate partout au Quebec.",
            "footer_region_title": "Toiture plate en {region}",
            "nav_badge": "Soumission gratuite",
            "nav_cta": "Obtenir un prix",
        },
    },
    {
        "niche": "nettoyage-conduits",
        "comment": "Nettoyage de conduits et ventilation Quebec",
        "prices_main_cards": [
            {"label":"Conduits de ventilation","sublabel":"Système central · VRV · VRC","emoji":"💨","key_min":"service1_min","key_max":"service1_max","featured":True},
            {"label":"Conduit de cheminée","sublabel":"Ramonage certifié WETT","emoji":"🔥","key_min":"service2_min","key_max":"service2_max","featured":False},
            {"label":"Conduit de sécheuse","sublabel":"Nettoyage anti-incendie","emoji":"🌀","key_min":"service3_min","key_max":"service3_max","featured":False},
        ],
        "site": {
            "name": "Nettoyage Conduits",
            "niche": "nettoyage-conduits",
            "domain": "https://nettoyage-conduits.ca",
            "phone": "",
            "service_label": "Nettoyage de Conduits",
            "schema_type": "HomeAndConstructionBusiness",
            "schema_description": "Nettoyage de conduits de ventilation et systemes HVAC a {ville}. Conduits d'air, dryer vent, systeme de chauffage. Experts certifies.",
            "price_range": "$",
            "ga_id": "G-XXXXXXXXXX",
            "form_name": "soumission-nettoyage-conduits",
            "lead_system": "external_link",
        },
        "affiliate": {
            "base_url": "https://soumissionrenovation.ca/fr/formulaire/service/nettoyage-conduits?utm_campaign=jb",
            "aff_id": "",
            "redirect_path": "/soumission-nettoyage-conduits/",
            "badge": "Soumission 100% gratuite",
            "button_text": "Obtenir mes soumissions gratuites",
            "sublabel": "3 a 5 soumissions - Techniciens locaux - Reponse en 24h",
        },
        "css_prefix": "nc-",
        "colors": {"50":"#ecfdf5","100":"#d1fae5","200":"#a7f3d0","300":"#6ee7b7","400":"#34d399","500":"#10b981","600":"#059669","700":"#047857","800":"#065f46","900":"#064e3b","shadow":"rgba(5,150,105,0.35)","shadow_hover":"rgba(5,150,105,0.50)"},
        "prices": make_prices(250,600,150,400,350,800,200,500),
        "images_alts": [
            "Technicien nettoyant des conduits de ventilation a {ville}, Quebec",
            "Nettoyage de conduits d'air dans une maison a {ville}",
            "Systeme de ventilation nettoye — {ville} et region",
            "Expert en nettoyage de conduits au travail a {ville}",
            "Conduits de climatisation nettoyes a {ville}",
        ],
        "seo_titles": [
            "Nettoyage Conduits {ville} — Prix {annee} & Soumissions Gratuites | {site_name}",
            "Prix Nettoyage Conduits {ville} {annee} : Ventilation, HVAC",
            "Nettoyage Conduits à {ville} — Experts Certifiés | {site_name}",
            "{ville} : Nettoyage Conduits {annee} — Jusqu'à 5 Soumissions Gratuites",
        ],
        "seo_descs": [
            "Comparez jusqu'a 5 soumissions gratuites pour le nettoyage de conduits a {ville}. Ventilation, HVAC, dryer vent. Reponse en 24h.",
            "Nettoyage professionnel de conduits de ventilation a {ville} — systeme HVAC, dryer vent, hottes. Techniciens certifies.",
            "Prix nettoyage conduits {ville} {annee} : maison des {service1_min}$. Comparez 5 soumissions de techniciens locaux.",
        ],
        "banner_text": "{nb} projets de nettoyage de conduits soumis cette semaine",
        "service_label_lc": "nettoyage de conduits",
        "service_label_pl": "nettoyages de conduits",
        "intro": "Vous {cherchez un technicien pour nettoyer vos conduits|planifiez le nettoyage de votre ventilation} a {ville}? {Obtenez|Recevez} jusqu'a 5 {soumissions gratuites|devis personnalises} de {techniciens en nettoyage de conduits|specialistes locaux} en moins de {24 heures|24h}. {Conduits d'air|Dryer vent|Systeme HVAC|Hottes commerciales} — {air plus sain|qualite de l'air amelioree}.",
        "form_options": [
            {"value":"residentiel","emoji":"🏠","label":"Maison unifamiliale (chauffage/clim)"},
            {"value":"dryer","emoji":"👕","label":"Conduit de secheuse (dryer vent)"},
            {"value":"commercial","emoji":"🏢","label":"Immeuble commercial ou multi"},
            {"value":"hotte","emoji":"🍳","label":"Hotte de cuisine (residentiel/resto)"},
            {"value":"inspection","emoji":"🔍","label":"Inspection camera seulement"},
        ],
        "section_headings": {
            "reassurance": "Pourquoi choisir {site_name} pour vos conduits a {ville} ?",
            "prices": "Prix nettoyage de conduits a {ville} — {annee}",
            "services": "Services de nettoyage de conduits disponibles a {ville}",
            "faq": "Questions frequentes — Nettoyage de conduits a {ville}",
            "cta_title": "Pret a assainir votre air a {ville} ?",
            "cta_subtitle": "Soumission gratuite · Reponse en 24h · Techniciens locaux verifies",
            "cta_button": "Obtenir mes soumissions gratuites",
            "cta_note": "Gratuit · Sans engagement · Reponse en 24h",
            "footer_tagline": "{nb_villes_total} municipalites couvertes. Techniciens en nettoyage de conduits partout au Quebec.",
            "footer_region_title": "Nettoyage conduits en {region}",
            "nav_badge": "Soumission gratuite",
            "nav_cta": "Obtenir un prix",
        },
    },
]

def build_qc_config(n):
    sl = n["service_label_lc"]
    sl_cap = n["site"]["service_label"]

    content = {
        "banner_text": n["banner_text"],
        "index_heading_spintax": [
            f"{{site_name}} — Tout le Quebec {{annee}}",
            f"{{site_name}} · {{nb_total}} villes couvertes {{annee}}",
            f"{sl_cap} au Quebec — {{nb_regions}} regions | {{site_name}}",
        ],
        "index_subheading_spintax": [
            f"Experts en {sl} — soumission gratuite sans engagement, reponse en 24h.",
            f"Comparez jusqu'a 5 soumissions de {sl} verifies pres de chez vous.",
            f"Soumission 100% gratuite · Reponse garantie en 24h.",
        ],
        "region_heading_spintax": [
            f"{sl_cap} en {{region}} — {{nb_villes}} municipalites couvertes",
            f"{sl_cap} professionnel en {{region}} — {{nb_villes}} villes",
            f"Expert {sl} {{region}} | {{nb_villes}} {{secteurs|municipalites|villes}} desservis",
        ],
        "region_intro_spintax": [
            f"Trouvez un {{expert en {sl}|specialiste professionnel}} dans votre ville en {{region}}.",
            f"Comparez les prix et {{obtenez|recevez}} jusqu'a 5 soumissions gratuites en {{region}}.",
            f"{{nb_villes}} municipalites en {{region}}. Soumission {{gratuite|sans frais}}, reponse en 24h.",
        ],
        "section_headings": n["section_headings"],
        "form_header": {
            "badge": "Soumission 100% gratuite",
            "title": f"Votre projet de {sl} a {{ville}}",
            "privacy_text": "Donnees confidentielles — transmises uniquement aux experts selectionnes dans votre secteur.",
        },
        "intro_spintax": [n["intro"]],
        "services": [
            {"icone":"✅","nom":f"{sl_cap} professionnel","desc":f"Travaux de {sl} realises par des experts certifies RBQ a {{ville}}."},
            {"icone":"💰","nom":"Soumissions gratuites","desc":"Comparez jusqu'a 5 soumissions gratuites de specialistes locaux."},
            {"icone":"⚡","nom":"Reponse en 24h","desc":"Nos partenaires vous repondent en moins de 24 heures."},
            {"icone":"🏆","nom":"Experts verifies","desc":f"Tous nos entrepreneurs en {sl} sont verifies et certifies."},
        ],
        "prices_display": {
            "subtitle": f"Tarifs indicatifs pour des travaux de {sl} a {{ville}}. Prix variables selon la superficie, les materiaux et la complexite.",
            "main_cards": n["prices_main_cards"],
        },
        "trust_points": [
            {"icon":"shield","title":"Entrepreneurs verifies","desc":f"Tous nos partenaires en {sl} sont certifies RBQ et assures."},
            {"icon":"dollar","title":"Soumission 100% gratuite","desc":"Aucun frais, aucun engagement. Comparez en toute liberte."},
            {"icon":"clock","title":"Reponse garantie en 24h","desc":"Nos partenaires locaux vous repondent rapidement."},
            {"icon":"star","title":"Experts locaux","desc":f"Des specialistes en {sl} qui connaissent votre region."},
        ],
        "faq_templates": [
            {"q":f"Combien coute un projet de {sl} a {{ville}} ?","a":f"Le prix d'un projet de {sl} a {{ville}} varie selon la superficie, les materiaux et la complexite. Comparez 5 soumissions gratuites pour obtenir le meilleur prix."},
            {"q":f"Comment trouver un bon expert en {sl} a {{ville}} ?","a":f"Privilegiez un entrepreneur certifie RBQ, assure et avec de bonnes references. Notre plateforme pre-verifie tous nos partenaires en {sl}."},
            {"q":f"Faut-il un permis pour des travaux de {sl} a {{ville}} ?","a":f"Certains travaux de {sl} necessitent un permis municipal. Consultez la ville de {{ville}} avant de commencer. Notre equipe peut vous orienter."},
            {"q":f"Quelle est la duree des travaux de {sl} ?","a":f"La duree varie selon l'ampleur du projet. Un petit projet de {sl} peut prendre quelques heures, un grand projet plusieurs jours."},
            {"q":"La soumission est-elle vraiment gratuite ?","a":"Oui, 100% gratuit et sans engagement. Vous recevez jusqu'a 5 soumissions de specialistes locaux et vous choisissez librement."},
        ],
        "cta_stats": [
            {"value":"5","label":"Soumissions"},
            {"value":"24h","label":"Reponse"},
            {"value":"100%","label":"Gratuit"},
        ],
    }

    config = {
        "_comment": f"config_{n['niche']}.json — Niche: {n['comment']}",
        "site": n["site"],
        "affiliate": n["affiliate"],
        "design": {
            "css_prefix": n["css_prefix"],
            "style": "rounded",
            "hero_style": "dark_overlay",
            "footer_style": "dark",
            "nav_style": "sticky_blur",
            "colors": n["colors"],
            "section_order": SECTION_ORDER,
            "templates_dir": "templates_v3",
        },
        "deploy": DEPLOY,
        "csv": CSV,
        "output_dir": f"dist_{n['niche']}",
        "performance": PERF,
        "social_proof": SP,
        "premium_cities": PREMIUM_CITIES,
        "authority_resources": qc_authority(n["service_label_lc"]),
        "images": make_images(n["images_alts"]),
        "prices": n["prices"],
        "seo": {
            "title_templates": n["seo_titles"],
            "desc_templates": n["seo_descs"],
        },
        "form": four_step_form_qc(n["site"]["service_label"], n["form_options"]),
        "content": content,
        "network": qc_network(n["niche"], n["site"]["domain"]),
        "anti_footprint": {
            "body_id_prefix": n["css_prefix"].rstrip("-"),
            "comments_count": 4,
            "random_comments": ["build","render","v1","static","gen","page","local","qc","lead","srv","node","data","proc","cache","init","ref","map","idx","seg","blk","tok","hash","seq"] + [n["niche"].replace("-","")[:8], n["css_prefix"].rstrip("-")],
        },
    }
    return config


# ─── EN NICHE DEFINITIONS ─────────────────────────────────────────────────────
EN_CSV = {"file": "CanadaCSV.csv", "col_city": "city", "col_city_ascii": "city_ascii", "col_region": "province_name", "col_population": "population"}
EN_PREMIUM = ["Toronto","Montreal","Vancouver","Calgary","Edmonton","Ottawa","Winnipeg","Hamilton","Kitchener","London","Halifax","Saskatoon","Regina","Victoria","Kelowna"]

EN_NICHES = [
    {
        "niche": "flooring",
        "config_key": "flooring_en",
        "prices_main_cards": [
            {"label":"Hardwood Installation","sublabel":"Solid · Engineered · Bamboo","emoji":"🪵","key_min":"service1_min","key_max":"service1_max","featured":True},
            {"label":"Laminate & Vinyl","sublabel":"LVP · LVT · Click-lock","emoji":"🏠","key_min":"service2_min","key_max":"service2_max","featured":False},
            {"label":"Sanding & Refinishing","sublabel":"Restore existing floors","emoji":"🪚","key_min":"service3_min","key_max":"service3_max","featured":False},
        ],
        "site": {
            "name": "Flooring Quotes",
            "niche": "flooring",
            "domain": "https://flooring-quotes.ca",
            "phone": "",
            "service_label": "Flooring",
            "schema_type": "HomeAndConstructionBusiness",
            "schema_description": "Professional flooring installation and replacement in {city}. Hardwood, laminate, vinyl plank, tile. Licensed flooring contractors.",
            "price_range": "$$",
            "ga_id": "G-XXXXXXXXXX",
            "form_name": "flooring-quote",
            "lead_system": "external_link",
            "lang": "en-CA",
        },
        "affiliate": {
            "base_url": "https://www.homestars.com/companies/search?q=flooring&near={city_ascii}&utm_campaign=jb",
            "aff_id": "",
            "redirect_path": "/flooring-quote/",
            "badge": "100% Free Quote",
            "button_text": "Get My Free Quotes",
            "sublabel": "3 to 5 quotes — Local flooring pros — Response in 24h",
        },
        "css_prefix": "fl-",
        "colors": {"50":"#fef9c3","100":"#fef08a","200":"#fde047","300":"#facc15","400":"#eab308","500":"#ca8a04","600":"#a16207","700":"#854d0e","800":"#713f12","900":"#422006","shadow":"rgba(161,98,7,0.35)","shadow_hover":"rgba(161,98,7,0.50)"},
        "prices": make_prices(3500,14000,2000,8000,1500,6000,4000,16000),
        "images_alts": [
            "Flooring contractor installing hardwood in a home in {city}",
            "New luxury vinyl plank flooring installed in {city}",
            "Professional flooring installation — {city}",
            "Wide plank hardwood floor — {city} home renovation",
            "Flooring specialist at work in {city}",
        ],
        "form_options": [
            {"value":"hardwood","emoji":"🪵","label":"Hardwood (solid or engineered)"},
            {"value":"laminate","emoji":"🏠","label":"Laminate flooring"},
            {"value":"vinyl","emoji":"⬜","label":"Luxury vinyl plank (LVP)"},
            {"value":"tile","emoji":"🔲","label":"Ceramic or porcelain tile"},
            {"value":"refinish","emoji":"✨","label":"Hardwood refinishing"},
        ],
    },
    {
        "niche": "painting",
        "config_key": "painting_en",
        "prices_main_cards": [
            {"label":"Interior Painting","sublabel":"Walls · Ceilings · Trim","emoji":"🏠","key_min":"service1_min","key_max":"service1_max","featured":True},
            {"label":"Exterior Painting","sublabel":"Siding · Trim · Deck","emoji":"🏡","key_min":"service2_min","key_max":"service2_max","featured":False},
            {"label":"Cabinet Painting","sublabel":"Kitchen · Bathroom · Built-ins","emoji":"🗄️","key_min":"service3_min","key_max":"service3_max","featured":False},
        ],
        "site": {
            "name": "Painting Quotes",
            "niche": "painting",
            "domain": "https://painting-quotes.ca",
            "phone": "",
            "service_label": "Painting",
            "schema_type": "HomeAndConstructionBusiness",
            "schema_description": "Professional interior and exterior painting in {city}. Residential and commercial painters. Licensed and insured.",
            "price_range": "$$",
            "ga_id": "G-XXXXXXXXXX",
            "form_name": "painting-quote",
            "lead_system": "external_link",
            "lang": "en-CA",
        },
        "affiliate": {
            "base_url": "https://www.homestars.com/companies/search?q=painting&near={city_ascii}&utm_campaign=jb",
            "aff_id": "",
            "redirect_path": "/painting-quote/",
            "badge": "100% Free Quote",
            "button_text": "Get My Free Quotes",
            "sublabel": "3 to 5 quotes — Local painters — Response in 24h",
        },
        "css_prefix": "pt-",
        "colors": {"50":"#fef2f2","100":"#fee2e2","200":"#fecaca","300":"#fca5a5","400":"#f87171","500":"#ef4444","600":"#dc2626","700":"#b91c1c","800":"#991b1b","900":"#7f1d1d","shadow":"rgba(220,38,38,0.35)","shadow_hover":"rgba(220,38,38,0.50)"},
        "prices": make_prices(3000,12000,1500,6000,4000,16000,800,3500),
        "images_alts": [
            "Professional painter on a ladder painting a home exterior in {city}",
            "Interior painting crew rolling walls in a home in {city}",
            "Freshly painted house exterior — {city}",
            "Painting contractor at work — {city}",
            "New interior paint job in a bright home in {city}",
        ],
        "form_options": [
            {"value":"interior","emoji":"🏠","label":"Interior painting (rooms, ceilings)"},
            {"value":"exterior","emoji":"🌤️","label":"Exterior painting (siding, trim)"},
            {"value":"cabinet","emoji":"🪟","label":"Cabinet painting / refinishing"},
            {"value":"commercial","emoji":"🏢","label":"Commercial or condo painting"},
            {"value":"deck","emoji":"🌿","label":"Deck or fence staining"},
        ],
    },
    {
        "niche": "landscaping",
        "config_key": "landscaping_en",
        "prices_main_cards": [
            {"label":"Landscape Design","sublabel":"Full yard · Garden beds","emoji":"🌿","key_min":"service1_min","key_max":"service1_max","featured":True},
            {"label":"Sod Installation","sublabel":"Kentucky Blue · Fescue · Rye","emoji":"🌱","key_min":"service2_min","key_max":"service2_max","featured":False},
            {"label":"Maintenance Contract","sublabel":"Seasonal · Weekly · Monthly","emoji":"🍂","key_min":"service3_min","key_max":"service3_max","featured":False},
        ],
        "site": {
            "name": "Landscaping Quotes",
            "niche": "landscaping",
            "domain": "https://landscaping-quotes.ca",
            "phone": "",
            "service_label": "Landscaping",
            "schema_type": "HomeAndConstructionBusiness",
            "schema_description": "Professional landscaping and lawn care in {city}. Design, installation, maintenance. Licensed landscaping contractors.",
            "price_range": "$$",
            "ga_id": "G-XXXXXXXXXX",
            "form_name": "landscaping-quote",
            "lead_system": "external_link",
            "lang": "en-CA",
        },
        "affiliate": {
            "base_url": "https://www.homestars.com/companies/search?q=landscaping&near={city_ascii}&utm_campaign=jb",
            "aff_id": "",
            "redirect_path": "/landscaping-quote/",
            "badge": "100% Free Quote",
            "button_text": "Get My Free Quotes",
            "sublabel": "3 to 5 quotes — Local landscapers — Response in 24h",
        },
        "css_prefix": "ls-",
        "colors": {"50":"#f0fdf4","100":"#dcfce7","200":"#bbf7d0","300":"#86efac","400":"#4ade80","500":"#22c55e","600":"#16a34a","700":"#15803d","800":"#166534","900":"#14532d","shadow":"rgba(22,163,74,0.35)","shadow_hover":"rgba(22,163,74,0.50)"},
        "prices": make_prices(5000,25000,2000,10000,3000,15000,1000,5000),
        "images_alts": [
            "Landscaping crew mowing a large lawn in {city}",
            "Professional landscapers installing garden beds in {city}",
            "Beautiful finished backyard landscape — {city}",
            "Landscaping crew laying sod in {city}",
            "Landscape contractor at work — {city}",
        ],
        "form_options": [
            {"value":"lawn","emoji":"🌿","label":"Lawn maintenance / mowing"},
            {"value":"design","emoji":"🌸","label":"Landscape design & installation"},
            {"value":"sod","emoji":"🟩","label":"Sod installation"},
            {"value":"patio","emoji":"🏡","label":"Patio / walkway / retaining wall"},
            {"value":"trees","emoji":"🌳","label":"Tree / shrub planting"},
        ],
    },
    {
        "niche": "fencing",
        "config_key": "fencing_en",
        "prices_main_cards": [
            {"label":"Wood Fence","sublabel":"Cedar · Pine · Pressure-treated","emoji":"🌲","key_min":"service1_min","key_max":"service1_max","featured":True},
            {"label":"Vinyl / PVC Fence","sublabel":"Privacy · Picket · Ranch","emoji":"🏡","key_min":"service2_min","key_max":"service2_max","featured":False},
            {"label":"Metal / Chain-link","sublabel":"Aluminum · Galvanized","emoji":"⚙️","key_min":"service3_min","key_max":"service3_max","featured":False},
        ],
        "site": {
            "name": "Fencing Quotes",
            "niche": "fencing",
            "domain": "https://fencing-quotes.ca",
            "phone": "",
            "service_label": "Fencing",
            "schema_type": "HomeAndConstructionBusiness",
            "schema_description": "Professional fence installation in {city}. Wood, vinyl, aluminum, chain link. Licensed fence contractors.",
            "price_range": "$$",
            "ga_id": "G-XXXXXXXXXX",
            "form_name": "fencing-quote",
            "lead_system": "external_link",
            "lang": "en-CA",
        },
        "affiliate": {
            "base_url": "https://www.homestars.com/companies/search?q=fencing&near={city_ascii}&utm_campaign=jb",
            "aff_id": "",
            "redirect_path": "/fencing-quote/",
            "badge": "100% Free Quote",
            "button_text": "Get My Free Quotes",
            "sublabel": "3 to 5 quotes — Local fence installers — Response in 24h",
        },
        "css_prefix": "fe-",
        "colors": {"50":"#f5f3ff","100":"#ede9fe","200":"#ddd6fe","300":"#c4b5fd","400":"#a78bfa","500":"#8b5cf6","600":"#7c3aed","700":"#6d28d9","800":"#5b21b6","900":"#4c1d95","shadow":"rgba(124,58,237,0.35)","shadow_hover":"rgba(124,58,237,0.50)"},
        "prices": make_prices(3500,14000,2000,8000,1500,6000,2500,10000),
        "images_alts": [
            "Fence installer setting cedar fence posts in a backyard in {city}",
            "New vinyl privacy fence installed in {city}",
            "Professional fence installation — {city}",
            "Wood privacy fence around a backyard — {city}",
            "Fence contractor at work in {city}",
        ],
        "form_options": [
            {"value":"wood","emoji":"🌲","label":"Wood fence (cedar / pressure-treated)"},
            {"value":"vinyl","emoji":"⬜","label":"Vinyl / PVC privacy fence"},
            {"value":"aluminum","emoji":"⚙️","label":"Aluminum ornamental fence"},
            {"value":"chain-link","emoji":"🔗","label":"Chain link fence"},
            {"value":"composite","emoji":"✅","label":"Composite or other"},
        ],
    },
    {
        "niche": "concrete",
        "config_key": "concrete_en",
        "prices_main_cards": [
            {"label":"Concrete Driveway","sublabel":"Plain · Stamped · Colored","emoji":"🚗","key_min":"service1_min","key_max":"service1_max","featured":True},
            {"label":"Patio & Walkway","sublabel":"Stamped · Exposed aggregate","emoji":"🏠","key_min":"service2_min","key_max":"service2_max","featured":False},
            {"label":"Concrete Repair","sublabel":"Cracks · Leveling · Sealing","emoji":"🔧","key_min":"service3_min","key_max":"service3_max","featured":False},
        ],
        "site": {
            "name": "Concrete Quotes",
            "niche": "concrete",
            "domain": "https://concrete-quotes.ca",
            "phone": "",
            "service_label": "Concrete",
            "schema_type": "HomeAndConstructionBusiness",
            "schema_description": "Professional concrete work in {city}. Driveways, patios, foundations, slabs. Licensed concrete contractors.",
            "price_range": "$$",
            "ga_id": "G-XXXXXXXXXX",
            "form_name": "concrete-quote",
            "lead_system": "external_link",
            "lang": "en-CA",
        },
        "affiliate": {
            "base_url": "https://www.homestars.com/companies/search?q=concrete&near={city_ascii}&utm_campaign=jb",
            "aff_id": "",
            "redirect_path": "/concrete-quote/",
            "badge": "100% Free Quote",
            "button_text": "Get My Free Quotes",
            "sublabel": "3 to 5 quotes — Local contractors — Response in 24h",
        },
        "css_prefix": "co-",
        "colors": {"50":"#f8fafc","100":"#f1f5f9","200":"#e2e8f0","300":"#cbd5e1","400":"#94a3b8","500":"#64748b","600":"#475569","700":"#334155","800":"#1e293b","900":"#0f172a","shadow":"rgba(71,85,105,0.35)","shadow_hover":"rgba(71,85,105,0.50)"},
        "prices": make_prices(5000,22000,3000,14000,2000,10000,4000,18000),
        "images_alts": [
            "Concrete crew finishing a new driveway in {city}",
            "Stamped concrete patio installation in {city}",
            "Professional concrete work — {city}",
            "New concrete driveway — {city} home",
            "Concrete contractor at work in {city}",
        ],
        "form_options": [
            {"value":"driveway","emoji":"🚗","label":"Concrete driveway"},
            {"value":"patio","emoji":"🏡","label":"Patio or walkway"},
            {"value":"foundation","emoji":"🏗️","label":"Foundation or basement floor"},
            {"value":"garage","emoji":"🏠","label":"Garage floor slab"},
            {"value":"stamped","emoji":"✨","label":"Stamped / decorative concrete"},
        ],
    },
]

def build_en_config(n):
    sl = n["site"]["service_label"]
    sl_lc = sl.lower()
    config = {
        "_comment": f"config_{n['config_key']}.json — Niche: {sl} Canada English",
        "site": n["site"],
        "affiliate": n["affiliate"],
        "design": {
            "css_prefix": n["css_prefix"],
            "style": "rounded",
            "hero_style": "dark_overlay",
            "footer_style": "dark",
            "nav_style": "sticky_blur",
            "colors": n["colors"],
            "section_order": SECTION_ORDER,
            "templates_dir": "templates_v3",
        },
        "deploy": DEPLOY,
        "csv": EN_CSV,
        "csv_options": {"filter_provinces": ["Ontario","British Columbia","Alberta","Quebec","Manitoba","Saskatchewan"],"min_population": 3000},
        "output_dir": f"dist_{n['config_key']}",
        "performance": PERF,
        "social_proof": SP,
        "premium_cities": EN_PREMIUM,
        "authority_resources": [
            {"url":"https://en.wikipedia.org/wiki/{city}","ancre":"{city} — Wikipedia","hook":f"Information about {{city}}: demographics and local context for {sl_lc} services."},
            {"url":"https://www.homestars.com/","ancre":"HomeStars — Verified Contractors","hook":f"HomeStars verifies {sl_lc} contractors across Canada. Check ratings before hiring."},
        ],
        "images": make_images(n["images_alts"]),
        "prices": n["prices"],
        "seo": {
            "title_templates": [
                f"{sl} {{city}} — Free Quotes {{year}} | {{site_name}}",
                f"Best {sl} Contractors in {{city}} {{year}} | {{site_name}}",
                f"{sl} {{city}} {{year}} — Compare 5 Free Quotes",
            ],
            "desc_templates": [
                f"Compare up to 5 free {sl_lc} quotes in {{city}}. Licensed and insured contractors. Response in 24h.",
                f"Professional {sl_lc} services in {{city}} — licensed contractors, free estimates, guaranteed work.",
            ],
        },
        "form": {
            "netlify_name": f"{sl_lc.replace(' ','-')}-quote",
            "submit_text": "Get My Free Quotes",
            "confirmation_title": "Request Received!",
            "confirmation_body": f"Our {sl_lc} pros in <strong>{{city}}</strong> will contact you within <strong>24 hours</strong>.",
            "confirmation_stats": [
                {"value":"24h","label":"Response"},{"value":"100%","label":"Free"},{"value":"5","label":"Quotes"},
            ],
            "steps": [
                {
                    "title": "Project Type",
                    "button_text": "Continue",
                    "fields": [{"type":"radio_cards","name":"project-type","label":f"What type of {sl_lc}?","required":True,"error_id":"project-error","options":n["form_options"]}]
                },
                {
                    "title": "Your Property",
                    "button_text": "Continue",
                    "fields": [
                        {"type":"select","name":"property-type","label":"Property type","required":True,"options":[
                            {"value":"house","label":"Single family home"},
                            {"value":"condo","label":"Condo / Apartment"},
                            {"value":"townhouse","label":"Townhouse"},
                            {"value":"commercial","label":"Commercial property"},
                        ]},
                        {"type":"select","name":"timeline","label":"When do you need the work done?","required":True,"options":[
                            {"value":"asap","label":"As soon as possible"},
                            {"value":"1-month","label":"Within 1 month"},
                            {"value":"3-months","label":"Within 3 months"},
                            {"value":"planning","label":"Just planning"},
                        ]},
                    ]
                },
                {
                    "title": "Your Contact Info",
                    "button_text": None,
                    "fields": [
                        {"type":"text","name":"name","label":"Full name","placeholder":"John Smith","required":True},
                        {"type":"email","name":"email","label":"Email address","placeholder":"john@example.com","required":True},
                        {"type":"tel","name":"phone","label":"Phone number","placeholder":"416 000-0000","required":True},
                    ]
                }
            ]
        },
        "content": {
            "banner_text": f"{{nb}} {sl_lc} projects submitted this week",
            "index_heading_spintax": [
                f"{{site_name}} — All of Canada {{year}}",
                f"{{site_name}} · {{nb_total}} cities covered {{year}}",
                f"{sl} Across Canada — {{nb_regions}} provinces | {{site_name}}",
            ],
            "index_subheading_spintax": [
                f"Professional {sl_lc} — free quotes, no commitment, response in 24h.",
                f"Compare up to 5 quotes from verified local {sl_lc} contractors.",
            ],
            "region_heading_spintax": [
                f"{sl} in {{region}} — {{nb_villes}} cities covered",
                f"Best {sl} Contractors in {{region}} — {{nb_villes}} cities",
            ],
            "region_intro_spintax": [
                f"Find a professional {sl_lc} contractor in your city in {{region}}.",
                f"Compare prices and get up to 5 free quotes in {{region}}.",
            ],
            "section_headings": {
                "reassurance": f"Why Choose {{site_name}} for {sl} in {{city}}?",
                "prices": f"{sl} Prices in {{city}} — {{year}}",
                "services": f"{sl} Services Available in {{city}}",
                "faq": f"Frequently Asked Questions — {sl} in {{city}}",
                "cta_title": f"Ready to Start Your {sl} Project in {{city}}?",
                "cta_subtitle": "Free quote · Response in 24h · Verified local contractors",
                "cta_button": "Get My Free Quotes",
                "cta_note": "Free · No commitment · Response in 24h",
                "footer_tagline": f"{{nb_villes_total}} cities covered. Professional {sl_lc} contractors across Canada.",
                "footer_region_title": f"{sl} in {{region}}",
                "nav_badge": "Free Quote",
                "nav_cta": "Get a Price",
            },
            "form_header": {
                "badge": "100% Free Quote",
                "title": f"Your {sl} Project in {{city}}",
                "privacy_text": "Your data is confidential — shared only with selected contractors in your area.",
            },
            "intro_spintax": [
                f"Looking for a {{professional {sl_lc} contractor|{sl_lc} specialist}} in {{city}}? {{Get|Receive}} up to 5 {{free quotes|personalized estimates}} from {{local {sl_lc} pros|verified contractors}} in less than {{24 hours|24h}}. {{Licensed|Certified}} — {{guaranteed work|quality results}}.",
            ],
            "services": [
                {"icone":"✅","nom":f"Professional {sl}","desc":f"Expert {sl_lc} services by licensed and insured contractors in {{city}}."},
                {"icone":"💰","nom":"Free Quotes","desc":"Compare up to 5 free quotes from local contractors."},
                {"icone":"⚡","nom":"24h Response","desc":"Our partner contractors respond within 24 hours."},
                {"icone":"🏆","nom":"Verified Contractors","desc":f"All our {sl_lc} contractors are verified, licensed, and insured."},
            ],
            "prices_display": {
                "subtitle": f"Indicative pricing for {sl_lc} projects in {{city}}. Final prices vary by scope, materials, and complexity.",
                "main_cards": n["prices_main_cards"],
            },
            "trust_points": [
                {"icon":"shield","title":"Verified Contractors","desc":f"All our {sl_lc} partners are licensed and insured."},
                {"icon":"dollar","title":"100% Free Quote","desc":"No fees, no commitment. Compare freely."},
                {"icon":"clock","title":"24h Guaranteed Response","desc":"Local partners respond quickly."},
                {"icon":"star","title":"Local Experts","desc":f"Specialists who know your area and {sl_lc} needs."},
            ],
            "faq_templates": [
                {"q":f"How much does {sl_lc} cost in {{city}}?","a":f"The cost of {sl_lc} in {{city}} varies by scope and materials. Compare 5 free quotes for the best price."},
                {"q":f"How do I find a reliable {sl_lc} contractor in {{city}}?","a":f"Look for a licensed, insured contractor with good reviews. Our platform pre-verifies all {sl_lc} partners."},
                {"q":"Is the quote really free?","a":"Yes, 100% free and no commitment. You receive up to 5 quotes from local specialists and choose freely."},
                {"q":f"How long does a {sl_lc} project take?","a":f"Duration varies by project size. A small {sl_lc} job may take a few hours; larger projects can take several days."},
            ],
            "cta_stats": [
                {"value":"5","label":"Quotes"},{"value":"24h","label":"Response"},{"value":"100%","label":"Free"},
            ],
        },
        "anti_footprint": {
            "body_id_prefix": n["css_prefix"].rstrip("-"),
            "comments_count": 4,
            "random_comments": ["build","render","v1","static","gen","page","local","ca","lead","srv","node","data","proc","cache","init","ref","map","idx","seg","blk","tok","hash","seq"] + [n["niche"][:8], n["css_prefix"].rstrip("-")],
        },
    }
    return config


# ─── WRITE FILES ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    qc_dir = os.path.join(BASE, "engine_qc")
    en_dir = os.path.join(BASE, "engine_en")
    created = []

    for n in QC_NICHES:
        path = os.path.join(qc_dir, f"config_{n['niche']}.json")
        if os.path.exists(path) and not force:
            print(f"  SKIP (exists): {path}")
            continue
        config = build_qc_config(n)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"  CREATED: {path}")
        created.append(path)

    for n in EN_NICHES:
        path = os.path.join(en_dir, f"config_{n['config_key']}.json")
        if os.path.exists(path) and not force:
            print(f"  SKIP (exists): {path}")
            continue
        config = build_en_config(n)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"  CREATED: {path}")
        created.append(path)

    print(f"\nDone. {len(created)} configs created.")
    if created:
        print("\nNext steps:")
        print("  1. Review each config and adjust domain, affiliate URL, prices")
        print("  2. python tools/generate_images.py <niche>  ← generates 50 images")
        print("  3. python engine_qc/EmpireGenerator.py --config engine_qc/config_<niche>.json")
        print("  4. python engine_en/EmpireGeneratorEN.py --config engine_en/config_<niche>_en.json")
