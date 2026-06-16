"""
Generate niche-specific hero images using Google Imagen 3 API.
Saves as JPEG in dist_{niche}/img/hero-N.jpg and updates config use_local=true.
"""
import json, os, base64, urllib.request, urllib.error, time, sys

GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
IMAGEN_URL  = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-fast-generate-001:predict?key={GEMINI_KEY}"
FLASH_URL   = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent?key={GEMINI_KEY}"

BASE       = r"C:/Users/bellj/OneDrive/Desktop/Programmatic seo/Empire-PSEO"
BASE_EN    = r"C:/Users/bellj/OneDrive/Desktop/Programmatic seo/Empire-PSEO/engine_en"
BASE_US    = r"C:/Users/bellj/OneDrive/Desktop/Programmatic seo/Empire-PSEO/site_USA"
ENGINE_USA = r"C:/Users/bellj/OneDrive/Desktop/Programmatic seo/Empire-PSEO/engine_usa"
SITES      = r"C:/Users/bellj/OneDrive/Desktop/Programmatic seo/Sites_relateds"

COUNT = 100  # images per niche

NICHES = {
    "calfeutrage": {
        "config": f"{BASE}/config_calfeutrage.json",
        "dist":   f"{BASE}/dist_calfeutrage",
        "prompts": [
            "Professional contractor applying white silicone caulk around a window frame on a house exterior, daytime, photorealistic",
            "Worker sealing a door frame with weatherstripping on a suburban home exterior, daylight, realistic photo",
            "Close-up of a tradesperson applying caulk gun sealant around a window, exterior insulation work, professional",
            "Home renovation worker installing foam weatherstripping on a front door, bright daylight",
            "Professional applying exterior caulking around window trim on a brick house, blue sky background",
        ],
    },
    "decontamination": {
        "config": f"{BASE}/config_decontamination.json",
        "dist":   f"{BASE}/dist_decontamination",
        "prompts": [
            "Worker in full white hazmat suit and respirator mask performing mold remediation in a basement, professional photo",
            "Decontamination team in protective suits removing asbestos from a building interior, realistic documentary photo",
            "Industrial hygienist in PPE collecting environmental samples inside a contaminated building, daylight",
            "Two workers in white Tyvek suits and respirators cleaning up a contaminated site, professional",
            "Biohazard cleanup crew in protective suits sealing contaminated materials in yellow bags, realistic photo",
        ],
    },
    "emondage": {
        "config": f"{BASE}/config_emondage.json",
        "dist":   f"{BASE}/dist_emondage",
        "prompts": [
            "Certified arborist high up in a large tree using a chainsaw to trim branches, daylight, professional photo",
            "Tree trimming crew working with a wood chipper on a residential street, daytime",
            "Professional arborist climbing a tall oak tree with ropes and harness, pruning equipment, sunny day",
            "Tree removal service worker cutting a large branch with a chainsaw from a bucket truck lift",
            "Ground crew loading tree branches into a wood chipper truck after trimming, suburban neighborhood",
        ],
    },
    "excavation": {
        "config": f"{BASE}/config_excavation.json",
        "dist":   f"{BASE}/dist_excavation",
        "prompts": [
            "Large yellow excavator digging a deep trench on a residential construction site, daytime",
            "Backhoe loader excavating earth on a construction site, heavy equipment operation, realistic photo",
            "Construction workers operating a yellow CAT excavator on a building site, daylight",
            "Excavation site with a large trackhoe digging foundation trenches, sunny day, professional photo",
            "Mini excavator working in a backyard for underground pipe installation, residential property",
        ],
    },
    "fosseseptique": {
        "config": f"{BASE}/config_fosseseptique.json",
        "dist":   f"{BASE}/dist_fosseseptique",
        "prompts": [
            "Workers installing a concrete septic tank in the ground with an excavator visible, residential yard, professional photo",
            "Septic system installation showing underground distribution pipes being laid in a trench, daytime",
            "Plumber connecting PVC pipes for a septic tank drain field, excavated trench, daylight",
            "Vacuum truck pumping out a residential septic tank in a yard, professional service",
            "Two workers installing a buried septic tank with heavy equipment in a rural property yard",
        ],
    },
    "maconnerie": {
        "config": f"{BASE}/config_maconnerie.json",
        "dist":   f"{BASE}/dist_maconnerie",
        "prompts": [
            "Skilled bricklayer laying bricks with mortar on a house wall, trowel in hand, daylight professional photo",
            "Mason worker constructing a stone wall, carefully placing stones with mortar, outdoor residential",
            "Close-up of a professional bricklayer spreading mortar and laying red bricks, construction site",
            "Two masonry workers building a brick chimney on a residential home, sunny day",
            "Professional mason repointing an old brick wall with fresh mortar, restoration work",
        ],
    },
    "paysagement": {
        "config": f"{BASE}/config_paysagement.json",
        "dist":   f"{BASE}/dist_paysagement",
        "prompts": [
            "Landscaper operating a commercial riding lawn mower on a large green residential lawn, sunny day",
            "Professional landscaping crew planting shrubs and flowers in a well-maintained backyard garden",
            "Worker using a commercial walk-behind lawn mower on a suburban front yard, bright daylight",
            "Landscaping team laying sod rolls in a freshly graded backyard, professional photo",
            "Gardener trimming hedges with professional shears in a beautiful residential garden, daytime",
        ],
    },
    "peinture": {
        "config": f"{BASE}/config_peinture.json",
        "dist":   f"{BASE}/dist_peinture",
        "prompts": [
            "Professional house painter on a ladder painting the exterior siding of a home with a brush, sunny day",
            "Interior painter rolling white paint on a living room wall with a roller and extension pole, daylight",
            "Painting contractor spraying exterior paint on a two-storey house, professional equipment",
            "Two painters in white overalls painting a room interior, rollers and paint trays, professional photo",
            "Professional painter cutting in paint along crown molding in a bright modern home interior",
        ],
    },
    "piscine": {
        "config": f"{BASE}/config_piscine.json",
        "dist":   f"{BASE}/dist_piscine",
        "prompts": [
            "Beautiful in-ground swimming pool under construction in a suburban backyard, workers installing pool shell",
            "Finished residential inground pool with crystal blue water in a green backyard, sunny summer day",
            "Pool construction workers installing pool liner in a new inground pool, professional photo",
            "Luxury inground swimming pool surrounded by a patio deck in a backyard, bright daylight",
            "Swimming pool contractor installing pool equipment and filtration system, residential yard",
        ],
    },
    "roofing": {
        "config": f"{BASE_EN}/config_roofing_en.json",
        "dist":   f"{BASE}/dist_roofing_en",
        "prompts": [
            "Roofer nailing asphalt shingles on a residential rooftop, sunny day, professional photo",
            "Roofing crew installing new shingles on a house roof replacement project, daylight",
            "Close-up of a roofer's hands nailing down a row of asphalt shingles, professional roofing",
            "Two roofing contractors replacing old shingles on a suburban home, sunny day",
            "Roofer on a steep roof laying tar paper underlayment before shingle installation, professional",
        ],
    },
    "hvac": {
        "config": f"{BASE_EN}/config_hvac_en.json",
        "dist":   f"{BASE}/dist_hvac_en",
        "prompts": [
            "HVAC technician installing an outdoor air conditioning condenser unit beside a house, professional",
            "Two HVAC workers installing ductwork in an attic space, professional photo, daylight",
            "Technician servicing a residential furnace in a basement, professional HVAC work, realistic photo",
            "HVAC contractor connecting refrigerant lines on a central air conditioning outdoor unit",
            "Professional HVAC installer setting a new heat pump unit on a concrete pad beside a house",
        ],
    },
    "waterproofing": {
        "config": f"{BASE_EN}/config_waterproofing_en.json",
        "dist":   f"{BASE}/dist_waterproofing_en",
        "prompts": [
            "Workers applying waterproofing membrane to a concrete foundation wall in an excavated trench",
            "Basement waterproofing contractor installing interior drainage system along concrete block walls",
            "Professional applying liquid waterproofing coating to an exterior foundation wall, excavated site",
            "Workers installing a sump pump and drainage system in a wet basement, professional photo",
            "Foundation repair specialist injecting epoxy into a crack in a concrete basement wall",
        ],
    },
    "waterdamage": {
        "config": f"{BASE_US}/config_waterdamage_us.json",
        "dist":   f"{BASE}/dist_waterdamage_us",
        "prompts": [
            "Water damage restoration crew using industrial fans and dehumidifiers in a flooded home interior",
            "Restoration workers extracting water from a flooded basement with professional equipment",
            "Technician in protective gear removing wet drywall after water damage in a home",
            "Water damage restoration team setting up drying equipment in a damaged living room, professional",
            "Workers pulling up water-damaged flooring and operating extraction equipment in a home",
        ],
    },
    "plomberie": {
        "config": f"{BASE}/engine_qc/config_plomberie.json",
        "dist":   f"{BASE}/dist_plomberie",
        "prompts": [
            "Modern bathroom interior with chrome faucet, white ceramic sink and clean tiles, no people, photorealistic",
            "Residential utility room with new copper pipes and water heater, wide shot, no people, professional photo",
            "Newly renovated bathroom with walk-in shower, floor tiles and modern fixtures, bright natural light, no people",
            "Under-sink plumbing with new PVC pipes neatly installed, wide angle shot, no hands visible, realistic",
            "Clean modern kitchen with new faucet and stainless steel sink, interior design photo, no people",
        ],
    },
    "cuisine": {
        "config": f"{BASE}/engine_qc/config_cuisine.json",
        "dist":   f"{BASE}/dist_cuisine",
        "prompts": [
            "Beautiful modern white kitchen with quartz countertops and shaker cabinets, no people, bright natural light, photorealistic",
            "Open-concept kitchen renovation with dark island, pendant lights and subway tile backsplash, no people, interior photo",
            "Sleek grey kitchen with built-in appliances, large window and hardwood floor, interior design photography, no people",
            "Bright kitchen renovation in progress showing new cabinets installed, wide shot from doorway, no people",
            "Luxury kitchen with white marble countertop, gold hardware and large format floor tile, no people, photorealistic",
        ],
    },
    "salledebain": {
        "config": f"{BASE}/engine_qc/config_salledebain.json",
        "dist":   f"{BASE}/dist_salledebain",
        "prompts": [
            "Freshly renovated modern bathroom with large format tile, floating vanity and frameless shower, no people, bright",
            "Beautiful white bathroom with freestanding tub, marble tiles and natural light, no people, photorealistic",
            "Modern bathroom with double vanity, backlit mirror and herringbone floor tile, no people, interior photo",
            "Walk-in shower with large grey tiles, rain showerhead and glass enclosure, no people, bright lighting",
            "Bathroom renovation with new floor tiles being laid, wide shot, no people visible, professional photo",
        ],
    },
    "electricien": {
        "config": f"{BASE}/engine_qc/config_electricien.json",
        "dist":   f"{BASE}/dist_electricien",
        "prompts": [
            "New residential electrical panel with circuit breakers installed on a wall, no people, wide shot, photorealistic",
            "Electrician seen from behind working on a wall-mounted electrical box, full body shot, no face visible",
            "Neat electrical conduit and wiring runs along a basement ceiling, wide angle, no people, professional photo",
            "Modern home electrical room with new 200-amp service panel and tidy wiring, no people, bright",
            "Outdoor electrical meter and service entrance on a residential home exterior, no people, daylight",
        ],
    },
    "plancher": {
        "config": f"{BASE}/engine_qc/config_plancher.json",
        "dist":   f"{BASE}/dist_plancher",
        "prompts": [
            "Beautiful newly installed light oak hardwood floor in a bright modern living room, no people, photorealistic",
            "Wide angle view of luxury vinyl plank flooring installation in progress, no people visible, professional photo",
            "Gleaming refinished hardwood floor in a spacious open-concept home interior, no people, natural light",
            "Close-up of wide-plank engineered hardwood floor with wood grain texture, no hands, product photography",
            "Modern kitchen with large format porcelain tile floor, no people, interior design photo, bright",
        ],
    },
    "soussol": {
        "config": f"{BASE}/engine_qc/config_soussol.json",
        "dist":   f"{BASE}/dist_soussol",
        "prompts": [
            "Beautifully finished basement with pot lights, vinyl plank floor and modern drywall, no people, bright",
            "Finished basement home theatre room with large TV, sectional sofa and recessed lighting, no people",
            "Modern basement apartment suite with open living area, kitchenette and full bathroom, no people, photorealistic",
            "Basement renovation in progress with framed walls and electrical rough-in, wide shot, no people",
            "Bright finished basement office with built-in shelves, desk area and carpet tile, no people, photorealistic",
        ],
    },
    # ── NEW V3 NICHES (launched April 2026) ──────────────────────────────────
    "cloture": {
        "config": f"{BASE}/engine_qc/config_cloture.json",
        "dist":   f"{BASE}/dist_cloture",
        "prompts": [
            "Professional fence installer driving cedar fence posts with a post driver in a residential backyard, sunny day",
            "Two workers installing a white vinyl privacy fence in a suburban yard, professional photo, daylight",
            "Finished wood privacy fence with lattice top around a backyard, green lawn, sunny Quebec neighborhood",
            "Contractor installing black aluminum ornamental fence on a residential property, daytime, realistic photo",
            "Cedar wood fence panels being installed by a two-man crew in a backyard, professional workmanship",
        ],
    },
    "chauffage": {
        "config": f"{BASE}/engine_qc/config_chauffage.json",
        "dist":   f"{BASE}/dist_chauffage",
        "prompts": [
            "HVAC technician installing a wall-mounted heat pump unit in a residential living room, professional photo",
            "Heating contractor working on a new natural gas furnace installation in a Quebec home basement, professional",
            "Technician servicing a residential boiler system, tools and components visible, professional photo, daylight",
            "New energy-efficient heat pump unit on a concrete pad beside a house exterior, sunny day, no people",
            "Plumber-heating specialist connecting pipes to a new baseboard heating system, professional work, daylight",
        ],
    },
    "beton": {
        "config": f"{BASE}/engine_qc/config_beton.json",
        "dist":   f"{BASE}/dist_beton",
        "prompts": [
            "Concrete workers finishing a new driveway surface with a float tool, residential property, sunny day, professional",
            "Worker using a concrete screed board to level a freshly poured garage floor slab, daylight",
            "New stamped concrete patio being installed in a backyard, workers smoothing the surface, professional photo",
            "Concrete contractor pouring foundation walls for a residential home addition, construction site, daylight",
            "Freshly poured and finished concrete driveway in front of a modern suburban home, no people, sunny",
        ],
    },
    "portes-fenetres": {
        "config": f"{BASE}/engine_qc/config_portes-fenetres.json",
        "dist":   f"{BASE}/dist_portes-fenetres",
        "prompts": [
            "Worker installing a large triple-pane vinyl window in a house exterior wall, sunny day, professional photo",
            "Two installers fitting a new exterior patio door into a residential doorframe, daylight, professional",
            "Window replacement professional measuring and fitting a new energy-efficient window in a Quebec home",
            "Technician installing a new fiberglass entry door on a residential home, wide shot, sunny day",
            "Close-up of a new triple-glazed window being sealed into a brick wall, professional installation",
        ],
    },
    "agrandissement": {
        "config": f"{BASE}/engine_qc/config_agrandissement.json",
        "dist":   f"{BASE}/dist_agrandissement",
        "prompts": [
            "Home addition under construction showing new wood-framed exterior walls and roof structure, daylight",
            "Residential home extension with new second-storey addition framed in wood, construction site, sunny day",
            "Contractor working on a rear home addition showing new siding and window rough openings, professional photo",
            "Finished modern home addition with large windows and new exterior cladding attached to an existing house",
            "Construction crew building a new room addition to a suburban home, framing stage, daylight",
        ],
    },
    "ceramique": {
        "config": f"{BASE}/engine_qc/config_ceramique.json",
        "dist":   f"{BASE}/dist_ceramique",
        "prompts": [
            "Tiler installing large format grey ceramic floor tiles with notched trowel and tile spacers, no people's faces, professional",
            "Beautiful finished bathroom with large format porcelain wall and floor tiles, no people, bright natural light",
            "Tile setter cutting ceramic tile with a wet saw on a job site, wide shot from behind, professional",
            "Modern kitchen with white subway tile backsplash installation in progress, no people visible, daylight",
            "Finished living room with large format porcelain floor tiles in a herringbone pattern, no people, interior photo",
        ],
    },
    "couvreur": {
        "config": f"{BASE}/engine_qc/config_couvreur.json",
        "dist":   f"{BASE}/dist_couvreur",
        "prompts": [
            "Roofer nailing asphalt shingles on a steep residential rooftop in Quebec, sunny day, professional photo",
            "Two roofing contractors replacing old shingles on a suburban Quebec home, bright daylight, professional",
            "Close-up of a roofer's hands laying architectural shingles with a nail gun, professional roofing work",
            "Roofing crew on a two-storey home installing new grey asphalt shingles, sunny Quebec neighborhood",
            "Professional roofer on a residential roof with safety harness, hammer and shingles, sunny day, realistic",
        ],
    },
    "bardeau": {
        "config": f"{BASE}/engine_qc/config_bardeau.json",
        "dist":   f"{BASE}/dist_bardeau",
        "prompts": [
            "Worker removing worn asphalt shingles from a residential roof, replacement project, sunny day, professional",
            "Roofer installing new 30-year architectural asphalt shingles on a Quebec home, professional photo",
            "Close-up of new dark grey asphalt shingles being nailed on a residential roof, professional roofing",
            "Roofing contractor showing worn curled asphalt shingles that need replacement, residential roof, daylight",
            "Before and after roofing: old granule-stripped shingles next to new ones on a Quebec home, realistic photo",
        ],
    },
    "toiture-residentielle": {
        "config": f"{BASE}/engine_qc/config_toiture-residentielle.json",
        "dist":   f"{BASE}/dist_toiture-residentielle",
        "prompts": [
            "Professional residential roofer inspecting a house roof in Quebec, safety harness, sunny day, realistic photo",
            "Roofing crew completing a full residential roof replacement on a Quebec family home, bright daylight",
            "Wide shot of a newly finished residential roof with dark shingles on a suburban Quebec home, no people",
            "Two roofers installing underlayment and flashing on a residential roof, professional photo, daylight",
            "Professional roofer working on a hip roof residential home in Quebec, sunny day, photorealistic",
        ],
    },
    "toiture-plate": {
        "config": f"{BASE}/engine_qc/config_toiture-plate.json",
        "dist":   f"{BASE}/dist_toiture-plate",
        "prompts": [
            "Roofing worker applying torch-applied modified bitumen membrane on a flat commercial roof, sunny day, professional",
            "Two roofers installing TPO single-ply membrane on a flat residential roof, white membrane, daylight",
            "Professional roofer applying cold-applied liquid waterproofing coating on a flat roof surface, wide shot",
            "Flat roof replacement crew removing old gravel-ballasted roofing, laying new insulation boards, daylight",
            "Workers sealing flat roof perimeter flashing with torch and modified bitumen, commercial building",
        ],
    },
    "nettoyage-conduits": {
        "config": f"{BASE}/engine_qc/config_nettoyage-conduits.json",
        "dist":   f"{BASE}/dist_nettoyage-conduits",
        "prompts": [
            "Air duct cleaning technician using a large negative air machine connected to a residential HVAC duct, professional photo",
            "Worker using a rotating brush tool inside a residential furnace duct during air duct cleaning service",
            "Duct cleaning professional inspecting an air vent with a flashlight, residential home interior",
            "Air duct cleaning crew truck parked outside a residential home, technicians unloading equipment",
            "Close-up of a flexible vacuum hose inserted into a residential cold air return duct for cleaning",
        ],
    },
    # ── QC PAVAGE NICHES ──────────────────────────────────────────────────────
    "pavage-asphalte": {
        "config": f"{BASE}/engine_qc/config_pavage-asphalte.json",
        "dist":   f"{BASE}/dist_pavage-asphalte",
        "prompts": [
            "Asphalt paving crew operating a commercial paver machine laying a new residential driveway in Quebec, sunny day, professional photo",
            "Freshly paved black asphalt driveway in front of a suburban Quebec home, no people, bright daylight, photorealistic",
            "Worker using a vibratory roller compacting hot mix asphalt on a residential driveway, Quebec suburb, daylight",
            "Two asphalt workers shoveling and raking hot mix asphalt around a residential driveway edge, sunny Quebec day",
            "Close-up of a smooth freshly laid asphalt surface with a house in the background, Quebec residential neighborhood",
            "Paving contractor operating a skid steer removing old asphalt from a residential driveway, preparation work, daylight",
            "Before and after style photo of a freshly paved asphalt driveway beside an old cracked one, Quebec home",
            "Asphalt paving truck dumping hot mix into a commercial paver at the start of a driveway, professional crew, Quebec",
            "Worker applying asphalt sealcoating with a squeegee on a residential driveway, suburban Quebec, sunny day",
            "Wide shot of a long newly paved asphalt driveway leading to a large Quebec home, no people, bright daylight",
        ],
    },
    "pavage-commercial": {
        "config": f"{BASE}/engine_qc/config_pavage-commercial.json",
        "dist":   f"{BASE}/dist_pavage-commercial",
        "prompts": [
            "Commercial asphalt paving crew operating a large paver machine on a parking lot in Quebec, sunny day, professional photo",
            "Freshly paved commercial parking lot with crisp white line markings, Quebec business, bright daylight",
            "Heavy roller compacting hot mix asphalt on a large commercial parking lot surface, professional crew, Quebec",
            "Two workers painting parking space lines on a newly paved commercial asphalt lot, Quebec, sunny day",
            "Asphalt paving crew laying a new access road for a commercial building in Quebec, wide shot, daylight",
            "Commercial paving contractor operating a motor grader leveling a large asphalt base, professional equipment, Quebec",
            "Workers installing asphalt around a loading dock area of a commercial warehouse, Quebec, professional photo",
            "Aerial-style view of a large commercial parking lot being paved with fresh black asphalt, Quebec, sunny day",
            "Close-up of a paving machine screed laying smooth asphalt on a commercial lot, professional detail shot",
            "Commercial asphalt truck dumping hot mix into a paver on a large business parking lot, Quebec, daylight",
        ],
    },
    "prix-pave-uni": {
        "config": f"{BASE}/engine_qc/config_prix-pave-uni.json",
        "dist":   f"{BASE}/dist_prix-pave-uni",
        "prompts": [
            "Professional landscaper installing interlocking paving stones on a residential driveway in Quebec, sunny day, photorealistic",
            "Newly completed interlocking paver driveway with grey and charcoal stones in front of a Quebec home, no people",
            "Worker cutting paving stones with a masonry saw during a residential driveway installation, Quebec, daylight",
            "Landscaping crew laying interlocking pavers on a backyard patio, suburban Quebec home, bright sunny day",
            "Close-up of beautiful herringbone pattern interlocking pavers being installed on a driveway, Quebec residential",
            "Wide shot of a large completed paving stone driveway with a garage door in background, Quebec suburb, daylight",
            "Two workers tamping and leveling sand base before laying interlocking pavers, residential Quebec, sunny",
            "Interlocking stone pathway and steps leading to a front door of a Quebec home, professional landscaping",
            "Worker using a plate compactor to set interlocking pavers on a newly installed residential driveway, Quebec",
            "Before and after of a cracked concrete driveway replaced with beautiful interlocking pavers, Quebec home",
        ],
    },
    # ── USA NICHES (Pennsylvania) ─────────────────────────────────────────────
    "roofing_us": {
        "config": f"{ENGINE_USA}/config_roofing_us.json",
        "dist":   f"{ENGINE_USA}/dist_roofing_us",
        "prompts": [
            "Roofing contractor nailing asphalt shingles on a steep residential roof, Pennsylvania suburb, sunny day, professional photo",
            "Two roofers replacing old shingles on a colonial-style home, Pennsylvania neighborhood, daylight",
            "Close-up of a roofer's hands laying down architectural shingles with a nail gun, professional roofing work",
            "Roofing crew on a large two-storey home, new grey shingles being installed, sunny Pennsylvania day",
            "Metal roof installation in progress on a rural Pennsylvania home, standing seam panels, sunny day",
        ],
    },
    "paving_us": {
        "config": f"{ENGINE_USA}/config_paving_us.json",
        "dist":   f"{ENGINE_USA}/dist_paving_us",
        "prompts": [
            "Asphalt paving crew operating a commercial paver machine laying a new driveway, Pennsylvania suburb, sunny day",
            "Worker using a hand tamper to compact asphalt edges on a residential driveway, professional photo",
            "Freshly paved black asphalt driveway in front of a colonial home in Pennsylvania, no people, sunny",
            "Paving contractor operating a vibratory roller compacting hot mix asphalt on a residential job, daylight",
            "Two workers sealcoating a residential driveway with squeegees, suburban Pennsylvania neighborhood, sunny day",
        ],
    },
    "hvac_us": {
        "config": f"{ENGINE_USA}/config_hvac_us.json",
        "dist":   f"{ENGINE_USA}/dist_hvac_us",
        "prompts": [
            "HVAC technician installing a central air conditioning condenser unit beside a Pennsylvania home, sunny day, professional",
            "Two HVAC workers installing sheet metal ductwork in a residential attic, professional photo, Pennsylvania",
            "Technician servicing a high-efficiency gas furnace in a basement, tools visible, professional HVAC work",
            "New Carrier or Trane heat pump unit on a concrete pad beside a house exterior, no people, sunny day",
            "HVAC contractor connecting refrigerant lines and electrical to a new central AC outdoor unit, professional",
        ],
    },
    "plumber_us": {
        "config": f"{ENGINE_USA}/config_plumber_us.json",
        "dist":   f"{ENGINE_USA}/dist_plumber_us",
        "prompts": [
            "Licensed plumber installing a new 50-gallon water heater in a Pennsylvania home utility room, professional photo",
            "Plumber snaking a clogged drain in a residential bathroom, professional work, no face visible, daylight",
            "New copper and PEX pipe installation in a residential basement, neat workmanship, no people, wide shot",
            "Plumber under a kitchen sink connecting new supply lines and drain, wide shot from behind, professional",
            "New tankless water heater installed on a basement wall with copper pipes, no people, professional photo",
        ],
    },
    "kitchen_us": {
        "config": f"{ENGINE_USA}/config_kitchen_us.json",
        "dist":   f"{ENGINE_USA}/dist_kitchen_us",
        "prompts": [
            "Beautiful newly remodeled kitchen with white shaker cabinets, quartz countertops and subway tile backsplash, no people, bright natural light",
            "Kitchen renovation in progress with new grey cabinets installed, contractor visible from behind checking alignment",
            "Sleek modern kitchen with dark navy cabinets, gold hardware and marble-look quartz countertops, no people, photorealistic",
            "Open-concept kitchen remodel with large island, pendant lights and hardwood floor, Pennsylvania home, no people",
            "Kitchen cabinet installation in progress, worker securing upper cabinets to wall, wide shot, no face visible",
        ],
    },
    # ── NEW EN V3 NICHES ──────────────────────────────────────────────────────
    "flooring_en": {
        "config": f"{BASE_EN}/config_flooring_en.json",
        "dist":   f"{BASE}/dist_flooring_en",
        "prompts": [
            "Flooring contractor installing wide-plank hardwood flooring in a bright modern Canadian home, professional",
            "Worker using a pneumatic nailer to install engineered hardwood floor in a living room, no face visible",
            "Beautiful finished light oak hardwood floor in a spacious open-concept home, no people, natural light",
            "Flooring installer cutting luxury vinyl plank with a table saw, professional, residential installation",
            "New light maple hardwood floor refinished to a shine in a bright Canadian home interior, no people",
        ],
    },
    "painting_en": {
        "config": f"{BASE_EN}/config_painting_en.json",
        "dist":   f"{BASE}/dist_painting_en",
        "prompts": [
            "Professional house painter on an extension ladder painting white trim on a Canadian home exterior, sunny day",
            "Two painters in white overalls rolling paint on a large interior living room wall, bright daylight",
            "Painting contractor using an airless sprayer on a two-storey home exterior, professional photo",
            "Close-up of a professional painter cutting in paint along ceiling trim with a brush, interior work",
            "Freshly painted suburban home exterior in a classic grey with white trim, no people, sunny day",
        ],
    },
    "landscaping_en": {
        "config": f"{BASE_EN}/config_landscaping_en.json",
        "dist":   f"{BASE}/dist_landscaping_en",
        "prompts": [
            "Professional landscaping crew mowing a large suburban lawn with commercial equipment, sunny day, Canada",
            "Landscaper planting shrubs and perennials in a well-designed front yard garden, bright daylight",
            "Landscape crew laying sod rolls in a freshly graded backyard, professional photo, sunny day",
            "Worker using a commercial edger along a driveway border in a tidy suburban yard, daytime",
            "Beautiful finished landscape with stone path, flower beds and green lawn in a Canadian backyard, no people",
        ],
    },
    "fencing_en": {
        "config": f"{BASE_EN}/config_fencing_en.json",
        "dist":   f"{BASE}/dist_fencing_en",
        "prompts": [
            "Professional fence crew installing cedar board-on-board privacy fence in a suburban Canadian backyard, daylight",
            "Two workers setting vinyl fence posts with a post-hole digger, residential yard, sunny day",
            "Finished black aluminum ornamental fence installed around a front yard, manicured lawn, no people",
            "Contractor attaching cedar fence panels to pressure-treated posts in a backyard, professional photo",
            "New wood privacy fence with metal gate in a well-kept suburban yard, no people, sunny day",
        ],
    },
    "concrete_en": {
        "config": f"{BASE_EN}/config_concrete_en.json",
        "dist":   f"{BASE}/dist_concrete_en",
        "prompts": [
            "Concrete crew finishing a freshly poured residential driveway with bull float and trowel, sunny day, professional",
            "Worker screeding a concrete garage floor slab, wide shot, professional construction photo",
            "New stamped concrete patio installation in a Canadian backyard, workers applying pattern stamp, daylight",
            "Freshly finished concrete driveway in front of a modern suburban Canadian home, no people, sunny",
            "Concrete pump truck pouring concrete for a new residential foundation, construction site, daylight",
        ],
    },
    # ── THERMOPOMPE V4 NICHES (QC, May 2026) ─────────────────────────────────
    # ── THERMOPOMPE V4 NICHES (QC, May 2026) ─────────────────────────────────
    "thermopompe-aerothermique": {
        "config": f"{BASE}/engine_qc/config_thermopompe-aerothermique.json",
        "dist":   f"{BASE}/dist_thermopompe-aerothermique",
        "prompts": [
            # summer — installation, green yard, bright day
            "Two certified HVAC technicians installing a new outdoor heat pump unit on a concrete pad beside a Quebec home, lush green lawn and trees, bright summer day, professional photo",
            # spring — indoor unit mounting, fresh light
            "HVAC technician carefully mounting a sleek white wall-mounted heat pump indoor unit in a modern Quebec living room, spring morning light through window, professional photo",
            # autumn — outdoor unit beside house, fall colors
            "New heat pump outdoor condenser unit installed beside a residential Quebec home, maple trees with orange and red autumn foliage in background, no people, photorealistic",
            # winter — unit running in cold, proving capability
            "Outdoor heat pump unit operating beside a Quebec home in deep winter, snow on the ground, frost on nearby surfaces, steam from the defrost cycle, no people, photorealistic",
            # interior neutral — cozy living room, no season clue
            "Sleek white ductless mini-split heat pump mounted on the wall of a bright modern Quebec living room, no people, warm ambient lighting, photorealistic",
        ],
    },
    "reparation-thermopompe": {
        "config": f"{BASE}/engine_qc/config_reparation-thermopompe.json",
        "dist":   f"{BASE}/dist_reparation-thermopompe",
        "prompts": [
            # summer — tech with gauges, sunny residential
            "HVAC technician in uniform using digital manifold gauges to check refrigerant on a heat pump outdoor unit, green lawn, warm sunny summer day, professional photo",
            # autumn — inspection with flashlight, leaves on ground
            "Service technician inspecting a heat pump condenser coil with a flashlight, fallen autumn leaves around the unit, residential property, professional photo, no face visible",
            # winter — frozen unit, emergency repair
            "HVAC repair technician removing ice buildup from a heavily frosted heat pump outdoor unit in winter, snow on the ground, urgent service call, professional photo",
            # spring — preventive maintenance, fresh morning
            "Certified technician doing annual heat pump maintenance on a mild spring morning, green grass just growing back, residential Quebec property, professional photo",
            # interior neutral — working on indoor unit
            "HVAC technician accessing the control board of a wall-mounted heat pump indoor unit with tools, modern residential interior, professional photo, no season clues",
        ],
    },
    "climatisation-thermopompe": {
        "config": f"{BASE}/engine_qc/config_climatisation-thermopompe.json",
        "dist":   f"{BASE}/dist_climatisation-thermopompe",
        "prompts": [
            # summer — comfort inside on hot day
            "Bright airy Quebec living room with a sleek white heat pump on the wall, summer sun and green trees visible through large windows, comfortable cool interior, no people, photorealistic",
            # spring — installation, light jacket weather
            "HVAC technician installing a wall-mounted heat pump unit in a bedroom, spring installation, light jacket, green buds on trees through window, professional photo",
            # autumn — outdoor unit, colored leaves
            "New heat pump condenser unit installed on a concrete pad beside a Quebec home, vibrant red and orange maple leaves around it, autumn afternoon, no people, photorealistic",
            # winter — cozy inside, cold outside
            "Cozy modern Quebec bedroom with a white heat pump on the wall maintaining warmth, snow falling outside the window, warm indoor ambiance, no people, photorealistic",
            # neutral interior — bedroom or office, no season
            "Sleek wall-mounted heat pump unit in a bright modern bedroom, clean minimal interior design, no people, soft natural light, photorealistic",
        ],
    },
    "installation-thermopompe": {
        "config": f"{BASE}/engine_qc/config_installation-thermopompe.json",
        "dist":   f"{BASE}/dist_installation-thermopompe",
        "prompts": [
            # summer — two-tech crew, sunny green yard
            "Two HVAC technicians installing an outdoor heat pump unit on wall brackets beside a Quebec home, lush green summer yard, sunny day, professional photo",
            # spring — drilling through wall, fresh air
            "HVAC professional drilling through an exterior wall to route refrigerant lines for a new heat pump installation, spring day, green lawn, residential Quebec home, professional photo",
            # autumn — mounting indoor unit, fall light through window
            "Certified installer mounting a new heat pump indoor air handler on a living room wall, warm autumn light through window, Quebec home, professional photo",
            # winter — completed outdoor unit in snow
            "Newly installed heat pump outdoor condenser on a concrete pad beside a Quebec home in winter, snow on the ground, unit ready to operate, no people, photorealistic",
            # neutral — both units together, clean result
            "Completed heat pump installation showing sleek indoor wall unit and outdoor condenser unit side by side in a bright Quebec home, no people, photorealistic",
        ],
    },
    # ── PORTE-GARAGE V4 (QC, June 2026) ──────────────────────────────────────
    "porte-garage": {
        "config": f"{BASE}/engine_qc/config_porte-garage.json",
        "dist":   f"{BASE}/dist_porte-garage",
        "prompts": [
            # installation — summer, green yard, two techs
            "Two garage door installers mounting a new white steel insulated sectional garage door on a suburban Quebec home, green lawn and trees, bright sunny summer day, professional photo",
            # aspirational — modern aluminium door, no people, autumn
            "Beautiful modern full-view aluminium and glass garage door on a contemporary Quebec home, vibrant red and orange maple trees in the background, no people, photorealistic",
            # wood-look door — spring morning, curb appeal
            "Elegant faux-wood textured steel garage door on a well-maintained suburban Quebec home, fresh green lawn, spring morning light, no people, photorealistic",
            # winter — insulated door, snow on ground, isolation angle
            "New white insulated steel garage door on a Quebec residential home in winter, snow covering the driveway and lawn, warm light from inside visible, no people, photorealistic",
            # technician repair — spring, ressort replacement
            "Garage door repair technician replacing a torsion spring on a residential garage door, tool belt visible, suburban Quebec backyard, spring daylight, professional photo, no face visible",
            # opener installation — interior shot, technician on ladder
            "HVAC technician installing a new electric garage door opener motor on the ceiling of a residential garage, ladder and tools visible, bright interior lighting, professional photo",
            # close-up detail — carriage-style door hardware
            "Close-up of decorative carriage-style hardware and frosted glass inserts on a dark grey steel garage door, suburban Quebec home exterior, daylight, photorealistic",
            # double door — large home, summer, no people
            "Large double white sectional garage door on an upscale Quebec suburban home, manicured front lawn, flower beds, bright summer sun, no people, photorealistic",
            # autumn — technician inspection, maintenance call
            "Garage door service technician inspecting the rollers and track of a residential garage door from outside, warm autumn light and fallen leaves, professional uniform, no face visible",
            # before/after style — cracked old door vs new door on same house
            "Side-by-side view of an old rusty dented garage door on the left and a brand new modern insulated steel garage door on the right, same Quebec bungalow facade, realistic photo",
        ],
    },
    "roofing_uk": {
        "config": f"{BASE}/engine_uk/config_roofing_uk.json",
        "dist":   f"{BASE}/dist_roofing_uk",
        "prompts": [
            "Professional roofer fitting grey slate tiles on a steep pitched roof of a British terraced house, overcast UK sky, photorealistic",
            "Roofing contractor replacing concrete roof tiles on a semi-detached UK home, ladder against the house, daylight",
            "Close-up of a tradesperson nailing new roof tiles on a British residential property, cloudy sky background, professional photo",
            "Two roofers working on a flat roof installation with EPDM membrane on a UK commercial building, daylight",
            "Worker fitting uPVC fascia boards and soffits on a British brick house, overcast day, realistic photo",
            "Roofer in high-vis jacket inspecting ridge tiles on top of a traditional UK terraced house, wide shot",
            "New grey concrete roof tiles being laid on a semi-detached house in England, scaffolding visible, sunny day",
            "Professional roofer repairing lead flashing around a chimney stack on a British red-brick house, realistic",
            "Close-up of a worker replacing broken roof tiles on a Victorian terraced house in the UK, overcast sky",
            "Roofing team on scaffolding fitting new slate roof on a detached house in Scotland, green hills background",
        ],
    },
}

DEMENAGEMENT = {
    "script": f"{SITES}/script-demenagement.py",
    "dist":   f"{SITES}/dist_demenagement",
    "prompts": [
        "Professional movers carrying cardboard boxes out of a house to a moving truck, daytime",
        "Moving crew loading furniture into a large moving truck, residential neighborhood, sunny day",
        "Two professional movers wrapping furniture with protective blankets before loading into a truck",
        "Moving company workers carrying a sofa through a front doorway, professional photo, daylight",
        "Professional movers stacking labeled cardboard boxes inside a moving truck, organized move",
    ],
}


def call_flash(prompt):
    """Call gemini-3.1-flash-image-preview (generateContent) — returns 1 image as base64."""
    body = json.dumps({
        "contents": [{"parts": [{"text": f"Generate a photorealistic image: {prompt}"}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]}
    }).encode()
    req = urllib.request.Request(
        FLASH_URL, data=body,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        resp = json.loads(r.read())
    for part in resp.get("candidates", [{}])[0].get("content", {}).get("parts", []):
        if "inlineData" in part:
            return [part["inlineData"]["data"]]
    return []


def call_imagen(prompt, n=1, retries=2):
    """Use gemini-3.1-flash-image-preview (2k RPD) directly — no Imagen 4."""
    results = []
    for _ in range(n):
        try:
            imgs = call_flash(prompt)
            results.extend(imgs)
            time.sleep(7)
        except Exception as e:
            print(f"    Flash error: {e}")
            time.sleep(15)
    return results


def _call_imagen_original(prompt, n=1, retries=2):
    """Legacy Imagen 4 fast — kept for reference, not used."""
    body = json.dumps({
        "instances": [{"prompt": prompt}],
        "parameters": {
            "sampleCount": n,
            "aspectRatio": "16:9",
            "safetyFilterLevel": "block_few",
            "personGeneration": "allow_adult",
        }
    }).encode()
    for attempt in range(retries):
        req = urllib.request.Request(
            IMAGEN_URL, data=body,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                resp = json.loads(r.read())
            return [p["bytesBase64Encoded"] for p in resp.get("predictions", [])]
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"    Imagen 429 — switching to Flash fallback...")
                # Fall back to flash (1 image per call, loop n times)
                results = []
                for _ in range(n):
                    try:
                        imgs = call_flash(prompt)
                        results.extend(imgs)
                        time.sleep(3)
                    except Exception as fe:
                        print(f"    Flash error: {fe}")
                return results
            else:
                raise
    return []


def list_existing(dist):
    """Return sorted list of /img/hero-N.jpg paths already in dist/img/."""
    img_dir = os.path.join(dist, "img")
    if not os.path.isdir(img_dir):
        return []
    files = sorted(
        [f for f in os.listdir(img_dir) if f.startswith("hero-") and f.endswith(".jpg")],
        key=lambda x: int(x.replace("hero-","").replace(".jpg",""))
    )
    return [f"/img/{f}" for f in files]


def generate_for_niche(name, cfg):
    dist = cfg["dist"]
    img_dir = os.path.join(dist, "img")

    # Resume from existing partial set or skip if already complete
    existing = list_existing(dist)
    if len(existing) >= COUNT:
        print(f"  Already have {len(existing)} images — skipping")
        return existing[:COUNT]
    if existing:
        print(f"  Resuming from {len(existing)} existing images...")

    os.makedirs(img_dir, exist_ok=True)
    prompts = cfg["prompts"]
    # 5 prompts x 6 images = 30; make 2 calls per prompt (4 + 2) = 6
    per_prompt = (COUNT + len(prompts) - 1) // len(prompts)  # ceil(30/5) = 6

    saved = list(existing)
    idx = len(saved) + 1
    for prompt in prompts:
        if len(saved) >= COUNT:
            break
        remaining_for_prompt = per_prompt
        while remaining_for_prompt > 0 and len(saved) < COUNT:
            batch = min(remaining_for_prompt, 4)  # Imagen max 4 per call
            print(f"  Generating {batch}x: {prompt[:70]}...")
            try:
                images = call_imagen(prompt, batch)
                for b64 in images:
                    if len(saved) >= COUNT:
                        break
                    path = os.path.join(img_dir, f"hero-{idx}.jpg")
                    with open(path, "wb") as f:
                        f.write(base64.b64decode(b64))
                    saved.append(f"/img/hero-{idx}.jpg")
                    print(f"    Saved hero-{idx}.jpg")
                    idx += 1
                remaining_for_prompt -= batch
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="ignore")
                print(f"    HTTP {e.code}: {body[:200]}")
                break
            except Exception as e:
                print(f"    Error: {e}")
                break
            time.sleep(5)

    return saved


def update_json_config(config_path, local_pool):
    with open(config_path, encoding="utf-8") as f:
        d = json.load(f)
    d["images"]["use_local"] = True
    d["images"]["local_pool"] = local_pool
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"  Config updated: use_local=true, {len(local_pool)} images")


def update_demenagement_script(script_path, local_pool):
    import re
    with open(script_path, encoding="utf-8") as f:
        src = f.read()
    lines = [f'    "{u}",' for u in local_pool]
    new_list = "HERO_IMAGES_LOCAL = [\n" + "\n".join(lines) + "\n]"
    # Replace or add LOCAL pool
    if "HERO_IMAGES_LOCAL" in src:
        src_new = re.sub(r"HERO_IMAGES_LOCAL\s*=\s*\[.*?\]", new_list, src, flags=re.DOTALL)
    else:
        # Insert before HERO_IMAGES_PEXELS
        src_new = src.replace("HERO_IMAGES_PEXELS", new_list + "\nHERO_IMAGES_PEXELS", 1)
    # Set USE_LOCAL = True
    if "USE_LOCAL" in src_new:
        src_new = re.sub(r"USE_LOCAL\s*=\s*\w+", "USE_LOCAL = True", src_new)
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(src_new)
    print(f"  Demenagement script updated: {len(local_pool)} local images")


if __name__ == "__main__":
    # Filter by niche name if passed as argument
    target = sys.argv[1] if len(sys.argv) > 1 else None

    results = {}
    for name, cfg in NICHES.items():
        if target and name != target:
            continue
        existing = list_existing(cfg["dist"])
        if len(existing) >= COUNT:
            print(f"\n=== {name} === SKIP ({len(existing)} images déjà présentes)")
            continue
        print(f"\n=== {name} ===")
        pool = generate_for_niche(name, cfg)
        print(f"  Generated {len(pool)} images")
        if len(pool) >= 10:
            update_json_config(cfg["config"], pool)
            results[name] = len(pool)
        else:
            print(f"  WARN: only {len(pool)} images, skipping config update")
            results[name] = 0
        if not target:
            time.sleep(5)  # brief pause between niches

    # Demenagement (no JSON config — separate script)
    if not target or target == "demenagement":
        print(f"\n=== demenagement ===")
        pool = generate_for_niche("demenagement", DEMENAGEMENT)
        print(f"  Generated {len(pool)} images")
        if len(pool) >= 10:
            update_demenagement_script(DEMENAGEMENT["script"], pool)
            results["demenagement"] = len(pool)

    print("\n=== RESULTS ===")
    for name, count in results.items():
        status = "OK" if count >= COUNT else f"PARTIAL ({count})" if count > 0 else "FAILED"
        print(f"  {name}: {status}")
    print("\nDone. Run EmpireGenerator for each niche to regenerate sites.")
