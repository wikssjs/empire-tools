"""
Generate 6 new EN config files for English Canada sites.
Run from Empire-PSEO root: python tools/create_en_configs.py
"""
import json, os

BASE = os.path.join(os.path.dirname(__file__), '..', 'engine_en')

LOCAL_POOL_50 = [f"/img/hero-{i}.jpg" for i in range(1, 51)]

COMMON = {
    "design_base": {
        "style": "rounded",
        "hero_style": "dark_overlay",
        "footer_style": "dark",
        "nav_style": "sticky_blur",
        "section_order": [
            ["reassurance","prices","services","faq"],
            ["prices","reassurance","services","faq"],
            ["reassurance","services","faq","prices"],
            ["services","reassurance","prices","faq"]
        ],
        "hero_overlay_base": 0.1,
        "hero_overlay_left": 0.5,
        "hero_overlay_mid": 0.18
    },
    "deploy": {"target": "netlify", "clean_urls": True},
    "csv": {
        "_comment": "Place your Canadian cities CSV in the engine_en/ folder.",
        "file": "CanadaCSV.csv",
        "col_city": "city",
        "col_city_ascii": "city_ascii",
        "col_region": "province_name",
        "col_population": "population",
        "filter_provinces": ["Ontario","Alberta","British Columbia"],
        "min_population": 1000
    },
    "performance": {"max_workers": 12},
    "social_proof": {
        "min": 3, "max": 12,
        "min_petite": 8, "max_petite": 25,
        "min_moyenne": 18, "max_moyenne": 60,
        "min_grande": 45, "max_grande": 130
    },
    "premium_cities": [
        "Toronto","Ottawa","Mississauga","Brampton","Hamilton",
        "London","Markham","Vaughan","Kitchener","Windsor",
        "Calgary","Edmonton","Red Deer","Lethbridge","Medicine Hat",
        "Vancouver","Surrey","Burnaby","Richmond","Kelowna","Abbotsford"
    ],
    "form_common": {
        "confirmation_stats": [
            {"value": "24h", "label": "Max response"},
            {"value": "100%", "label": "Free"},
            {"value": "5", "label": "Quotes"}
        ],
        "contact_step": {
            "title": "Your Contact Info",
            "button_text": None,
            "fields": [
                {"type":"text","name":"name","label":"Full Name","placeholder":"John Smith","required":True},
                {"type":"email","name":"email","label":"Email Address","placeholder":"john@example.com","required":True},
                {"type":"tel","name":"phone","label":"Phone Number","placeholder":"416 000-0000","required":True}
            ]
        }
    }
}

NICHES = {
    "plumber": {
        "site": {
            "name": "Plumber Quotes Canada",
            "niche": "plumber-en",
            "domain": "https://plumber-quotes.ca",
            "phone": "",
            "service_label": "Plumbing",
            "schema_type": "HomeAndConstructionBusiness",
            "schema_description": "Licensed plumbers in {city}, {province}. Installation, repair, water heater, drain cleaning. Emergency service available.",
            "price_range": "$$",
            "ga_id": "G-XXXXXXXXXX",
            "form_name": "plumber-quote",
            "lead_system": "external_link"
        },
        "affiliate": {
            "base_url": "https://renoquotes.com/en/form/service/plumbing?utm_campaign=jb",
            "aff_id": "",
            "redirect_path": "/get-plumbing-quote/",
            "badge": "100% Free — No Obligation",
            "button_text": "Get My Free Plumbing Quotes",
            "sublabel": "3 to 5 quotes · Licensed plumbers · Response within 24h"
        },
        "colors": {
            "50": "#eff6ff","100": "#dbeafe","200": "#bfdbfe","300": "#93c5fd",
            "400": "#60a5fa","500": "#3b82f6","600": "#2563eb","700": "#1d4ed8",
            "800": "#1e40af","900": "#1e3a8a",
            "shadow": "rgba(37,99,235,0.35)","shadow_hover": "rgba(37,99,235,0.50)"
        },
        "css_prefix": "pm-",
        "output_dir": "../dist_plumber_en",
        "prices": {
            "grande_ville": {"seuil":50000,"service1_min":3000,"service1_max":15000,"service2_min":800,"service2_max":4000,"service3_min":150,"service3_max":600,"service4_min":100,"service4_max":350},
            "moyenne_ville": {"seuil":15000,"service1_min":2500,"service1_max":12000,"service2_min":700,"service2_max":3500,"service3_min":130,"service3_max":500,"service4_min":90,"service4_max":300},
            "petite_ville": {"seuil":5000,"service1_min":2200,"service1_max":10000,"service2_min":600,"service2_max":3000,"service3_min":120,"service3_max":450,"service4_min":80,"service4_max":280},
            "village": {"seuil":0,"service1_min":2000,"service1_max":9000,"service2_min":500,"service2_max":2500,"service3_min":100,"service3_max":400,"service4_min":70,"service4_max":250}
        },
        "seo": {
            "title_templates": [
                "Plumber {city} — {annee} Prices & Free Quotes | {site_name}",
                "Licensed Plumbers in {city} {annee} — Installation, Repair & Emergency",
                "{city} Plumbing {annee} — Certified Plumbers | {site_name}",
                "{city}: Plumbing {annee} — Up to 5 Free Quotes | {site_name}",
                "Plumbing Quotes {city} {annee} | Local Licensed Plumbers | {site_name}"
            ],
            "desc_templates": [
                "Compare up to 5 free plumbing quotes in {city}. Plumbing installation from ${service1_min}, repairs from ${service3_min}. Response within 24h.",
                "Plumbing in {city} — installation, repair, water heater and drain cleaning. Licensed and insured plumbers. Free quote.",
                "Plumbing prices {city} {annee}: installation from ${service1_min}, repairs from ${service3_min}. Compare 5 local plumber quotes.",
                "Looking for a plumber in {city}? Licensed plumbers — free quote, emergency service, 24h response.",
                "Find the best plumber in {city} in {annee}. Installation, repair, leak detection — free quote, no obligation."
            ]
        },
        "content": {
            "banner_text": "{nb} plumbing jobs submitted this week in {city}",
            "index_heading_spintax": [
                "{site_name} — All of Canada {annee}",
                "{site_name} · {nb_total} cities covered {annee}",
                "Plumbing Across Canada — {nb_regions} provinces | {site_name}"
            ],
            "index_subheading_spintax": [
                "Licensed plumbers — free quote, no obligation, 24h response.",
                "Compare up to 5 quotes from verified local plumbers near you.",
                "Installation · Repair · Water Heater · Drain Cleaning · Response guaranteed within 24h."
            ],
            "region_heading_spintax": [
                "Plumbing in {region} — {nb_villes} cities covered",
                "Licensed Plumbers in {region} — {nb_villes} cities",
                "Plumbing {region} | {nb_villes} {cities|communities|towns} served"
            ],
            "region_intro_spintax": [
                "Find a {licensed plumber|certified plumbing contractor} in your city in {region}.",
                "Compare prices and {get|receive} up to 5 free quotes in {region}.",
                "{nb_villes} cities in {region}. {Free|No-obligation} quote, 24h response."
            ],
            "section_headings": {
                "reassurance": "Why choose {site_name} for your plumbing project in {city}?",
                "prices": "Plumbing prices in {city} — {annee}",
                "services": "Plumbing services available in {city}",
                "faq": "Frequently asked questions — Plumbing in {city}",
                "cta_title": "Need a plumber in {city}?",
                "cta_subtitle": "Free quote · 24h response · Licensed local plumbers",
                "cta_button": "Get My Free Plumbing Quotes",
                "cta_note": "Free · No obligation · Response within 24h",
                "footer_tagline": "{nb_villes_total} cities covered. Plumbing experts across Canada.",
                "footer_region_title": "Plumbing in {region}",
                "nav_badge": "Free Quote",
                "nav_cta": "Get a Price"
            },
            "form_header": {
                "badge": "100% Free Quote",
                "title": "Your plumbing project in {city}",
                "privacy_text": "Your information is confidential — shared only with pre-screened local plumbers."
            },
            "intro_spintax": [
                "Looking for a {plumber|licensed plumbing contractor} in {city}? {Get|Receive} up to 5 {free quotes|personalized estimates} from {licensed plumbers|local experts} within {24 hours|24h}. {Installation|Repair|Water heater|Drain cleaning} — {quality workmanship|licensed and insured}.",
                "{Compare prices|Find the best rate} for {plumbing installation|pipe repair} in {city}. Our {plumbing partners|certified plumbers} {meet|exceed} industry standards with {a written warranty|workmanship guarantee} — {competitive pricing|best value}.",
                "The {best plumbers|top-rated plumbing contractors} in {city} are on our platform. {Installation|Repair|Water heater|Emergency service} — {get|receive} 5 {free|no-obligation} quotes within {24h|24 hours}.",
                "{Burst pipe|Clogged drain|Leaking faucet} in {city}? These issues {require urgent attention|need a certified plumber}. Our {plumbing partners|local specialists} {diagnose and repair|assess and fix} the problem {quickly|as a priority}. {Free quote|No-cost estimate} within {24h|one business day}.",
                "Did you know that {undetected leaks|poor installation} can cause {thousands in water damage|significant structural damage}? In {city}, our {licensed plumbers|certified contractors} {identify and fix|locate and repair} issues before they escalate. Get a {free|no-obligation} quote."
            ],
            "trust_points": [
                {"title": "Licensed & Insured Plumbers", "desc": "Every plumbing partner holds a valid plumbing licence, carries general liability insurance, and has recent references verified.", "icon": "shield"},
                {"title": "100% Free Quote", "desc": "No fees, no obligation. Compare up to 5 plumbing quotes for your project in {city} — completely free.", "icon": "dollar"},
                {"title": "Local Experts in {city}", "desc": "Plumbers who know {city}'s building codes and local regulations — critical factors for proper plumbing work.", "icon": "map"},
                {"title": "Emergency Service Available", "desc": "Burst pipes, major leaks — your contractor partners provide prompt emergency plumbing service in {city}.", "icon": "star"}
            ],
            "prices_display": {
                "subtitle": "Local estimates based on scope, accessibility and materials",
                "main_cards": [
                    {"key_min":"service1_min","key_max":"service1_max","label":"Full Plumbing Installation","sublabel":"New build · Renovation · Complete system","emoji":"🔧","featured":True},
                    {"key_min":"service2_min","key_max":"service2_max","label":"Pipe Repair / Replacement","sublabel":"Burst pipes · Leak repair · Repiping","emoji":"🚿","featured":False},
                    {"key_min":"service3_min","key_max":"service3_max","label":"Plumbing Inspection","sublabel":"Full assessment · Camera inspection · Report","emoji":"🔍","featured":False}
                ],
                "secondary_cards": [
                    {"key_min":"service4_min","key_max":"service4_max","label":"🚰 Drain cleaning / unclogging","suffix":""},
                    {"key_min":"service3_min","key_max":"service3_max","label":"♨️ Water heater installation","suffix":""},
                    {"key_min":"service4_min","key_max":"service4_max","label":"🔧 Faucet / fixture replacement","suffix":""},
                    {"key_min":"service4_min","key_max":"service4_max","label":"🌊 Sump pump installation","suffix":""}
                ]
            },
            "services": [
                {"title":"Plumbing Installation","desc":"Complete plumbing systems for new construction and renovations in {city}. Licensed plumbers, quality materials.","icon":"wrench"},
                {"title":"Pipe Repair & Replacement","desc":"Burst pipes, corroded lines, leaks — fast and reliable repair services in {city}.","icon":"tool"},
                {"title":"Drain Cleaning","desc":"Clogged drains, slow drainage, blockages — professional hydro-jetting and snaking services.","icon":"droplet"},
                {"title":"Water Heater Service","desc":"Installation, repair and replacement of tank and tankless water heaters in {city}.","icon":"flame"},
                {"title":"Leak Detection","desc":"Non-invasive leak detection technology to locate hidden leaks before they cause damage.","icon":"search"},
                {"title":"Emergency Plumbing","desc":"24/7 emergency response for burst pipes, major leaks and flooding in {city}.","icon":"alert"}
            ],
            "faq_items": [
                {"q":"How much does it cost to hire a plumber in {city}?","a":"Plumbing costs in {city} vary by job type. Minor repairs start around ${service4_min}–${service4_max}, while full installations range from ${service1_min} to ${service1_max}. Get 3–5 free quotes to compare.","open":True},
                {"q":"How quickly can a plumber come to {city}?","a":"Most of our partner plumbers in {city} respond within 24 hours for standard jobs. For emergencies (burst pipes, major leaks), same-day or next-day service is typically available.","open":False},
                {"q":"Do I need a permit for plumbing work in {city}?","a":"Most significant plumbing work in {city} requires a permit from the local municipality. Our licensed plumbers handle the permit process as part of the job.","open":False},
                {"q":"What's covered in a plumbing inspection?","a":"A plumbing inspection in {city} covers all visible pipes, fixtures, water heater, drainage system, and water pressure. You'll receive a written report with photos and recommended repairs.","open":False},
                {"q":"How do I prevent frozen pipes in {city}?","a":"In {city}'s cold winters, insulate exposed pipes, maintain minimum heat in your home, and know where your main shut-off valve is. Our plumbers can assess your risk and add insulation where needed.","open":False}
            ]
        },
        "form_steps": [
            {"title":"Service Type","button_text":"Continue","fields":[{"type":"radio_cards","name":"project-type","label":"What plumbing service do you need?","required":True,"error_id":"project-error","options":[{"value":"installation","emoji":"🔧","label":"New Installation"},{"value":"repair","emoji":"🚿","label":"Repair / Leak"},{"value":"drain","emoji":"🚰","label":"Drain Cleaning"},{"value":"water-heater","emoji":"♨️","label":"Water Heater"},{"value":"emergency","emoji":"🚨","label":"Emergency — ASAP"}]}]},
            {"title":"Your Property","button_text":"Continue","fields":[{"type":"select","name":"property-type","label":"Property Type","required":True,"options":[{"value":"house","label":"Single-family House"},{"value":"condo","label":"Condo / Townhouse"},{"value":"multi","label":"Duplex / Triplex"},{"value":"commercial","label":"Commercial / Industrial"},{"value":"other","label":"Other"}]}]},
            {"title":"Timeline","button_text":"Continue","fields":[{"type":"radio_cards","name":"timeline","label":"When do you need the work done?","required":True,"error_id":"timeline-error","options":[{"value":"urgent","emoji":"🚨","label":"Emergency — ASAP"},{"value":"this-week","emoji":"📅","label":"This Week"},{"value":"this-month","emoji":"🗓️","label":"This Month"},{"value":"planning","emoji":"💭","label":"Planning Ahead"}]}]}
        ],
        "authority_resources": [
            {"url":"https://en.wikipedia.org/wiki/{city}","ancre":"{city} — Wikipedia","hook":"Background on {city}: population, climate and building codes — key factors for plumbing system requirements."},
            {"url":"https://www.cca-acc.com/","ancre":"Canadian Construction Association","hook":"Industry standards and best practices for plumbing contractors in {city}."}
        ],
        "images_alt_templates": [
            "Licensed plumber working in {city}, {province}",
            "Plumbing repair in {city} — professional plumbers",
            "Pipe installation in {city}",
            "Certified plumber on a job in {city}",
            "Plumbing renovation in {city}, {province}"
        ]
    },

    "kitchen": {
        "site": {
            "name": "Kitchen Quotes Canada",
            "niche": "kitchen-en",
            "domain": "https://kitchen-quotes.ca",
            "phone": "",
            "service_label": "Kitchen Renovation",
            "schema_type": "HomeAndConstructionBusiness",
            "schema_description": "Kitchen renovation contractors in {city}, {province}. Cabinets, countertops, islands, full remodels. Licensed and insured.",
            "price_range": "$$$",
            "ga_id": "G-XXXXXXXXXX",
            "form_name": "kitchen-quote",
            "lead_system": "external_link"
        },
        "affiliate": {
            "base_url": "https://renoquotes.com/en/form/service/kitchen-renovation?utm_campaign=jb",
            "aff_id": "",
            "redirect_path": "/get-kitchen-quote/",
            "badge": "100% Free — No Obligation",
            "button_text": "Get My Free Kitchen Quotes",
            "sublabel": "3 to 5 quotes · Local renovation experts · Response within 24h"
        },
        "colors": {
            "50": "#fff7ed","100": "#ffedd5","200": "#fed7aa","300": "#fdba74",
            "400": "#fb923c","500": "#f97316","600": "#ea580c","700": "#c2410c",
            "800": "#9a3412","900": "#7c2d12",
            "shadow": "rgba(234,88,12,0.35)","shadow_hover": "rgba(234,88,12,0.50)"
        },
        "css_prefix": "kt-",
        "output_dir": "../dist_kitchen_en",
        "prices": {
            "grande_ville": {"seuil":50000,"service1_min":25000,"service1_max":80000,"service2_min":10000,"service2_max":30000,"service3_min":3000,"service3_max":12000,"service4_min":1500,"service4_max":5000},
            "moyenne_ville": {"seuil":15000,"service1_min":20000,"service1_max":65000,"service2_min":8000,"service2_max":25000,"service3_min":2500,"service3_max":10000,"service4_min":1200,"service4_max":4000},
            "petite_ville": {"seuil":5000,"service1_min":18000,"service1_max":55000,"service2_min":7000,"service2_max":22000,"service3_min":2000,"service3_max":8000,"service4_min":1000,"service4_max":3500},
            "village": {"seuil":0,"service1_min":15000,"service1_max":45000,"service2_min":6000,"service2_max":18000,"service3_min":1800,"service3_max":7000,"service4_min":800,"service4_max":3000}
        },
        "seo": {
            "title_templates": [
                "Kitchen Renovation {city} — {annee} Prices & Free Quotes | {site_name}",
                "Kitchen Remodeling Contractors in {city} {annee} — Cabinets, Countertops & More",
                "{city} Kitchen Renovation {annee} — Licensed Contractors | {site_name}",
                "{city}: Kitchen Remodel {annee} — Up to 5 Free Quotes | {site_name}",
                "Kitchen Renovation Quotes {city} {annee} | Local Experts | {site_name}"
            ],
            "desc_templates": [
                "Compare up to 5 free kitchen renovation quotes in {city}. Full remodel from ${service1_min}, cabinet replacement from ${service3_min}. Response within 24h.",
                "Kitchen renovation in {city} — full remodel, cabinets, countertops, islands. Licensed contractors. Free quote.",
                "Kitchen renovation prices {city} {annee}: full remodel from ${service1_min}. Compare 5 local contractor quotes.",
                "Looking for a kitchen contractor in {city}? Licensed renovation experts — free quote, 24h response.",
                "Find the best kitchen renovation contractor in {city} in {annee}. Full remodel, cabinets, countertops — free quote."
            ]
        },
        "content": {
            "banner_text": "{nb} kitchen renovation projects submitted this week in {city}",
            "index_heading_spintax": [
                "{site_name} — All of Canada {annee}",
                "{site_name} · {nb_total} cities covered {annee}",
                "Kitchen Renovation Across Canada — {nb_regions} provinces | {site_name}"
            ],
            "index_subheading_spintax": [
                "Licensed kitchen contractors — free quote, no obligation, 24h response.",
                "Compare up to 5 quotes from verified kitchen renovation experts near you.",
                "Full Remodel · Cabinets · Countertops · Islands · Response guaranteed within 24h."
            ],
            "region_heading_spintax": [
                "Kitchen Renovation in {region} — {nb_villes} cities covered",
                "Kitchen Contractors in {region} — {nb_villes} cities",
                "Kitchen Renovation {region} | {nb_villes} {cities|communities|towns} served"
            ],
            "region_intro_spintax": [
                "Find a {licensed kitchen contractor|certified renovation expert} in your city in {region}.",
                "Compare prices and {get|receive} up to 5 free quotes in {region}.",
                "{nb_villes} cities in {region}. {Free|No-obligation} quote, 24h response."
            ],
            "section_headings": {
                "reassurance": "Why choose {site_name} for your kitchen renovation in {city}?",
                "prices": "Kitchen renovation prices in {city} — {annee}",
                "services": "Kitchen renovation services available in {city}",
                "faq": "Frequently asked questions — Kitchen renovation in {city}",
                "cta_title": "Ready to renovate your kitchen in {city}?",
                "cta_subtitle": "Free quote · 24h response · Local licensed contractors",
                "cta_button": "Get My Free Kitchen Quotes",
                "cta_note": "Free · No obligation · Response within 24h",
                "footer_tagline": "{nb_villes_total} cities covered. Kitchen renovation experts across Canada.",
                "footer_region_title": "Kitchen Renovation in {region}",
                "nav_badge": "Free Quote",
                "nav_cta": "Get a Price"
            },
            "form_header": {
                "badge": "100% Free Quote",
                "title": "Your kitchen renovation in {city}",
                "privacy_text": "Your information is confidential — shared only with pre-screened local contractors."
            },
            "intro_spintax": [
                "Looking for a {kitchen renovation contractor|certified kitchen remodeler} in {city}? {Get|Receive} up to 5 {free quotes|personalized estimates} from {licensed contractors|local experts} within {24 hours|24h}. {Full remodel|Cabinet replacement|Countertops|Islands} — {quality craftsmanship|licensed and insured}.",
                "{Compare prices|Find the best rate} for {kitchen renovation|kitchen remodeling} in {city}. Our {renovation partners|certified contractors} {transform|upgrade} kitchens with {quality materials|premium finishes} — {competitive pricing|best value}.",
                "The {best kitchen contractors|top-rated renovation experts} in {city} are on our platform. {Full remodel|Cabinet replacement|Countertop upgrade} — {get|receive} 5 {free|no-obligation} quotes within {24h|24 hours}.",
                "Dreaming of a {new kitchen|modern kitchen|updated kitchen} in {city}? Our {renovation partners|local specialists} {design and build|plan and execute} kitchen transformations that {increase home value|improve daily living}. {Free quote|No-cost estimate} within {24h|one business day}.",
                "Did you know that a {kitchen renovation|kitchen remodel} in {city} can {increase your home's value|offer the best ROI} of any renovation? Our {licensed contractors|certified kitchen experts} {plan and execute|design and deliver} projects {on time and on budget|with quality guarantees}."
            ],
            "trust_points": [
                {"title": "Licensed & Insured Contractors", "desc": "Every renovation partner is fully licensed, carries liability insurance, and has verified references in {city}.", "icon": "shield"},
                {"title": "100% Free Quote", "desc": "No fees, no obligation. Compare up to 5 kitchen renovation quotes in {city} — completely free.", "icon": "dollar"},
                {"title": "Local Design Expertise in {city}", "desc": "Contractors who know {city}'s style trends, material suppliers, and permit requirements for kitchen renovations.", "icon": "map"},
                {"title": "Quality Guaranteed", "desc": "From cabinets to countertops — your contractors stand behind their work with written warranties.", "icon": "star"}
            ],
            "prices_display": {
                "subtitle": "Estimates based on kitchen size, materials and scope of work",
                "main_cards": [
                    {"key_min":"service1_min","key_max":"service1_max","label":"Full Kitchen Renovation","sublabel":"Demo · Cabinets · Countertops · Flooring · Appliances","emoji":"🍳","featured":True},
                    {"key_min":"service2_min","key_max":"service2_max","label":"Cabinet Replacement","sublabel":"New cabinets · Hardware · Installation","emoji":"🪵","featured":False},
                    {"key_min":"service3_min","key_max":"service3_max","label":"Countertop Installation","sublabel":"Quartz · Granite · Laminate · Full install","emoji":"✨","featured":False}
                ],
                "secondary_cards": [
                    {"key_min":"service4_min","key_max":"service4_max","label":"💎 Kitchen island addition","suffix":""},
                    {"key_min":"service3_min","key_max":"service3_max","label":"🍽️ Backsplash installation","suffix":""},
                    {"key_min":"service4_min","key_max":"service4_max","label":"🎨 Cabinet refinishing / painting","suffix":""},
                    {"key_min":"service4_min","key_max":"service4_max","label":"💡 Under-cabinet lighting","suffix":""}
                ]
            },
            "services": [
                {"title":"Full Kitchen Renovation","desc":"Complete kitchen remodels in {city} — from demo to final finish. Cabinets, countertops, flooring, lighting and appliances.","icon":"wrench"},
                {"title":"Cabinet Installation","desc":"Custom and semi-custom kitchen cabinets. Full installation including hardware and trim in {city}.","icon":"tool"},
                {"title":"Countertop Installation","desc":"Quartz, granite, marble, laminate — professional templating and installation in {city}.","icon":"droplet"},
                {"title":"Kitchen Islands","desc":"Custom kitchen island design and installation to maximize your kitchen's functionality and value.","icon":"flame"},
                {"title":"Backsplash & Tile","desc":"Tile selection, design and installation. Backsplash, floor tile and feature walls in {city}.","icon":"search"},
                {"title":"Appliance Integration","desc":"Built-in appliance planning and installation — seamless integration with your new kitchen design.","icon":"alert"}
            ],
            "faq_items": [
                {"q":"How much does a kitchen renovation cost in {city}?","a":"Kitchen renovation costs in {city} vary widely. A basic refresh starts around ${service3_min}–${service2_min}, while a full high-end renovation can reach ${service1_max} or more. Get 3–5 free quotes to compare real prices.","open":True},
                {"q":"How long does a kitchen renovation take in {city}?","a":"Most kitchen renovations in {city} take 4–8 weeks from demo to completion, depending on scope. Full custom renovations with structural changes may take 10–14 weeks.","open":False},
                {"q":"Do I need a permit for my kitchen renovation in {city}?","a":"Structural changes, electrical work and plumbing modifications typically require permits in {city}. Your contractor will handle the permitting process as part of the project.","open":False},
                {"q":"What's the best material for kitchen countertops in {city}?","a":"Quartz is the most popular choice in {city} for its durability and low maintenance. Granite offers a unique natural look. Laminate provides excellent value. Your contractor can show you samples and pricing for each option.","open":False},
                {"q":"How do I choose the right kitchen contractor in {city}?","a":"Look for contractors who are licensed, insured, and have completed similar kitchen renovations in {city}. Request references, review their portfolio, and compare at least 3 detailed quotes before deciding.","open":False}
            ]
        },
        "form_steps": [
            {"title":"Project Scope","button_text":"Continue","fields":[{"type":"radio_cards","name":"project-type","label":"What type of kitchen work do you need?","required":True,"error_id":"project-error","options":[{"value":"full-reno","emoji":"🏠","label":"Full Kitchen Renovation"},{"value":"cabinets","emoji":"🪵","label":"Cabinet Replacement"},{"value":"countertops","emoji":"✨","label":"Countertop Only"},{"value":"island","emoji":"🍳","label":"Island Addition"},{"value":"refresh","emoji":"🎨","label":"Cosmetic Refresh"}]}]},
            {"title":"Your Kitchen","button_text":"Continue","fields":[{"type":"select","name":"kitchen-size","label":"Kitchen Size","required":True,"options":[{"value":"small","label":"Small (under 100 sq ft)"},{"value":"medium","label":"Medium (100–150 sq ft)"},{"value":"large","label":"Large (150–200 sq ft)"},{"value":"xlarge","label":"Extra Large (200+ sq ft)"}]},{"type":"select","name":"property-type","label":"Property Type","required":True,"options":[{"value":"house","label":"Single-family House"},{"value":"condo","label":"Condo / Townhouse"},{"value":"multi","label":"Duplex / Triplex"},{"value":"other","label":"Other"}]}]},
            {"title":"Timeline","button_text":"Continue","fields":[{"type":"radio_cards","name":"timeline","label":"When do you want to start?","required":True,"error_id":"timeline-error","options":[{"value":"asap","emoji":"🚀","label":"As Soon as Possible"},{"value":"1-3months","emoji":"📅","label":"Within 1–3 Months"},{"value":"3-6months","emoji":"🗓️","label":"3–6 Months"},{"value":"planning","emoji":"💭","label":"Still Planning"}]}]}
        ],
        "authority_resources": [
            {"url":"https://en.wikipedia.org/wiki/{city}","ancre":"{city} — Wikipedia","hook":"Background on {city}: demographics, housing and neighbourhood styles — useful context for your kitchen renovation."},
            {"url":"https://www.hpba.org/","ancre":"HPBA — Home Performance Building Association","hook":"Standards and certifications for home renovation contractors in {city}."}
        ],
        "images_alt_templates": [
            "Modern kitchen renovation in {city}, {province}",
            "Kitchen remodel in {city} — new cabinets and countertops",
            "Custom kitchen design in {city}",
            "Kitchen renovation completed in {city}",
            "New kitchen installation in {city}, {province}"
        ]
    },

    "bathroom": {
        "site": {
            "name": "Bathroom Quotes Canada",
            "niche": "bathroom-en",
            "domain": "https://bathroom-quotes.ca",
            "phone": "",
            "service_label": "Bathroom Renovation",
            "schema_type": "HomeAndConstructionBusiness",
            "schema_description": "Bathroom renovation contractors in {city}, {province}. Full remodel, tiling, fixtures, shower installation. Licensed and insured.",
            "price_range": "$$$",
            "ga_id": "G-XXXXXXXXXX",
            "form_name": "bathroom-quote",
            "lead_system": "external_link"
        },
        "affiliate": {
            "base_url": "https://renoquotes.com/en/form/service/bathroom-renovation?utm_campaign=jb",
            "aff_id": "",
            "redirect_path": "/get-bathroom-quote/",
            "badge": "100% Free — No Obligation",
            "button_text": "Get My Free Bathroom Quotes",
            "sublabel": "3 to 5 quotes · Local renovation experts · Response within 24h"
        },
        "colors": {
            "50": "#f0fdfa","100": "#ccfbf1","200": "#99f6e4","300": "#5eead4",
            "400": "#2dd4bf","500": "#14b8a6","600": "#0d9488","700": "#0f766e",
            "800": "#115e59","900": "#134e4a",
            "shadow": "rgba(13,148,136,0.35)","shadow_hover": "rgba(13,148,136,0.50)"
        },
        "css_prefix": "bm-",
        "output_dir": "../dist_bathroom_en",
        "prices": {
            "grande_ville": {"seuil":50000,"service1_min":15000,"service1_max":50000,"service2_min":5000,"service2_max":20000,"service3_min":2000,"service3_max":8000,"service4_min":500,"service4_max":2500},
            "moyenne_ville": {"seuil":15000,"service1_min":12000,"service1_max":40000,"service2_min":4000,"service2_max":16000,"service3_min":1800,"service3_max":7000,"service4_min":450,"service4_max":2000},
            "petite_ville": {"seuil":5000,"service1_min":10000,"service1_max":35000,"service2_min":3500,"service2_max":14000,"service3_min":1500,"service3_max":6000,"service4_min":400,"service4_max":1800},
            "village": {"seuil":0,"service1_min":9000,"service1_max":30000,"service2_min":3000,"service2_max":12000,"service3_min":1200,"service3_max":5000,"service4_min":350,"service4_max":1500}
        },
        "seo": {
            "title_templates": [
                "Bathroom Renovation {city} — {annee} Prices & Free Quotes | {site_name}",
                "Bathroom Remodeling Contractors in {city} {annee} — Tiling, Fixtures & More",
                "{city} Bathroom Renovation {annee} — Licensed Contractors | {site_name}",
                "{city}: Bathroom Remodel {annee} — Up to 5 Free Quotes | {site_name}",
                "Bathroom Renovation Quotes {city} {annee} | Local Experts | {site_name}"
            ],
            "desc_templates": [
                "Compare up to 5 free bathroom renovation quotes in {city}. Full remodel from ${service1_min}, tiling from ${service3_min}. Response within 24h.",
                "Bathroom renovation in {city} — full remodel, tiling, shower, fixtures. Licensed contractors. Free quote.",
                "Bathroom renovation prices {city} {annee}: full remodel from ${service1_min}. Compare 5 local contractor quotes.",
                "Looking for a bathroom contractor in {city}? Licensed renovation experts — free quote, 24h response.",
                "Find the best bathroom renovation contractor in {city} in {annee}. Full remodel, tile, fixtures — free quote."
            ]
        },
        "content": {
            "banner_text": "{nb} bathroom renovation projects submitted this week in {city}",
            "index_heading_spintax": [
                "{site_name} — All of Canada {annee}",
                "{site_name} · {nb_total} cities covered {annee}",
                "Bathroom Renovation Across Canada — {nb_regions} provinces | {site_name}"
            ],
            "index_subheading_spintax": [
                "Licensed bathroom contractors — free quote, no obligation, 24h response.",
                "Compare up to 5 quotes from verified bathroom renovation experts near you.",
                "Full Remodel · Tiling · Shower · Fixtures · Response guaranteed within 24h."
            ],
            "region_heading_spintax": [
                "Bathroom Renovation in {region} — {nb_villes} cities covered",
                "Bathroom Contractors in {region} — {nb_villes} cities",
                "Bathroom Renovation {region} | {nb_villes} {cities|communities|towns} served"
            ],
            "region_intro_spintax": [
                "Find a {licensed bathroom contractor|certified renovation expert} in your city in {region}.",
                "Compare prices and {get|receive} up to 5 free quotes in {region}.",
                "{nb_villes} cities in {region}. {Free|No-obligation} quote, 24h response."
            ],
            "section_headings": {
                "reassurance": "Why choose {site_name} for your bathroom renovation in {city}?",
                "prices": "Bathroom renovation prices in {city} — {annee}",
                "services": "Bathroom renovation services available in {city}",
                "faq": "Frequently asked questions — Bathroom renovation in {city}",
                "cta_title": "Ready to renovate your bathroom in {city}?",
                "cta_subtitle": "Free quote · 24h response · Local licensed contractors",
                "cta_button": "Get My Free Bathroom Quotes",
                "cta_note": "Free · No obligation · Response within 24h",
                "footer_tagline": "{nb_villes_total} cities covered. Bathroom renovation experts across Canada.",
                "footer_region_title": "Bathroom Renovation in {region}",
                "nav_badge": "Free Quote",
                "nav_cta": "Get a Price"
            },
            "form_header": {
                "badge": "100% Free Quote",
                "title": "Your bathroom renovation in {city}",
                "privacy_text": "Your information is confidential — shared only with pre-screened local contractors."
            },
            "intro_spintax": [
                "Looking for a {bathroom renovation contractor|certified bathroom remodeler} in {city}? {Get|Receive} up to 5 {free quotes|personalized estimates} from {licensed contractors|local experts} within {24 hours|24h}. {Full remodel|Tiling|Shower installation|Fixture replacement} — {quality craftsmanship|licensed and insured}.",
                "{Compare prices|Find the best rate} for {bathroom renovation|bathroom remodeling} in {city}. Our {renovation partners|certified contractors} {transform|upgrade} bathrooms with {premium tile|quality fixtures} — {competitive pricing|best value}.",
                "The {best bathroom contractors|top-rated renovation experts} in {city} are on our platform. {Full remodel|Walk-in shower|Freestanding tub|Heated floors} — {get|receive} 5 {free|no-obligation} quotes within {24h|24 hours}.",
                "Dreaming of a {spa-like bathroom|modern bathroom|updated ensuite} in {city}? Our {renovation partners|local specialists} {design and build|plan and execute} bathroom transformations that {increase home value|add daily luxury}. {Free quote|No-cost estimate} within {24h|one business day}."
            ],
            "trust_points": [
                {"title": "Licensed & Insured Contractors", "desc": "Every renovation partner is fully licensed, carries liability insurance, and has verified references in {city}.", "icon": "shield"},
                {"title": "100% Free Quote", "desc": "No fees, no obligation. Compare up to 5 bathroom renovation quotes in {city} — completely free.", "icon": "dollar"},
                {"title": "Tile & Waterproofing Expertise", "desc": "Proper waterproofing is critical in bathrooms. Our contractors in {city} are experts in membrane installation and tile work.", "icon": "map"},
                {"title": "Satisfaction Guaranteed", "desc": "From tile to fixtures — your contractors stand behind their work with written workmanship warranties.", "icon": "star"}
            ],
            "prices_display": {
                "subtitle": "Estimates based on bathroom size, finishes and scope of work",
                "main_cards": [
                    {"key_min":"service1_min","key_max":"service1_max","label":"Full Bathroom Renovation","sublabel":"Demo · Tile · Shower · Fixtures · Vanity","emoji":"🛁","featured":True},
                    {"key_min":"service2_min","key_max":"service2_max","label":"Shower Installation","sublabel":"Custom shower · Tile · Glass door · Fixtures","emoji":"🚿","featured":False},
                    {"key_min":"service3_min","key_max":"service3_max","label":"Tile Installation","sublabel":"Floor tile · Wall tile · Grouting · Waterproofing","emoji":"🔲","featured":False}
                ],
                "secondary_cards": [
                    {"key_min":"service4_min","key_max":"service4_max","label":"🛁 Bathtub replacement","suffix":""},
                    {"key_min":"service3_min","key_max":"service3_max","label":"🪞 Vanity & mirror installation","suffix":""},
                    {"key_min":"service4_min","key_max":"service4_max","label":"💧 Fixture replacement (faucets/toilet)","suffix":""},
                    {"key_min":"service3_min","key_max":"service3_max","label":"🌡️ Heated floor installation","suffix":""}
                ]
            },
            "services": [
                {"title":"Full Bathroom Renovation","desc":"Complete bathroom remodels in {city} — from demo to final finish. Tile, shower, vanity, fixtures and lighting.","icon":"wrench"},
                {"title":"Shower Installation","desc":"Custom walk-in showers with tile, glass doors and premium fixtures. Installed by certified contractors in {city}.","icon":"tool"},
                {"title":"Tile & Waterproofing","desc":"Floor and wall tile installation with professional membrane waterproofing. Essential for lasting results.","icon":"droplet"},
                {"title":"Vanity & Fixtures","desc":"Vanity installation, mirror, faucets, toilet and lighting — all coordinated for a cohesive look.","icon":"flame"},
                {"title":"Bathtub Replacement","desc":"Freestanding tubs, soaker tubs, walk-in showers — upgrade your tub to match your new bathroom design.","icon":"search"},
                {"title":"Heated Floors","desc":"In-floor radiant heating installation — the ultimate comfort upgrade for your bathroom in {city}.","icon":"alert"}
            ],
            "faq_items": [
                {"q":"How much does a bathroom renovation cost in {city}?","a":"Bathroom renovation costs in {city} range from ${service3_min}–${service2_min} for a partial refresh to ${service1_min}–${service1_max} for a full master ensuite renovation. Get 3–5 free quotes to compare real prices.","open":True},
                {"q":"How long does a bathroom renovation take in {city}?","a":"A typical bathroom renovation in {city} takes 2–4 weeks for a standard bathroom, and 4–6 weeks for a larger master ensuite with custom tile work.","open":False},
                {"q":"Do I need a permit for my bathroom renovation in {city}?","a":"Moving plumbing, adding electrical circuits or structural changes require permits in {city}. Simple cosmetic renovations like tile replacement typically don't. Your contractor will advise you.","open":False},
                {"q":"What's the best tile for a bathroom in {city}?","a":"Porcelain tile is the most popular choice in {city} for its durability, water resistance and wide range of styles. Ceramic is a cost-effective alternative. Natural stone requires sealing but offers a premium look.","open":False},
                {"q":"Should I renovate my bathroom or do a tub-to-shower conversion?","a":"A tub-to-shower conversion in {city} costs ${service2_min}–${service2_max} and is popular for main bathrooms. Full renovation offers better ROI if you're updating multiple elements. Your contractor can advise based on your goals and budget.","open":False}
            ]
        },
        "form_steps": [
            {"title":"Project Type","button_text":"Continue","fields":[{"type":"radio_cards","name":"project-type","label":"What type of bathroom work do you need?","required":True,"error_id":"project-error","options":[{"value":"full-reno","emoji":"🛁","label":"Full Bathroom Renovation"},{"value":"shower","emoji":"🚿","label":"Shower Installation"},{"value":"tile","emoji":"🔲","label":"Tiling Only"},{"value":"fixtures","emoji":"💧","label":"Fixture Replacement"},{"value":"conversion","emoji":"✨","label":"Tub-to-Shower Conversion"}]}]},
            {"title":"Your Bathroom","button_text":"Continue","fields":[{"type":"select","name":"bathroom-type","label":"Bathroom Type","required":True,"options":[{"value":"main","label":"Main Bathroom"},{"value":"ensuite","label":"Master Ensuite"},{"value":"powder","label":"Powder Room"},{"value":"basement","label":"Basement Bathroom"},{"value":"other","label":"Other"}]},{"type":"select","name":"property-type","label":"Property Type","required":True,"options":[{"value":"house","label":"Single-family House"},{"value":"condo","label":"Condo / Townhouse"},{"value":"multi","label":"Duplex / Triplex"},{"value":"other","label":"Other"}]}]},
            {"title":"Timeline","button_text":"Continue","fields":[{"type":"radio_cards","name":"timeline","label":"When do you want to start?","required":True,"error_id":"timeline-error","options":[{"value":"asap","emoji":"🚀","label":"As Soon as Possible"},{"value":"1-3months","emoji":"📅","label":"Within 1–3 Months"},{"value":"3-6months","emoji":"🗓️","label":"3–6 Months"},{"value":"planning","emoji":"💭","label":"Still Planning"}]}]}
        ],
        "authority_resources": [
            {"url":"https://en.wikipedia.org/wiki/{city}","ancre":"{city} — Wikipedia","hook":"Background on {city}: demographics, housing and building regulations."},
            {"url":"https://www.cca-acc.com/","ancre":"Canadian Construction Association","hook":"Standards and certifications for renovation contractors in {city}."}
        ],
        "images_alt_templates": [
            "Modern bathroom renovation in {city}, {province}",
            "Bathroom remodel in {city} — new tile and shower",
            "Custom bathroom design in {city}",
            "Bathroom renovation completed in {city}",
            "New bathroom installation in {city}, {province}"
        ]
    },

    "electrician": {
        "site": {
            "name": "Electrician Quotes Canada",
            "niche": "electrician-en",
            "domain": "https://electrician-quotes.ca",
            "phone": "",
            "service_label": "Electrical",
            "schema_type": "HomeAndConstructionBusiness",
            "schema_description": "Licensed electricians in {city}, {province}. Panel upgrades, wiring, EV chargers, electrical repairs. Licensed and insured.",
            "price_range": "$$",
            "ga_id": "G-XXXXXXXXXX",
            "form_name": "electrician-quote",
            "lead_system": "external_link"
        },
        "affiliate": {
            "base_url": "https://renoquotes.com/en/form/service/electrical?utm_campaign=jb",
            "aff_id": "",
            "redirect_path": "/get-electrician-quote/",
            "badge": "100% Free — No Obligation",
            "button_text": "Get My Free Electrical Quotes",
            "sublabel": "3 to 5 quotes · Licensed electricians · Response within 24h"
        },
        "colors": {
            "50": "#fefce8","100": "#fef9c3","200": "#fef08a","300": "#fde047",
            "400": "#facc15","500": "#eab308","600": "#ca8a04","700": "#a16207",
            "800": "#854d0e","900": "#713f12",
            "shadow": "rgba(202,138,4,0.35)","shadow_hover": "rgba(202,138,4,0.50)"
        },
        "css_prefix": "ec-",
        "output_dir": "../dist_electrician_en",
        "prices": {
            "grande_ville": {"seuil":50000,"service1_min":3000,"service1_max":12000,"service2_min":1500,"service2_max":5000,"service3_min":200,"service3_max":800,"service4_min":100,"service4_max":400},
            "moyenne_ville": {"seuil":15000,"service1_min":2500,"service1_max":10000,"service2_min":1200,"service2_max":4000,"service3_min":180,"service3_max":700,"service4_min":90,"service4_max":350},
            "petite_ville": {"seuil":5000,"service1_min":2200,"service1_max":9000,"service2_min":1000,"service2_max":3500,"service3_min":150,"service3_max":600,"service4_min":80,"service4_max":300},
            "village": {"seuil":0,"service1_min":2000,"service1_max":8000,"service2_min":900,"service2_max":3000,"service3_min":130,"service3_max":500,"service4_min":70,"service4_max":280}
        },
        "seo": {
            "title_templates": [
                "Electrician {city} — {annee} Prices & Free Quotes | {site_name}",
                "Licensed Electricians in {city} {annee} — Panel Upgrades, Wiring & EV Chargers",
                "{city} Electrician {annee} — Certified Electrical Contractors | {site_name}",
                "{city}: Electrical Work {annee} — Up to 5 Free Quotes | {site_name}",
                "Electrician Quotes {city} {annee} | Licensed Local Electricians | {site_name}"
            ],
            "desc_templates": [
                "Compare up to 5 free electrician quotes in {city}. Panel upgrades from ${service1_min}, repairs from ${service3_min}. Response within 24h.",
                "Electrical services in {city} — panel upgrades, wiring, EV chargers, repairs. Licensed and insured electricians. Free quote.",
                "Electrician prices {city} {annee}: panel upgrade from ${service1_min}. Compare 5 local electrician quotes.",
                "Looking for a licensed electrician in {city}? Certified electrical contractors — free quote, 24h response.",
                "Find the best electrician in {city} in {annee}. Panel upgrade, wiring, EV charger — free quote, no obligation."
            ]
        },
        "content": {
            "banner_text": "{nb} electrical jobs submitted this week in {city}",
            "index_heading_spintax": [
                "{site_name} — All of Canada {annee}",
                "{site_name} · {nb_total} cities covered {annee}",
                "Electrical Services Across Canada — {nb_regions} provinces | {site_name}"
            ],
            "index_subheading_spintax": [
                "Licensed electricians — free quote, no obligation, 24h response.",
                "Compare up to 5 quotes from verified local electricians near you.",
                "Panel Upgrades · Wiring · EV Chargers · Repairs · Response guaranteed within 24h."
            ],
            "region_heading_spintax": [
                "Electricians in {region} — {nb_villes} cities covered",
                "Licensed Electricians in {region} — {nb_villes} cities",
                "Electrical Services {region} | {nb_villes} {cities|communities|towns} served"
            ],
            "region_intro_spintax": [
                "Find a {licensed electrician|certified electrical contractor} in your city in {region}.",
                "Compare prices and {get|receive} up to 5 free quotes in {region}.",
                "{nb_villes} cities in {region}. {Free|No-obligation} quote, 24h response."
            ],
            "section_headings": {
                "reassurance": "Why choose {site_name} for your electrical work in {city}?",
                "prices": "Electrician prices in {city} — {annee}",
                "services": "Electrical services available in {city}",
                "faq": "Frequently asked questions — Electricians in {city}",
                "cta_title": "Need a licensed electrician in {city}?",
                "cta_subtitle": "Free quote · 24h response · Certified local electricians",
                "cta_button": "Get My Free Electrical Quotes",
                "cta_note": "Free · No obligation · Response within 24h",
                "footer_tagline": "{nb_villes_total} cities covered. Electrical experts across Canada.",
                "footer_region_title": "Electricians in {region}",
                "nav_badge": "Free Quote",
                "nav_cta": "Get a Price"
            },
            "form_header": {
                "badge": "100% Free Quote",
                "title": "Your electrical project in {city}",
                "privacy_text": "Your information is confidential — shared only with pre-screened licensed electricians."
            },
            "intro_spintax": [
                "Looking for a {licensed electrician|certified electrical contractor} in {city}? {Get|Receive} up to 5 {free quotes|personalized estimates} from {licensed electricians|local experts} within {24 hours|24h}. {Panel upgrade|New wiring|EV charger|Electrical repair} — {safe and code-compliant|licensed and insured}.",
                "{Compare prices|Find the best rate} for {electrical work|panel upgrades} in {city}. Our {electrician partners|certified contractors} {meet|exceed} electrical code with {permitted work|inspected installations} — {competitive pricing|best value}.",
                "The {best electricians|top-rated electrical contractors} in {city} are on our platform. {Panel upgrade|New circuits|EV charger installation|Rewiring} — {get|receive} 5 {free|no-obligation} quotes within {24h|24 hours}.",
                "Planning a {home addition|renovation|EV purchase} in {city}? Your electrical panel may need an upgrade. Our {licensed electricians|certified contractors} {assess and upgrade|evaluate and expand} your electrical capacity safely. {Free quote|No-cost estimate} within {24h|one business day}.",
                "Did you know that {outdated wiring|aluminum wiring|overloaded panels} are a leading cause of {house fires|electrical hazards} in {city}? Our {licensed electricians|certified contractors} {inspect, repair and upgrade|assess and modernize} your electrical system safely and to code."
            ],
            "trust_points": [
                {"title": "Licensed Master Electricians", "desc": "Every electrician partner holds a valid provincial licence, carries liability insurance, and pulls proper permits for all work in {city}.", "icon": "shield"},
                {"title": "100% Free Quote", "desc": "No fees, no obligation. Compare up to 5 electrician quotes for your project in {city} — completely free.", "icon": "dollar"},
                {"title": "Code-Compliant Work", "desc": "All electrical work in {city} is performed to the Canadian Electrical Code and inspected where required. Your safety is guaranteed.", "icon": "map"},
                {"title": "Fast Response", "desc": "Most of our electrician partners in {city} respond within 24 hours. Same-day service available for urgent electrical issues.", "icon": "star"}
            ],
            "prices_display": {
                "subtitle": "Local estimates based on scope, panel size and materials",
                "main_cards": [
                    {"key_min":"service1_min","key_max":"service1_max","label":"Electrical Panel Upgrade","sublabel":"200A upgrade · New breakers · Grounding · Permit","emoji":"⚡","featured":True},
                    {"key_min":"service2_min","key_max":"service2_max","label":"Wiring / Rewiring","sublabel":"New circuits · Renovation wiring · Knob-and-tube removal","emoji":"🔌","featured":False},
                    {"key_min":"service3_min","key_max":"service3_max","label":"Electrical Inspection","sublabel":"Full assessment · ESA report · Deficiency list","emoji":"🔍","featured":False}
                ],
                "secondary_cards": [
                    {"key_min":"service3_min","key_max":"service3_max","label":"🚗 EV charger installation","suffix":""},
                    {"key_min":"service4_min","key_max":"service4_max","label":"⚡ Outlet & switch replacement","suffix":""},
                    {"key_min":"service4_min","key_max":"service4_max","label":"💡 Pot light installation","suffix":""},
                    {"key_min":"service3_min","key_max":"service3_max","label":"🏠 Generator connection / transfer switch","suffix":""}
                ]
            },
            "services": [
                {"title":"Panel Upgrades","desc":"Electrical panel upgrades to 200A or 400A in {city}. All work permitted and inspected to the Canadian Electrical Code.","icon":"wrench"},
                {"title":"Residential Wiring","desc":"New construction, renovation and addition wiring in {city}. Circuits, outlets, switches and more.","icon":"tool"},
                {"title":"EV Charger Installation","desc":"Level 2 EV charger installation at your home in {city}. Compatible with all major EV brands.","icon":"droplet"},
                {"title":"Pot Lights & Lighting","desc":"Pot light installation, lighting upgrades and smart home lighting in {city}.","icon":"flame"},
                {"title":"Electrical Repairs","desc":"Faulty outlets, tripping breakers, flickering lights — fast and safe electrical repairs in {city}.","icon":"search"},
                {"title":"Safety Inspections","desc":"Full electrical inspection with ESA-qualified report. Identify hazards before buying or selling your home in {city}.","icon":"alert"}
            ],
            "faq_items": [
                {"q":"How much does an electrical panel upgrade cost in {city}?","a":"A 200A panel upgrade in {city} typically costs ${service1_min}–${service1_max}, including labour, materials and permit. Prices vary based on panel location, service entrance and city permit fees.","open":True},
                {"q":"Do I need a permit for electrical work in {city}?","a":"Yes — almost all electrical work in {city} requires a permit from the Electrical Safety Authority (ESA) or local authority. Our licensed electricians handle permitting as part of every job.","open":False},
                {"q":"How much does an EV charger installation cost in {city}?","a":"A Level 2 EV charger installation in {city} costs ${service3_min}–${service3_max}, depending on panel capacity, wire run length and charger type. Some utilities offer rebates — ask your electrician.","open":False},
                {"q":"How do I know if I need a panel upgrade in {city}?","a":"Signs you may need a panel upgrade: frequently tripping breakers, flickering lights, a panel under 100A, or adding high-draw appliances like an EV charger or hot tub. Our electricians provide free assessments.","open":False},
                {"q":"How long does electrical panel upgrade take in {city}?","a":"A standard 200A panel upgrade in {city} typically takes one full day. The power is off for approximately 4–6 hours during the switchover. Your electrician will book the permit inspection in advance.","open":False}
            ]
        },
        "form_steps": [
            {"title":"Service Type","button_text":"Continue","fields":[{"type":"radio_cards","name":"project-type","label":"What electrical work do you need?","required":True,"error_id":"project-error","options":[{"value":"panel","emoji":"⚡","label":"Panel Upgrade"},{"value":"wiring","emoji":"🔌","label":"Wiring / Rewiring"},{"value":"ev-charger","emoji":"🚗","label":"EV Charger"},{"value":"repair","emoji":"🔧","label":"Repair / Issue"},{"value":"inspection","emoji":"🔍","label":"Inspection"}]}]},
            {"title":"Your Property","button_text":"Continue","fields":[{"type":"select","name":"property-type","label":"Property Type","required":True,"options":[{"value":"house","label":"Single-family House"},{"value":"condo","label":"Condo / Townhouse"},{"value":"multi","label":"Duplex / Triplex"},{"value":"commercial","label":"Commercial"},{"value":"other","label":"Other"}]},{"type":"select","name":"panel-size","label":"Current Panel Size (if known)","required":False,"options":[{"value":"unknown","label":"I don't know"},{"value":"60","label":"60A (old)"},{"value":"100","label":"100A"},{"value":"200","label":"200A"},{"value":"400","label":"400A+"}]}]},
            {"title":"Timeline","button_text":"Continue","fields":[{"type":"radio_cards","name":"timeline","label":"When do you need the work done?","required":True,"error_id":"timeline-error","options":[{"value":"urgent","emoji":"🚨","label":"Urgent — Safety Issue"},{"value":"this-week","emoji":"📅","label":"This Week"},{"value":"this-month","emoji":"🗓️","label":"This Month"},{"value":"planning","emoji":"💭","label":"Planning Ahead"}]}]}
        ],
        "authority_resources": [
            {"url":"https://en.wikipedia.org/wiki/{city}","ancre":"{city} — Wikipedia","hook":"Background on {city}: demographics, housing and electrical infrastructure."},
            {"url":"https://www.esasafe.com/","ancre":"ESA — Electrical Safety Authority","hook":"Electrical safety standards and permit requirements for work in {city}."}
        ],
        "images_alt_templates": [
            "Licensed electrician working in {city}, {province}",
            "Electrical panel upgrade in {city}",
            "EV charger installation in {city}",
            "Certified electrician on a job in {city}",
            "Electrical wiring in {city}, {province}"
        ]
    },

    "paving": {
        "site": {
            "name": "Paving Quotes Canada",
            "niche": "paving-en",
            "domain": "https://paving-quotes.ca",
            "phone": "",
            "service_label": "Paving & Asphalt",
            "schema_type": "HomeAndConstructionBusiness",
            "schema_description": "Paving contractors in {city}, {province}. Driveway paving, asphalt, interlocking, concrete. Licensed and insured.",
            "price_range": "$$$",
            "ga_id": "G-XXXXXXXXXX",
            "form_name": "paving-quote",
            "lead_system": "external_link"
        },
        "affiliate": {
            "base_url": "https://renoquotes.com/en/form/service/paving-asphalt?utm_campaign=jb",
            "aff_id": "",
            "redirect_path": "/get-paving-quote/",
            "badge": "100% Free — No Obligation",
            "button_text": "Get My Free Paving Quotes",
            "sublabel": "3 to 5 quotes · Local paving contractors · Response within 24h"
        },
        "colors": {
            "50": "#f8fafc","100": "#f1f5f9","200": "#e2e8f0","300": "#cbd5e1",
            "400": "#94a3b8","500": "#64748b","600": "#475569","700": "#334155",
            "800": "#1e293b","900": "#0f172a",
            "shadow": "rgba(71,85,105,0.35)","shadow_hover": "rgba(71,85,105,0.50)"
        },
        "css_prefix": "pv-",
        "output_dir": "../dist_paving_en",
        "prices": {
            "grande_ville": {"seuil":50000,"service1_min":5000,"service1_max":20000,"service2_min":3000,"service2_max":12000,"service3_min":2000,"service3_max":8000,"service4_min":500,"service4_max":2000},
            "moyenne_ville": {"seuil":15000,"service1_min":4500,"service1_max":18000,"service2_min":2500,"service2_max":10000,"service3_min":1800,"service3_max":7000,"service4_min":450,"service4_max":1800},
            "petite_ville": {"seuil":5000,"service1_min":4000,"service1_max":15000,"service2_min":2200,"service2_max":9000,"service3_min":1500,"service3_max":6000,"service4_min":400,"service4_max":1500},
            "village": {"seuil":0,"service1_min":3500,"service1_max":13000,"service2_min":2000,"service2_max":8000,"service3_min":1200,"service3_max":5000,"service4_min":350,"service4_max":1200}
        },
        "seo": {
            "title_templates": [
                "Paving {city} — {annee} Prices & Free Quotes | {site_name}",
                "Driveway Paving Contractors in {city} {annee} — Asphalt, Interlocking & Concrete",
                "{city} Paving {annee} — Licensed Contractors | {site_name}",
                "{city}: Driveway Paving {annee} — Up to 5 Free Quotes | {site_name}",
                "Paving Quotes {city} {annee} | Local Licensed Contractors | {site_name}"
            ],
            "desc_templates": [
                "Compare up to 5 free paving quotes in {city}. New driveway from ${service1_min}, repairs from ${service4_min}. Response within 24h.",
                "Paving in {city} — asphalt driveway, interlocking, concrete, repairs. Licensed contractors. Free quote.",
                "Paving prices {city} {annee}: new driveway from ${service1_min}. Compare 5 local paving contractor quotes.",
                "Looking for a paving contractor in {city}? Licensed and insured — free quote, 24h response.",
                "Find the best paving contractor in {city} in {annee}. Asphalt, interlocking, concrete — free quote."
            ]
        },
        "content": {
            "banner_text": "{nb} paving projects submitted this week in {city}",
            "index_heading_spintax": [
                "{site_name} — All of Canada {annee}",
                "{site_name} · {nb_total} cities covered {annee}",
                "Paving & Asphalt Across Canada — {nb_regions} provinces | {site_name}"
            ],
            "index_subheading_spintax": [
                "Licensed paving contractors — free quote, no obligation, 24h response.",
                "Compare up to 5 quotes from verified local paving contractors near you.",
                "Asphalt · Interlocking · Concrete · Repairs · Response guaranteed within 24h."
            ],
            "region_heading_spintax": [
                "Paving in {region} — {nb_villes} cities covered",
                "Paving Contractors in {region} — {nb_villes} cities",
                "Paving {region} | {nb_villes} {cities|communities|towns} served"
            ],
            "region_intro_spintax": [
                "Find a {licensed paving contractor|certified asphalt contractor} in your city in {region}.",
                "Compare prices and {get|receive} up to 5 free quotes in {region}.",
                "{nb_villes} cities in {region}. {Free|No-obligation} quote, 24h response."
            ],
            "section_headings": {
                "reassurance": "Why choose {site_name} for your paving project in {city}?",
                "prices": "Paving prices in {city} — {annee}",
                "services": "Paving services available in {city}",
                "faq": "Frequently asked questions — Paving in {city}",
                "cta_title": "Need a paving contractor in {city}?",
                "cta_subtitle": "Free quote · 24h response · Local licensed contractors",
                "cta_button": "Get My Free Paving Quotes",
                "cta_note": "Free · No obligation · Response within 24h",
                "footer_tagline": "{nb_villes_total} cities covered. Paving experts across Canada.",
                "footer_region_title": "Paving in {region}",
                "nav_badge": "Free Quote",
                "nav_cta": "Get a Price"
            },
            "form_header": {
                "badge": "100% Free Quote",
                "title": "Your paving project in {city}",
                "privacy_text": "Your information is confidential — shared only with pre-screened local paving contractors."
            },
            "intro_spintax": [
                "Looking for a {paving contractor|licensed asphalt contractor} in {city}? {Get|Receive} up to 5 {free quotes|personalized estimates} from {licensed contractors|local experts} within {24 hours|24h}. {New driveway|Asphalt repair|Interlocking|Concrete} — {quality workmanship|licensed and insured}.",
                "{Compare prices|Find the best rate} for {driveway paving|asphalt installation} in {city}. Our {paving partners|certified contractors} {deliver|install} long-lasting surfaces with {quality materials|commercial-grade asphalt} — {competitive pricing|best value}.",
                "The {best paving contractors|top-rated asphalt contractors} in {city} are on our platform. {New asphalt driveway|Interlocking stone|Concrete driveway|Crack sealing} — {get|receive} 5 {free|no-obligation} quotes within {24h|24 hours}.",
                "A {cracked driveway|damaged asphalt|deteriorating pavement} in {city} {loses value every season|gets worse over winter}. Our {paving partners|local specialists} {repair or replace|assess and fix} your driveway before it requires {full replacement|costly excavation}. {Free quote|No-cost estimate} within {24h|one business day}."
            ],
            "trust_points": [
                {"title": "Licensed & Insured Contractors", "desc": "Every paving partner is fully licensed, carries liability insurance, and has verified references in {city}.", "icon": "shield"},
                {"title": "100% Free Quote", "desc": "No fees, no obligation. Compare up to 5 paving quotes for your project in {city} — completely free.", "icon": "dollar"},
                {"title": "Local Expertise in {city}", "desc": "Paving contractors who know {city}'s soil conditions, freeze-thaw cycles and municipal regulations for driveway work.", "icon": "map"},
                {"title": "Durable Results", "desc": "Quality base preparation and materials ensure your new driveway in {city} lasts 15–25 years with proper maintenance.", "icon": "star"}
            ],
            "prices_display": {
                "subtitle": "Estimates based on surface area, material and access",
                "main_cards": [
                    {"key_min":"service1_min","key_max":"service1_max","label":"New Asphalt Driveway","sublabel":"Excavation · Gravel base · Hot-mix asphalt · Edging","emoji":"🚗","featured":True},
                    {"key_min":"service2_min","key_max":"service2_max","label":"Interlocking Stone","sublabel":"Base prep · Interlocking pavers · Sand joints · Edging","emoji":"🪨","featured":False},
                    {"key_min":"service3_min","key_max":"service3_max","label":"Concrete Driveway","sublabel":"Forms · Reinforcement · Pour · Finish · Cure","emoji":"🏗️","featured":False}
                ],
                "secondary_cards": [
                    {"key_min":"service4_min","key_max":"service4_max","label":"🔧 Asphalt crack sealing","suffix":""},
                    {"key_min":"service4_min","key_max":"service4_max","label":"🎨 Driveway seal coating","suffix":""},
                    {"key_min":"service3_min","key_max":"service3_max","label":"🛤️ Parking lot paving","suffix":""},
                    {"key_min":"service4_min","key_max":"service4_max","label":"🌿 Paving stone pathway","suffix":""}
                ]
            },
            "services": [
                {"title":"Asphalt Driveway Installation","desc":"New asphalt driveway installation in {city}. Excavation, gravel base, hot-mix asphalt, proper grading and drainage.","icon":"wrench"},
                {"title":"Interlocking Stone","desc":"Interlocking stone driveways, walkways and patios in {city}. Classic look, easy repairs, long-lasting.","icon":"tool"},
                {"title":"Concrete Driveway","desc":"Reinforced concrete driveways in {city}. Long-lasting, low maintenance, custom finishes available.","icon":"droplet"},
                {"title":"Asphalt Repair","desc":"Crack filling, patching, pothole repair — extend the life of your existing driveway in {city}.","icon":"flame"},
                {"title":"Seal Coating","desc":"Protect your asphalt driveway with professional seal coating. Extends life and improves appearance.","icon":"search"},
                {"title":"Parking Lots & Commercial","desc":"Commercial parking lot paving, line marking and maintenance in {city}. Licensed for large-scale projects.","icon":"alert"}
            ],
            "faq_items": [
                {"q":"How much does a new asphalt driveway cost in {city}?","a":"A new asphalt driveway in {city} typically costs ${service1_min}–${service1_max}, depending on size, excavation required and access. Get 3–5 free quotes to compare real prices.","open":True},
                {"q":"Asphalt vs. interlocking vs. concrete — which is best for {city}?","a":"In {city}'s climate, asphalt is the most popular choice — it handles freeze-thaw cycles well and is cost-effective. Interlocking offers a premium look. Concrete is very durable but requires expansion joints in cold climates. Your contractor can advise based on your budget and preferences.","open":False},
                {"q":"How long does a new driveway installation take in {city}?","a":"A standard residential driveway in {city} takes 1–2 days to complete. Asphalt needs 24–48h to cure before driving on it. Interlocking can take 2–4 days.","open":False},
                {"q":"When is the best time to pave a driveway in {city}?","a":"In {city}, the paving season runs from late spring to early fall (May–October). Asphalt should not be installed when temperatures are below 10°C. Spring and summer are the most popular booking times — plan ahead.","open":False},
                {"q":"How long does an asphalt driveway last in {city}?","a":"A well-installed asphalt driveway in {city} typically lasts 20–30 years with seal coating every 3–5 years and prompt crack repair. Poor base preparation is the main cause of premature failure.","open":False}
            ]
        },
        "form_steps": [
            {"title":"Project Type","button_text":"Continue","fields":[{"type":"radio_cards","name":"project-type","label":"What type of paving work do you need?","required":True,"error_id":"project-error","options":[{"value":"new-asphalt","emoji":"🚗","label":"New Asphalt Driveway"},{"value":"interlocking","emoji":"🪨","label":"Interlocking Stone"},{"value":"concrete","emoji":"🏗️","label":"Concrete Driveway"},{"value":"repair","emoji":"🔧","label":"Repair / Patching"},{"value":"sealcoat","emoji":"🎨","label":"Seal Coating"}]}]},
            {"title":"Your Project","button_text":"Continue","fields":[{"type":"select","name":"driveway-size","label":"Approximate Driveway Size","required":True,"options":[{"value":"small","label":"Small (under 300 sq ft)"},{"value":"medium","label":"Medium (300–600 sq ft)"},{"value":"large","label":"Large (600–1,000 sq ft)"},{"value":"xlarge","label":"Extra Large (1,000+ sq ft)"}]},{"type":"select","name":"property-type","label":"Property Type","required":True,"options":[{"value":"house","label":"Residential — House"},{"value":"commercial","label":"Commercial"},{"value":"parking-lot","label":"Parking Lot"},{"value":"other","label":"Other"}]}]},
            {"title":"Timeline","button_text":"Continue","fields":[{"type":"radio_cards","name":"timeline","label":"When do you want the work done?","required":True,"error_id":"timeline-error","options":[{"value":"this-spring","emoji":"🌸","label":"This Spring"},{"value":"this-summer","emoji":"☀️","label":"This Summer"},{"value":"fall","emoji":"🍂","label":"This Fall"},{"value":"planning","emoji":"💭","label":"Still Planning"}]}]}
        ],
        "authority_resources": [
            {"url":"https://en.wikipedia.org/wiki/{city}","ancre":"{city} — Wikipedia","hook":"Background on {city}: climate, soil and infrastructure — key factors for driveway planning."},
            {"url":"https://www.cca-acc.com/","ancre":"Canadian Construction Association","hook":"Industry standards for paving contractors in {city}."}
        ],
        "images_alt_templates": [
            "Paving contractor working in {city}, {province}",
            "New asphalt driveway in {city}",
            "Interlocking stone installation in {city}",
            "Driveway paving project in {city}",
            "Finished driveway in {city}, {province}"
        ]
    },

    "basement": {
        "site": {
            "name": "Basement Quotes Canada",
            "niche": "basement-en",
            "domain": "https://basement-quotes.ca",
            "phone": "",
            "service_label": "Basement Renovation",
            "schema_type": "HomeAndConstructionBusiness",
            "schema_description": "Basement renovation contractors in {city}, {province}. Finishing, waterproofing, underpinning, legal suites. Licensed and insured.",
            "price_range": "$$$",
            "ga_id": "G-XXXXXXXXXX",
            "form_name": "basement-quote",
            "lead_system": "external_link"
        },
        "affiliate": {
            "base_url": "https://renoquotes.com/en/form/service/basement-renovation?utm_campaign=jb",
            "aff_id": "",
            "redirect_path": "/get-basement-quote/",
            "badge": "100% Free — No Obligation",
            "button_text": "Get My Free Basement Quotes",
            "sublabel": "3 to 5 quotes · Local renovation experts · Response within 24h"
        },
        "colors": {
            "50": "#f0f9ff","100": "#e0f2fe","200": "#bae6fd","300": "#7dd3fc",
            "400": "#38bdf8","500": "#0ea5e9","600": "#0284c7","700": "#0369a1",
            "800": "#075985","900": "#0c4a6e",
            "shadow": "rgba(2,132,199,0.35)","shadow_hover": "rgba(2,132,199,0.50)"
        },
        "css_prefix": "bs-",
        "output_dir": "../dist_basement_en",
        "prices": {
            "grande_ville": {"seuil":50000,"service1_min":30000,"service1_max":100000,"service2_min":15000,"service2_max":50000,"service3_min":5000,"service3_max":20000,"service4_min":2000,"service4_max":8000},
            "moyenne_ville": {"seuil":15000,"service1_min":25000,"service1_max":80000,"service2_min":12000,"service2_max":40000,"service3_min":4000,"service3_max":16000,"service4_min":1800,"service4_max":7000},
            "petite_ville": {"seuil":5000,"service1_min":22000,"service1_max":70000,"service2_min":10000,"service2_max":35000,"service3_min":3500,"service3_max":14000,"service4_min":1500,"service4_max":6000},
            "village": {"seuil":0,"service1_min":20000,"service1_max":60000,"service2_min":9000,"service2_max":30000,"service3_min":3000,"service3_max":12000,"service4_min":1200,"service4_max":5000}
        },
        "seo": {
            "title_templates": [
                "Basement Renovation {city} — {annee} Prices & Free Quotes | {site_name}",
                "Basement Finishing Contractors in {city} {annee} — Waterproofing, Legal Suites & More",
                "{city} Basement Renovation {annee} — Licensed Contractors | {site_name}",
                "{city}: Basement Finishing {annee} — Up to 5 Free Quotes | {site_name}",
                "Basement Renovation Quotes {city} {annee} | Local Experts | {site_name}"
            ],
            "desc_templates": [
                "Compare up to 5 free basement renovation quotes in {city}. Full finish from ${service1_min}, waterproofing from ${service3_min}. Response within 24h.",
                "Basement renovation in {city} — finishing, waterproofing, underpinning, legal suites. Licensed contractors. Free quote.",
                "Basement renovation prices {city} {annee}: full finish from ${service1_min}. Compare 5 local contractor quotes.",
                "Looking for a basement contractor in {city}? Licensed renovation experts — free quote, 24h response.",
                "Find the best basement contractor in {city} in {annee}. Finishing, waterproofing, suite — free quote."
            ]
        },
        "content": {
            "banner_text": "{nb} basement renovation projects submitted this week in {city}",
            "index_heading_spintax": [
                "{site_name} — All of Canada {annee}",
                "{site_name} · {nb_total} cities covered {annee}",
                "Basement Renovation Across Canada — {nb_regions} provinces | {site_name}"
            ],
            "index_subheading_spintax": [
                "Licensed basement contractors — free quote, no obligation, 24h response.",
                "Compare up to 5 quotes from verified basement renovation experts near you.",
                "Finishing · Waterproofing · Legal Suites · Underpinning · Response guaranteed within 24h."
            ],
            "region_heading_spintax": [
                "Basement Renovation in {region} — {nb_villes} cities covered",
                "Basement Contractors in {region} — {nb_villes} cities",
                "Basement Renovation {region} | {nb_villes} {cities|communities|towns} served"
            ],
            "region_intro_spintax": [
                "Find a {licensed basement contractor|certified renovation expert} in your city in {region}.",
                "Compare prices and {get|receive} up to 5 free quotes in {region}.",
                "{nb_villes} cities in {region}. {Free|No-obligation} quote, 24h response."
            ],
            "section_headings": {
                "reassurance": "Why choose {site_name} for your basement renovation in {city}?",
                "prices": "Basement renovation prices in {city} — {annee}",
                "services": "Basement renovation services available in {city}",
                "faq": "Frequently asked questions — Basement renovation in {city}",
                "cta_title": "Ready to renovate your basement in {city}?",
                "cta_subtitle": "Free quote · 24h response · Local licensed contractors",
                "cta_button": "Get My Free Basement Quotes",
                "cta_note": "Free · No obligation · Response within 24h",
                "footer_tagline": "{nb_villes_total} cities covered. Basement renovation experts across Canada.",
                "footer_region_title": "Basement Renovation in {region}",
                "nav_badge": "Free Quote",
                "nav_cta": "Get a Price"
            },
            "form_header": {
                "badge": "100% Free Quote",
                "title": "Your basement renovation in {city}",
                "privacy_text": "Your information is confidential — shared only with pre-screened local contractors."
            },
            "intro_spintax": [
                "Looking for a {basement renovation contractor|licensed basement finisher} in {city}? {Get|Receive} up to 5 {free quotes|personalized estimates} from {licensed contractors|local experts} within {24 hours|24h}. {Full finishing|Waterproofing|Legal suite|Underpinning} — {quality craftsmanship|licensed and insured}.",
                "{Compare prices|Find the best rate} for {basement finishing|basement renovation} in {city}. Our {renovation partners|certified contractors} {transform|convert} unfinished basements into {livable space|income-generating suites} — {competitive pricing|best value}.",
                "The {best basement contractors|top-rated renovation experts} in {city} are on our platform. {Full finish|Legal suite|Waterproofing|Underpinning} — {get|receive} 5 {free|no-obligation} quotes within {24h|24 hours}.",
                "An {unfinished basement|damp basement|unused basement} in {city} is {lost living space|lost monthly income}. Our {renovation partners|local specialists} {design and build|plan and execute} basements that {add value|generate rental income}. {Free quote|No-cost estimate} within {24h|one business day}.",
                "Did you know that a {finished basement|basement legal suite} can {add 10–20% to your home's value|generate $1,500+/month in rental income} in {city}? Our {licensed contractors|certified experts} {plan and build|design and deliver} code-compliant basement spaces {on time and on budget|with quality guarantees}."
            ],
            "trust_points": [
                {"title": "Licensed & Insured Contractors", "desc": "Every renovation partner is fully licensed, carries liability insurance, and has verified references in {city}.", "icon": "shield"},
                {"title": "100% Free Quote", "desc": "No fees, no obligation. Compare up to 5 basement renovation quotes in {city} — completely free.", "icon": "dollar"},
                {"title": "Waterproofing Expertise", "desc": "Proper waterproofing is critical before finishing a basement. Our contractors in {city} assess and correct moisture issues first.", "icon": "map"},
                {"title": "Code-Compliant Builds", "desc": "All basement renovations — including legal suites — are built to code with proper permits in {city}.", "icon": "star"}
            ],
            "prices_display": {
                "subtitle": "Estimates based on size, scope and finish level",
                "main_cards": [
                    {"key_min":"service1_min","key_max":"service1_max","label":"Full Basement Finish","sublabel":"Framing · Drywall · Flooring · Lighting · Bathroom","emoji":"🏠","featured":True},
                    {"key_min":"service2_min","key_max":"service2_max","label":"Legal Basement Suite","sublabel":"Permits · Egress · Kitchen · Bath · Full finish","emoji":"🏡","featured":False},
                    {"key_min":"service3_min","key_max":"service3_max","label":"Waterproofing","sublabel":"Interior/exterior membrane · Sump pump · Drainage","emoji":"💧","featured":False}
                ],
                "secondary_cards": [
                    {"key_min":"service4_min","key_max":"service4_max","label":"🛁 Basement bathroom addition","suffix":""},
                    {"key_min":"service3_min","key_max":"service3_max","label":"☔ Interior waterproofing system","suffix":""},
                    {"key_min":"service4_min","key_max":"service4_max","label":"🌡️ Basement heating installation","suffix":""},
                    {"key_min":"service4_min","key_max":"service4_max","label":"🪟 Egress window installation","suffix":""}
                ]
            },
            "services": [
                {"title":"Basement Finishing","desc":"Full basement finishing in {city} — framing, insulation, drywall, flooring, lighting and trim. Turn unused space into living space.","icon":"wrench"},
                {"title":"Legal Basement Suite","desc":"Complete legal basement suite construction in {city}. Permits, egress, kitchen, bathroom, separate entrance — income-ready.","icon":"tool"},
                {"title":"Basement Waterproofing","desc":"Interior and exterior waterproofing systems. Sump pumps, drainage membranes, crack injection in {city}.","icon":"droplet"},
                {"title":"Underpinning","desc":"Basement underpinning to increase ceiling height in {city}. Structural engineering and permit included.","icon":"flame"},
                {"title":"Basement Bathroom","desc":"New bathroom addition in your basement. Full plumbing rough-in, tile, fixtures and ventilation.","icon":"search"},
                {"title":"Home Theatre & Media Room","desc":"Custom home theatre and media room design and installation. Wiring, acoustics and custom millwork in {city}.","icon":"alert"}
            ],
            "faq_items": [
                {"q":"How much does it cost to finish a basement in {city}?","a":"A full basement finish in {city} typically costs ${service1_min}–${service1_max}, depending on size, bathroom inclusion and finish level. A basic finish with no bathroom starts around ${service3_min}–${service2_min}. Get 3–5 free quotes to compare.","open":True},
                {"q":"How much does a legal basement suite cost in {city}?","a":"A legal basement suite in {city} typically costs ${service2_min}–${service2_max}, including permits, egress windows, kitchen, bathroom and separate entrance. Rental income of $1,500–$2,500+/month is common in larger {city} markets.","open":False},
                {"q":"Do I need a permit to finish my basement in {city}?","a":"Yes — basement finishing that includes electrical, plumbing or structural work requires permits in {city}. Legal suites require additional permits and inspections. Your contractor handles the permitting process.","open":False},
                {"q":"How do I know if my basement has a moisture problem?","a":"Signs of basement moisture in {city}: water stains, efflorescence (white powder on walls), musty odour, peeling paint, or visible mold. Our contractors assess moisture before any finishing work to prevent future damage.","open":False},
                {"q":"How long does a basement renovation take in {city}?","a":"A full basement finish in {city} takes 4–8 weeks. A legal suite with plumbing and permitting takes 8–14 weeks. Underpinning adds 2–4 weeks. Your contractor will provide a detailed schedule.","open":False}
            ]
        },
        "form_steps": [
            {"title":"Project Type","button_text":"Continue","fields":[{"type":"radio_cards","name":"project-type","label":"What basement work do you need?","required":True,"error_id":"project-error","options":[{"value":"full-finish","emoji":"🏠","label":"Full Basement Finish"},{"value":"legal-suite","emoji":"🏡","label":"Legal Basement Suite"},{"value":"waterproofing","emoji":"💧","label":"Waterproofing"},{"value":"bathroom","emoji":"🛁","label":"Basement Bathroom"},{"value":"underpinning","emoji":"🔩","label":"Underpinning"}]}]},
            {"title":"Your Basement","button_text":"Continue","fields":[{"type":"select","name":"basement-size","label":"Approximate Basement Size","required":True,"options":[{"value":"small","label":"Small (under 500 sq ft)"},{"value":"medium","label":"Medium (500–800 sq ft)"},{"value":"large","label":"Large (800–1,200 sq ft)"},{"value":"xlarge","label":"Extra Large (1,200+ sq ft)"}]},{"type":"select","name":"basement-condition","label":"Current Basement Condition","required":True,"options":[{"value":"unfinished","label":"Fully Unfinished"},{"value":"partial","label":"Partially Finished"},{"value":"finished","label":"Finished (Renovating)"},{"value":"wet","label":"Has Moisture Issues"}]}]},
            {"title":"Timeline","button_text":"Continue","fields":[{"type":"radio_cards","name":"timeline","label":"When do you want to start?","required":True,"error_id":"timeline-error","options":[{"value":"asap","emoji":"🚀","label":"As Soon as Possible"},{"value":"1-3months","emoji":"📅","label":"Within 1–3 Months"},{"value":"3-6months","emoji":"🗓️","label":"3–6 Months"},{"value":"planning","emoji":"💭","label":"Still Planning"}]}]}
        ],
        "authority_resources": [
            {"url":"https://en.wikipedia.org/wiki/{city}","ancre":"{city} — Wikipedia","hook":"Background on {city}: demographics, housing and rental market — key context for basement suite investments."},
            {"url":"https://www.cmhc-schl.gc.ca/","ancre":"CMHC — Canada Mortgage and Housing Corporation","hook":"Housing guidelines and secondary suite resources for homeowners in {city}."}
        ],
        "images_alt_templates": [
            "Basement renovation in {city}, {province}",
            "Finished basement in {city} — open concept design",
            "Legal basement suite in {city}",
            "Basement renovation completed in {city}",
            "New basement finishing in {city}, {province}"
        ]
    }
}


def build_config(niche_key, data):
    design = dict(COMMON["design_base"])
    design["css_prefix"] = data["css_prefix"]
    design["colors"] = data["colors"]

    form_steps = data["form_steps"] + [COMMON["form_common"]["contact_step"]]

    images = {
        "use_local": False,
        "alt_templates": data["images_alt_templates"],
        "local_pool": LOCAL_POOL_50,
        "pexels_pool": []
    }

    content = dict(data["content"])
    content["faq_items"] = data["content"]["faq_items"]

    form = {
        "netlify_name": data["site"]["form_name"],
        "submit_text": data["affiliate"]["button_text"],
        "confirmation_title": "Request Received!",
        "confirmation_body": f"Our {data['site']['service_label'].lower()} contractors in <strong>{{{{city}}}}</strong> will contact you within the next <strong>24 hours</strong>.",
        "confirmation_stats": COMMON["form_common"]["confirmation_stats"],
        "steps": form_steps
    }

    cfg = {
        "_comment": f"config_{niche_key}_en.json — Niche: {data['site']['service_label']} English Canada (ON/AB/BC)",
        "site": data["site"],
        "affiliate": data["affiliate"],
        "design": design,
        "deploy": COMMON["deploy"],
        "csv": COMMON["csv"],
        "output_dir": data["output_dir"],
        "performance": COMMON["performance"],
        "social_proof": COMMON["social_proof"],
        "premium_cities": COMMON["premium_cities"],
        "authority_resources": data["authority_resources"],
        "images": images,
        "prices": data["prices"],
        "seo": data["seo"],
        "form": form,
        "content": content,
        "network": {
            "sister_sites": []
        }
    }
    return cfg


for niche_key, niche_data in NICHES.items():
    cfg = build_config(niche_key, niche_data)
    out_path = os.path.join(BASE, f"config_{niche_key}_en.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    print(f"Created: {out_path}")

print("\nAll 6 EN configs created successfully.")
