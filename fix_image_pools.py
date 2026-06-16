"""
Replace all image pools with 30 niche-relevant Pexels photos.
Scrapes Pexels search pages (no API key needed), verifies CDN URLs.
"""
import json, urllib.request, urllib.parse, re, time, os

BASE = r"C:/Users/bellj/OneDrive/Desktop/Programmatic seo/Empire-PSEO"
BASE_EN = r"C:/Users/bellj/OneDrive/Desktop/Programmatic seo/Empire-PSEO/sites_anglais"
SITES_REL = r"C:/Users/bellj/OneDrive/Desktop/Programmatic seo/Sites_relateds"

TARGET = 30

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}

# Search terms per niche — multiple terms to get 30 unique photos
NICHE_TERMS = {
    # QC
    "calfeutrage":    ["window caulking", "weatherstripping home", "door seal exterior", "window insulation home", "home exterior renovation"],
    "decontamination":["hazmat worker cleanup", "mold remediation", "asbestos removal worker", "industrial cleaning protective suit", "contamination cleanup crew"],
    "emondage":       ["tree pruning arborist", "tree trimming chainsaw", "arborist work", "tree removal service", "tree surgeon climbing"],
    "excavation":     ["excavator digging", "construction excavator", "backhoe construction", "excavation site", "bulldozer earth moving"],
    "fosseseptique":  ["sewer pipe plumbing", "drainage pipe", "underground pipe installation", "plumber pipes", "water pipe repair"],
    "maconnerie":     ["bricklayer masonry", "stone wall masonry", "brick laying construction", "mason brickwork", "stone masonry repair"],
    "paysagement":    ["landscaping garden", "lawn mowing service", "garden landscaper", "backyard landscaping", "grass lawn maintenance"],
    "peinture":       ["house painting exterior", "painter painting wall", "interior house painting", "painter roller brush", "home painting contractor"],
    "piscine":        ["swimming pool construction", "backyard swimming pool", "pool installation", "in-ground pool blue water", "residential swimming pool"],
    # EN Canada
    "roofing":        ["roof replacement shingles", "roofer installing shingles", "roofing contractor", "roof repair worker", "house roof construction"],
    "hvac":           ["hvac air conditioner unit", "air conditioning installation", "hvac technician repair", "furnace heating system", "air conditioning outdoor unit"],
    "waterproofing":  ["basement waterproofing", "foundation waterproofing", "basement wall repair crack", "concrete foundation repair", "basement sealing"],
    # USA
    "waterdamage":    ["water damage restoration", "flood damage home", "water damage ceiling", "restoration worker water damage", "flooded basement cleanup"],
    # Demenagement
    "demenagement":   ["moving truck loading furniture", "movers carrying boxes", "moving boxes home", "professional movers furniture", "moving day boxes truck"],
}

def pexels_search(term, page=1):
    """Scrape Pexels search and return list of photo IDs."""
    url = f"https://www.pexels.com/search/{urllib.parse.quote(term)}/?page={page}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode("utf-8", errors="ignore")
        ids = re.findall(r"/photos/(\d{5,9})/", html)
        return list(dict.fromkeys(ids))  # deduplicate preserving order
    except Exception as e:
        print(f"  Pexels error '{term}' p{page}: {e}")
        return []

def make_url(photo_id):
    return f"https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.jpeg?auto=compress&cs=tinysrgb&w=1200&h=600&fit=crop"

def verify_url(url):
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            ct = r.headers.get("Content-Type", "")
            return r.status == 200 and "image" in ct
    except:
        return False

def collect_pexels(terms, need):
    candidates = []
    seen = set()
    for term in terms:
        for page in [1, 2]:
            print(f"  Scraping Pexels: '{term}' page {page}")
            for pid in pexels_search(term, page):
                if pid not in seen:
                    seen.add(pid)
                    candidates.append(pid)
            time.sleep(0.5)
            if len(candidates) >= need * 2:
                break
        if len(candidates) >= need * 2:
            break

    print(f"  Verifying {len(candidates)} candidates, need {need}...")
    verified = []
    for pid in candidates:
        if len(verified) >= need:
            break
        url = make_url(pid)
        if verify_url(url):
            verified.append(url)
            print(f"  OK {pid}")
        else:
            print(f"  NO {pid}")
        time.sleep(0.15)
    return verified

def update_json_config(path, urls):
    d = json.load(open(path, encoding="utf-8"))
    d["images"]["pexels_pool"] = urls
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def update_demenagement(urls):
    path = f"{SITES_REL}/script-demenagement.py"
    with open(path, encoding="utf-8") as f:
        src = f.read()
    lines = [f'    "{u}",  # Pexels' for u in urls]
    new_list = "HERO_IMAGES_PEXELS = [\n" + "\n".join(lines) + "\n]"
    src_new = re.sub(r"HERO_IMAGES_PEXELS\s*=\s*\[.*?\]", new_list, src, flags=re.DOTALL)
    with open(path, "w", encoding="utf-8") as f:
        f.write(src_new)

CONFIGS = {
    "calfeutrage":    (f"{BASE}/config_calfeutrage.json",    "json"),
    "decontamination":(f"{BASE}/config_decontamination.json","json"),
    "emondage":       (f"{BASE}/config_emondage.json",       "json"),
    "excavation":     (f"{BASE}/config_excavation.json",     "json"),
    "fosseseptique":  (f"{BASE}/config_fosseseptique.json",  "json"),
    "maconnerie":     (f"{BASE}/config_maconnerie.json",     "json"),
    "paysagement":    (f"{BASE}/config_paysagement.json",    "json"),
    "peinture":       (f"{BASE}/config_peinture.json",       "json"),
    "piscine":        (f"{BASE}/config_piscine.json",        "json"),
    "roofing":        (f"{BASE_EN}/config_roofing_en.json",  "json"),
    "hvac":           (f"{BASE_EN}/config_hvac_en.json",     "json"),
    "waterproofing":  (f"{BASE_EN}/config_waterproofing_en.json", "json"),
    "waterdamage":    (f"{BASE}/site_USA/config_waterdamage_us.json", "json"),
    "demenagement":   (None, "demenagement"),
}

if __name__ == "__main__":
    results = {}
    for niche, (path, kind) in CONFIGS.items():
        print(f"\n=== {niche} ===")
        urls = collect_pexels(NICHE_TERMS[niche], TARGET)
        print(f"  Got {len(urls)} verified URLs")
        if len(urls) < 10:
            print(f"  WARNING: only {len(urls)}, skipping")
            results[niche] = len(urls)
            continue
        if kind == "json":
            update_json_config(path, urls)
        elif kind == "demenagement":
            update_demenagement(urls)
        results[niche] = len(urls)
        print(f"  Saved {niche}: {len(urls)} images")

    print("\n=== RESULTS ===")
    for niche, count in results.items():
        status = "OK" if count >= TARGET else f"WARN {count}"
        print(f"  {niche}: {status}")
