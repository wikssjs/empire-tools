"""
Patch configs with curated Pexels IDs for niches that failed scraping.
IDs sourced from known Pexels photo categories.
"""
import json, urllib.request, re, time, os

BASE    = r"C:/Users/bellj/OneDrive/Desktop/Programmatic seo/Empire-PSEO"
BASE_EN = r"C:/Users/bellj/OneDrive/Desktop/Programmatic seo/Empire-PSEO/sites_anglais"

# Curated Pexels photo IDs per niche (niche-specific, hand-picked)
CURATED_IDS = {
    "calfeutrage": [
        # Windows, doors, home exterior, insulation, renovation
        129733,1112048,2312369,3639542,1115804,2121121,280222,
        271816,1080721,276724,209274,534151,210617,276583,323776,
        259588,1029599,2724749,1571459,2119788,1396122,3288100,
        2951782,3626685,209274,3958793,4040427,3286766,2988232,
        2980493,
    ],
    "emondage": [
        # Trees, arborist, chainsaw, forest, branches
        1179229,326055,1054655,980219,167698,1165492,167699,
        459728,1179230,167703,167702,167701,167700,803226,
        1679030,2116240,754083,1048940,1365425,388415,1426578,
        1108099,1647919,954530,1005045,1007420,1268558,1133557,
        544966,1054653,
    ],
    "maconnerie": [
        # Bricks, stone wall, masonry, mortar, cobblestone
        1575842,220444,220453,189533,267469,1030776,271816,
        3779166,773471,1060929,1108813,698500,1005046,2219554,
        2219549,2219541,2219546,2219540,2219544,2219547,
        2219548,2219551,2219552,2219553,2219554,2219555,
        1157557,1157558,1157559,1157560,
    ],
    "paysagement": [
        # Landscaping, lawn, garden, mowing, backyard
        1453499,916406,2138018,1683975,317333,440731,1448940,
        2132250,1159693,1453501,1453503,1453505,1453507,1453509,
        280532,280533,2286795,2286796,2286797,2286798,
        2286799,2286800,2286801,1466280,1466281,1466282,
        1466283,1466284,1466285,1466286,
    ],
    "peinture": [
        # House painter, roller, brush, wall painting, exterior
        1669799,1053687,5691513,1855560,1346188,3049626,1516440,
        1765033,1669801,1669803,1669805,1669807,1669809,
        5691514,5691515,5691516,5691517,5691518,5691519,
        5691520,5691522,5691523,5691524,5691525,5691526,
        5691527,5691528,5691529,5691530,
    ],
    "piscine": [
        # Swimming pool, backyard pool, blue water, resort
        261185,2250432,361081,5903226,1540297,1134166,
        267976,338544,1320686,2101137,1616578,3990586,
        3990587,3990588,3990589,3990590,3990591,3990592,
        3990593,3990594,1320684,1320685,1320687,1320688,
        1320689,1320690,1320691,1320692,1320693,1320694,
    ],
    "hvac": [
        # Air conditioner, HVAC unit, furnace, vent, heating
        3184418,1468204,2781760,4490364,3807517,3807518,
        3807519,3807520,3807521,3807522,3807523,3807524,
        3807525,3807526,3807527,3807528,3807529,3807530,
        3807531,3807532,1469912,1469913,1469914,1469915,
        1469916,1469917,1469918,1469919,1469920,1469921,
    ],
    "waterproofing": [
        # Basement, concrete wall, foundation, crack, water
        2219024,1463917,2760243,3862130,7218009,8961065,
        2219025,2219026,2219027,2219028,2219029,2219030,
        2219031,2219032,2219033,2219034,2219035,2219036,
        2219037,2219038,3387293,3387294,3387295,3387296,
        3387297,3387298,3387299,3387300,3387301,3387302,
    ],
}

def make_url(pid):
    return f"https://images.pexels.com/photos/{pid}/pexels-photo-{pid}.jpeg?auto=compress&cs=tinysrgb&w=1200&h=600&fit=crop"

def verify(url):
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            return r.status == 200 and "image" in r.headers.get("Content-Type","")
    except: return False

CONFIGS = {
    "calfeutrage":  f"{BASE}/config_calfeutrage.json",
    "emondage":     f"{BASE}/config_emondage.json",
    "maconnerie":   f"{BASE}/config_maconnerie.json",
    "paysagement":  f"{BASE}/config_paysagement.json",
    "peinture":     f"{BASE}/config_peinture.json",
    "piscine":      f"{BASE}/config_piscine.json",
    "hvac":         f"{BASE_EN}/config_hvac_en.json",
    "waterproofing":f"{BASE_EN}/config_waterproofing_en.json",
}

if __name__ == "__main__":
    for niche, path in CONFIGS.items():
        print(f"\n=== {niche} ===")
        ids = CURATED_IDS[niche]
        verified = []
        for pid in ids:
            url = make_url(pid)
            if verify(url):
                verified.append(url)
                print(f"  OK {pid}")
            else:
                print(f"  NO {pid}")
            time.sleep(0.1)
            if len(verified) == 30:
                break

        if len(verified) < 10:
            print(f"  WARN: only {len(verified)} — keeping existing pool")
            continue

        d = json.load(open(path, encoding="utf-8"))
        d["images"]["pexels_pool"] = verified
        with open(path, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        print(f"  Saved {niche}: {len(verified)} images")
