"""
Replace ALL image pools with 30 verified, niche-relevant Pexels photos.
Uses official Pexels API — reads real photo titles before including.
"""
import json, urllib.request, urllib.parse, time, re, os

API_KEY = "nMisrB2I8IMhI9G61aUIQRAtunFKtlroUzr8IbCKgyBW9dLMkupIdQIX"
BASE    = r"C:/Users/bellj/OneDrive/Desktop/Programmatic seo/Empire-PSEO"
BASE_EN = r"C:/Users/bellj/OneDrive/Desktop/Programmatic seo/Empire-PSEO/sites_anglais"
SITES   = r"C:/Users/bellj/OneDrive/Desktop/Programmatic seo/Sites_relateds"

TARGET = 30

# Best search terms per niche (multiple to reach 30 unique photos)
NICHE_TERMS = {
    "calfeutrage":    ["window caulking", "weatherstripping", "home window exterior", "door insulation", "window frame seal"],
    "decontamination":["hazmat worker", "asbestos removal", "mold remediation", "protective suit cleanup", "industrial decontamination"],
    "emondage":       ["tree trimming arborist", "tree pruning", "arborist chainsaw", "tree removal service", "tree climbing worker"],
    "excavation":     ["excavator machine", "backhoe construction", "excavation site", "bulldozer", "construction heavy equipment"],
    "fosseseptique":  ["plumber pipe repair", "sewer pipe", "septic tank", "underground plumbing", "drain pipe"],
    "maconnerie":     ["bricklayer masonry", "brick wall construction", "stone masonry", "brickwork", "mason worker"],
    "paysagement":    ["lawn mowing landscaping", "garden landscaping", "landscaper", "lawn care service", "backyard landscaping"],
    "peinture":       ["house painter", "exterior house painting", "wall painting roller", "painting contractor", "interior painting"],
    "piscine":        ["swimming pool backyard", "inground pool installation", "pool contractor", "backyard swimming pool blue", "residential pool"],
    "roofing":        ["roofer installing shingles", "roofing contractor", "roof replacement", "shingles roof", "roof repair worker"],
    "hvac":           ["air conditioner outdoor unit", "hvac technician", "air conditioning installation", "furnace heating", "heat pump unit"],
    "waterproofing":  ["basement waterproofing", "foundation repair crack", "concrete basement", "foundation wall waterproof", "basement sealing"],
    "waterdamage":    ["water damage restoration", "flood damage home", "water damaged ceiling", "restoration worker cleanup", "flooded basement"],
    "demenagement":   ["movers moving boxes", "moving truck furniture", "professional movers", "moving day boxes", "moving company workers"],
}

CONFIGS = {
    "calfeutrage":    (f"{BASE}/config_calfeutrage.json",                  "json"),
    "decontamination":(f"{BASE}/config_decontamination.json",              "json"),
    "emondage":       (f"{BASE}/config_emondage.json",                     "json"),
    "excavation":     (f"{BASE}/config_excavation.json",                   "json"),
    "fosseseptique":  (f"{BASE}/config_fosseseptique.json",                "json"),
    "maconnerie":     (f"{BASE}/config_maconnerie.json",                   "json"),
    "paysagement":    (f"{BASE}/config_paysagement.json",                  "json"),
    "peinture":       (f"{BASE}/config_peinture.json",                     "json"),
    "piscine":        (f"{BASE}/config_piscine.json",                      "json"),
    "roofing":        (f"{BASE_EN}/config_roofing_en.json",                "json"),
    "hvac":           (f"{BASE_EN}/config_hvac_en.json",                   "json"),
    "waterproofing":  (f"{BASE_EN}/config_waterproofing_en.json",          "json"),
    "waterdamage":    (f"{BASE}/site_USA/config_waterdamage_us.json",      "json"),
    "demenagement":   (f"{SITES}/script-demenagement.py",                  "demenagement"),
    "plomberie":      (f"{BASE}/engine_qc/config_plomberie.json",           "json"),
    "cuisine":        (f"{BASE}/engine_qc/config_cuisine.json",             "json"),
    "salledebain":    (f"{BASE}/engine_qc/config_salledebain.json",         "json"),
    "electricien":    (f"{BASE}/engine_qc/config_electricien.json",         "json"),
    "plancher":       (f"{BASE}/engine_qc/config_plancher.json",            "json"),
    "soussol":        (f"{BASE}/engine_qc/config_soussol.json",             "json"),
}

def pexels_search(term, per_page=30, page=1):
    url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(term)}&per_page={per_page}&page={page}&orientation=landscape"
    req = urllib.request.Request(url, headers={"Authorization": API_KEY, "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def make_url(photo):
    pid = photo["id"]
    return f"https://images.pexels.com/photos/{pid}/pexels-photo-{pid}.jpeg?auto=compress&cs=tinysrgb&w=1200&h=600&fit=crop"

# Keywords that should appear in photo alt/title to confirm relevance
RELEVANCE_KEYWORDS = {
    "calfeutrage":    ["window","door","wall","seal","caulk","frame","home","house","exterior","insulation","renovation"],
    "decontamination":["hazmat","worker","suit","mask","protective","construction","industrial","clean","safety","contamination"],
    "emondage":       ["tree","wood","forest","branch","chainsaw","arborist","garden","nature","leaf","trunk","pruning"],
    "excavation":     ["excavator","construction","machine","bulldozer","backhoe","earth","site","heavy","equipment","truck","dirt"],
    "fosseseptique":  ["pipe","plumber","plumbing","sewer","drain","water","repair","worker","tool","valve","faucet","wrench"],
    "maconnerie":     ["brick","stone","wall","masonry","mortar","mason","concrete","build","cobble","arch","construct"],
    "paysagement":    ["lawn","garden","grass","landscape","mow","plant","yard","green","flower","outdoor","backyard"],
    "peinture":       ["paint","painter","brush","roll","wall","color","house","interior","exterior","renovation"],
    "piscine":        ["pool","swim","water","backyard","blue","residential","outdoor","luxury","resort","aqua"],
    "roofing":        ["roof","shingle","roofer","house","home","tile","construction","repair","worker","building"],
    "hvac":           ["air","conditioner","hvac","heat","cool","furnace","vent","unit","pump","technician","system"],
    "waterproofing":  ["basement","wall","concrete","foundation","crack","water","repair","seal","drain","pipe"],
    "waterdamage":    ["water","damage","flood","wet","restoration","cleanup","mold","leak","repair","ceiling","worker"],
    "demenagement":   ["move","moving","mover","box","truck","furniture","relocation","carry","pack","load"],
    "plomberie":      ["plumber","plumbing","pipe","faucet","sink","bathroom","water","repair","wrench","drain"],
    "cuisine":        ["kitchen","cabinet","renovation","countertop","modern kitchen","interior kitchen","cooking"],
    "salledebain":    ["bathroom","shower","bathtub","tile","vanity","renovation bathroom","modern bathroom"],
    "electricien":    ["electrician","electrical","wiring","panel","circuit","worker electric","power installation"],
    "plancher":       ["hardwood floor","flooring","wood floor","laminate floor","floor installation","tile floor"],
    "soussol":        ["basement","finished basement","basement renovation","drywall basement","underground room"],
}

def is_relevant(photo, niche):
    """Check if photo alt/photographer text contains niche keywords."""
    text = (photo.get("alt", "") + " " + photo.get("photographer", "")).lower()
    keywords = RELEVANCE_KEYWORDS.get(niche, [])
    return any(kw in text for kw in keywords)

def collect(terms, niche):
    urls = []
    seen_ids = set()
    skipped = 0
    for term in terms:
        if len(urls) >= TARGET:
            break
        try:
            for page in [1, 2]:
                if len(urls) >= TARGET:
                    break
                data = pexels_search(term, per_page=30, page=page)
                photos = data.get("photos", [])
                if not photos:
                    break
                for p in photos:
                    if p["id"] in seen_ids:
                        continue
                    seen_ids.add(p["id"])
                    if not is_relevant(p, niche):
                        skipped += 1
                        continue
                    url = make_url(p)
                    urls.append(url)
                    title = p.get("alt", "")
                    print(f"  OK [{p['id']}] {title[:70]}")
                    if len(urls) >= TARGET:
                        break
                time.sleep(0.3)
        except Exception as e:
            print(f"  API error '{term}': {e}")
    if skipped:
        print(f"  (filtered out {skipped} irrelevant photos)")
    return urls[:TARGET]

def update_demenagement(urls):
    path = f"{SITES}/script-demenagement.py"
    with open(path, encoding="utf-8") as f:
        src = f.read()
    lines = [f'    "{u}",  # Pexels' for u in urls]
    new_list = "HERO_IMAGES_PEXELS = [\n" + "\n".join(lines) + "\n]"
    src_new = re.sub(r"HERO_IMAGES_PEXELS\s*=\s*\[.*?\]", new_list, src, flags=re.DOTALL)
    with open(path, "w", encoding="utf-8") as f:
        f.write(src_new)

if __name__ == "__main__":
    results = {}
    for niche, (path, kind) in CONFIGS.items():
        print(f"\n=== {niche} ===")
        urls = collect(NICHE_TERMS[niche], niche)
        print(f"  -> {len(urls)} photos")
        if len(urls) < 10:
            print(f"  SKIP: not enough photos")
            results[niche] = 0
            continue
        if kind == "json":
            d = json.load(open(path, encoding="utf-8"))
            d["images"]["pexels_pool"] = urls
            with open(path, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
        elif kind == "demenagement":
            update_demenagement(urls)
        results[niche] = len(urls)
        print(f"  Saved {niche}")

    print("\n=== RESULTS ===")
    for niche, count in results.items():
        print(f"  {niche}: {count} images")
    print("\nAll done — clean up temp scripts now.")
