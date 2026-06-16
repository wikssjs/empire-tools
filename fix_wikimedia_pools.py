"""
Replace uncertain niche image pools with 100% relevant Wikimedia Commons CC images.
Uses open Wikimedia API — no auth required.
"""
import json, urllib.request, urllib.parse, hashlib, re, time

BASE    = r"C:/Users/bellj/OneDrive/Desktop/Programmatic seo/Empire-PSEO"
BASE_EN = r"C:/Users/bellj/OneDrive/Desktop/Programmatic seo/Empire-PSEO/sites_anglais"

NICHE_TERMS = {
    "calfeutrage":   ["window caulking", "door weatherstripping", "window seal foam", "home insulation window", "caulk sealant"],
    "emondage":      ["tree trimming arborist", "tree pruning", "chainsaw tree", "arborist climbing tree", "tree removal"],
    "piscine":       ["residential swimming pool backyard", "in-ground pool", "swimming pool blue water", "backyard pool", "outdoor pool"],
    "hvac":          ["air conditioner outdoor unit", "HVAC system", "air conditioning unit", "furnace heating", "heat pump"],
    "waterproofing": ["basement waterproofing", "foundation crack repair", "concrete basement wall", "foundation wall", "basement water"],
    "paysagement":   ["lawn mowing", "landscaping garden", "backyard garden landscaping", "garden maintenance", "lawn care"],
    "maconnerie":    ["bricklayer masonry", "brick wall construction", "stone masonry", "brickwork laying", "masonry worker"],
}

CONFIGS = {
    "calfeutrage":   f"{BASE}/config_calfeutrage.json",
    "emondage":      f"{BASE}/config_emondage.json",
    "piscine":       f"{BASE}/config_piscine.json",
    "hvac":          f"{BASE_EN}/config_hvac_en.json",
    "waterproofing": f"{BASE_EN}/config_waterproofing_en.json",
    "paysagement":   f"{BASE}/config_paysagement.json",
    "maconnerie":    f"{BASE}/config_maconnerie.json",
}

TARGET = 30

def wikimedia_search(term, limit=50):
    api = "https://commons.wikimedia.org/w/api.php"
    params = urllib.parse.urlencode({
        "action": "query", "list": "search",
        "srsearch": term, "srnamespace": 6,
        "srlimit": limit, "format": "json",
    })
    req = urllib.request.Request(f"{api}?{params}", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
    return [p["title"].replace("File:", "") for p in data.get("query", {}).get("search", [])]

def get_wikimedia_url(filename):
    name = filename.replace(" ", "_")
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in ["jpg", "jpeg", "png"]:
        return None
    md5 = hashlib.md5(name.encode()).hexdigest()
    a, b = md5[0], md5[:2]
    return f"https://upload.wikimedia.org/wikipedia/commons/{a}/{b}/{urllib.parse.quote(name)}"

def verify(url):
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            ct = r.headers.get("Content-Type", "")
            return r.status == 200 and "image" in ct
    except:
        return False

def collect(terms, need):
    all_urls = []
    seen = set()
    for term in terms:
        print(f"  Wikimedia: '{term}'")
        filenames = wikimedia_search(term, limit=50)
        for fn in filenames:
            url = get_wikimedia_url(fn)
            if not url or url in seen:
                continue
            if verify(url):
                all_urls.append(url)
                seen.add(url)
                print(f"  OK {fn[:60]}")
            else:
                print(f"  NO {fn[:60]}")
            time.sleep(0.1)
            if len(all_urls) >= need:
                break
        time.sleep(0.5)
        if len(all_urls) >= need:
            break
    return all_urls

if __name__ == "__main__":
    for niche, path in CONFIGS.items():
        print(f"\n=== {niche} ===")
        d = json.load(open(path, encoding="utf-8"))
        # Keep existing Pexels/StockSnap pool as fallback, replace with Wikimedia
        urls = collect(NICHE_TERMS[niche], TARGET)
        print(f"  Got {len(urls)} Wikimedia images")
        if len(urls) >= 10:
            # Fill remaining with existing pool if under 30
            existing = d["images"]["pexels_pool"]
            combined = list(dict.fromkeys(urls + existing))[:TARGET]
            d["images"]["pexels_pool"] = combined
            with open(path, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
            print(f"  Saved {niche}: {len(combined)} images ({len(urls)} Wikimedia)")
        else:
            print(f"  WARN: only {len(urls)} — keeping existing pool")
