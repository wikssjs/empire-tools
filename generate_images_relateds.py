"""
Generate hero images for Sites_relateds niches using Gemini 2.5 Flash Image (Nano Banana 2).
Saves 30 images per niche to pages_{niche}/img/hero-N.jpg
Usage: python generate_images_relateds.py
"""
import os, base64, json, time, sys, urllib.request, urllib.error

GEMINI_KEY = "AIzaSyCSTSlGdpD9wLN93_fe2GYVRFnluJ4uoz8"
FLASH_URL  = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key={GEMINI_KEY}"
BASE       = r"C:/Users/bellj/OneDrive/Desktop/Programmatic seo/Sites_relateds"
COUNT      = 100  # images per niche
SLEEP_SEC  = 7    # ~8-9 images/min to stay under 10 IPM limit

NICHES = {
    "thermopompe": {
        "dist": f"{BASE}/pages_thermopompe",
        "prompts": [
            "Professional HVAC technician installing a white modern heat pump unit on exterior brick wall of a Quebec house, sunny day, photorealistic",
            "Close-up of a new Mitsubishi heat pump mounted on exterior wall, clean installation, residential home, daylight",
            "Two HVAC workers installing a split system heat pump outdoor unit on a suburban home, professional photo",
            "Modern white heat pump unit installed beside a house foundation in a Quebec backyard, autumn day",
            "Technician connecting electrical wiring to a new heat pump outdoor condenser unit, professional work",
        ],
    },
    "fissure": {
        "dist": f"{BASE}/pages_fissure",
        "prompts": [
            "Worker injecting epoxy resin into a foundation crack in a concrete basement wall, professional photo",
            "Close-up of polyurethane foam injection repair on a basement foundation crack, professional contractor",
            "Foundation repair specialist applying waterproof sealant to a cracked concrete wall, interior basement",
            "Professional worker repairing a structural crack in a poured concrete foundation wall, daylight",
            "Contractor using injection equipment to seal a horizontal crack in a basement foundation wall",
        ],
    },
    "toiture": {
        "dist": f"{BASE}/pages_toiture",
        "prompts": [
            "Professional roofer installing asphalt shingles on a residential home roof, sunny day Quebec, photorealistic",
            "Two roofing contractors nailing new shingles on a steep pitched roof, bright daylight, professional photo",
            "Roofer carrying shingle bundles up a ladder to a residential roof replacement job",
            "Close-up of roofer hand-nailing asphalt shingles on a new roof installation, skilled tradesperson",
            "Roofing crew working on a large residential roof replacement in a Quebec suburb, professional photo",
        ],
    },
    "fenetres": {
        "dist": f"{BASE}/pages_fenetres",
        "prompts": [
            "New white vinyl double-pane window installed on a brick Quebec house exterior, close-up, daylight, photorealistic",
            "Modern energy-efficient window frames installed on a suburban home exterior, bright sunny day",
            "Close-up of a freshly installed uPVC window with clean caulk seal on a house wall, professional finish",
            "Row of new white vinyl windows on a renovated Quebec home exterior, sunny day, photorealistic",
            "Two workers standing on the ground installing a large window on a house ground floor, professional photo",
        ],
    },
    "revetement": {
        "dist": f"{BASE}/pages_revetement",
        "prompts": [
            "Newly installed white vinyl siding on a Quebec house exterior, clean professional finish, sunny day",
            "Worker standing on the ground installing vinyl siding panels on the lower section of a house, photorealistic",
            "Close-up of interlocking vinyl siding panels being installed on a home exterior wall, daylight",
            "Beautiful suburban Quebec home with freshly installed gray fiber cement board siding, photorealistic",
            "Two contractors at ground level fitting vinyl cladding panels on a house wall, professional photo",
        ],
    },
    "gouttieres": {
        "dist": f"{BASE}/pages_gouttieres",
        "prompts": [
            "Close-up of new seamless aluminum gutters installed on a Quebec house fascia, clean finish, daylight",
            "New white vinyl rain gutters and downspout on a suburban home exterior, photorealistic",
            "Worker standing on the ground securing a gutter downspout bracket to a brick wall, professional",
            "Freshly installed aluminum gutters on a residential home, water flowing cleanly, sunny day",
            "Professional gutter system with downspout installed on a Quebec house, ground-level view, photorealistic",
        ],
    },
    "isolation": {
        "dist": f"{BASE}/pages_isolation",
        "prompts": [
            "Professional insulation contractor spraying open-cell foam insulation in an attic, worker standing on floor joists, photorealistic",
            "Attic fully covered with thick blown-in cellulose insulation, professional installation, bright lighting",
            "Worker standing in a basement spraying polyurethane foam insulation on walls, protective suit, bright lights",
            "Close-up of pink fiberglass batt insulation installed between wall studs, clean professional work",
            "Finished attic insulation with thick layer of spray foam covering all rafters, professional result",
        ],
    },
    "demenagement": {
        "dist": f"{BASE}/pages_demenagement",
        "prompts": [
            "Professional movers in uniform carrying large cardboard boxes from a house entrance to a moving truck, sunny day",
            "Moving company team loading furniture into a large white moving truck parked in a driveway, photorealistic",
            "Two professional movers carrying a wrapped sofa through a front door, ground level, daylight",
            "Moving crew using a wheeled dolly to move stacked boxes to a truck, residential street, professional",
            "Professional movers carefully wrapping furniture in blankets next to a moving truck, sunny day",
        ],
    },
    "drain": {
        "dist": f"{BASE}/pages_drain",
        "prompts": [
            "Workers at ground level installing a French drain with perforated pipe and gravel around a house foundation",
            "Close-up of perforated PVC drainage pipe being laid in a gravel-filled trench, professional installation",
            "Excavator digging a trench around a residential foundation for French drain installation, daylight",
            "Close-up of perforated drainage pipe surrounded by crushed stone in a foundation trench, photorealistic",
            "Waterproofing membrane and drainage pipe installed on a concrete foundation wall, professional work",
        ],
    },
    "deneigement": {
        "dist": f"{BASE}/dist",
        "prompts": [
            "Worker operating a commercial snowblower clearing a residential driveway after heavy snowfall, Quebec winter",
            "Snow removal truck with plow clearing a parking lot after a snowstorm, daytime, photorealistic",
            "Two workers shoveling snow from a front walkway and stairs of a Quebec home, winter morning",
            "Professional snowblower machine clearing a wide driveway, snow flying, bright winter day",
            "Snow removal team with equipment clearing a commercial property parking lot, Quebec winter, photorealistic",
        ],
    },
    "extermination": {
        "dist": f"{BASE}/dist_extermination",
        "prompts": [
            "Professional exterminator in uniform kneeling and spraying pest control treatment along a baseboard, photorealistic",
            "Pest control technician crouching to inspect and treat a basement corner for insects, professional",
            "Exterminator in protective gear applying treatment around a home foundation at ground level, daylight",
            "Professional pest control worker placing bait stations along a wall, residential home, photorealistic",
            "Pest control technician standing and using a sprayer to treat a residential kitchen, professional uniform",
        ],
    },
    "pavage": {
        "dist": f"{BASE}/dist_pavage",
        "prompts": [
            "Professional paving crew operating a roller compactor on freshly laid asphalt driveway, steam rising, daylight",
            "New smooth black asphalt driveway freshly completed on a suburban Quebec home, photorealistic",
            "Worker using a hand tamper at ground level to compact fresh asphalt on a driveway edge, professional",
            "Asphalt paver machine laying hot mix on a residential driveway, professional crew, sunny day",
            "Beautiful newly paved black asphalt driveway with crisp clean edges on a Quebec property, photorealistic",
        ],
    },
}


def list_existing(dist_dir):
    img_dir = os.path.join(dist_dir, "img")
    if not os.path.isdir(img_dir):
        return []
    return [f for f in os.listdir(img_dir) if f.startswith("hero-") and f.endswith(".jpg")]


def call_flash(prompt):
    """Call gemini-2.5-flash-image — returns list of raw image bytes."""
    body = json.dumps({
        "contents": [{"parts": [{"text": f"Generate a photorealistic image: {prompt}. No text, no watermarks, no logos."}]}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]},
    }).encode()
    req = urllib.request.Request(FLASH_URL, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
        images = []
        for cand in data.get("candidates", []):
            for part in cand.get("content", {}).get("parts", []):
                if "inlineData" in part:
                    images.append(base64.b64decode(part["inlineData"]["data"]))
        return images
    except urllib.error.HTTPError as e:
        body_err = e.read().decode()
        print(f"    HTTP {e.code}: {body_err[:200]}")
        raise


def generate_for_niche(niche, cfg):
    dist_dir = cfg["dist"]
    img_dir  = os.path.join(dist_dir, "img")
    os.makedirs(img_dir, exist_ok=True)

    existing = list_existing(dist_dir)
    existing_indices = set()
    for f in existing:
        try:
            existing_indices.add(int(f.replace("hero-", "").replace(".jpg", "")))
        except ValueError:
            pass

    needed = [i for i in range(COUNT) if i not in existing_indices]
    if not needed:
        print(f"  [{niche}] Already {COUNT} images — skipping")
        return

    print(f"  [{niche}] Generating {len(needed)} images (have {len(existing_indices)}/{COUNT})...")
    prompts = cfg["prompts"]

    for idx in needed:
        prompt = prompts[idx % len(prompts)]
        out_path = os.path.join(img_dir, f"hero-{idx}.jpg")
        retries = 3
        for attempt in range(retries):
            try:
                imgs = call_flash(prompt)
                if not imgs:
                    print(f"    [{niche}] hero-{idx}: empty response, retry {attempt+1}")
                    time.sleep(10)
                    continue
                with open(out_path, "wb") as f:
                    f.write(imgs[0])
                print(f"    [{niche}] hero-{idx}.jpg saved ({len(imgs[0])//1024}KB)")
                time.sleep(SLEEP_SEC)
                break
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    print(f"    [{niche}] hero-{idx}: 429 rate limit — waiting 60s...")
                    time.sleep(60)
                else:
                    print(f"    [{niche}] hero-{idx}: HTTP {e.code} — retry {attempt+1}")
                    time.sleep(15)
            except Exception as ex:
                print(f"    [{niche}] hero-{idx}: error {ex} — retry {attempt+1}")
                time.sleep(15)
        else:
            print(f"    [{niche}] hero-{idx}: FAILED after {retries} attempts")


if __name__ == "__main__":
    niches_to_run = sys.argv[1:] if len(sys.argv) > 1 else list(NICHES.keys())
    print(f"Generating images for: {niches_to_run}")
    print(f"Total: {len(niches_to_run) * COUNT} images at ~{SLEEP_SEC}s each\n")
    for niche in niches_to_run:
        if niche not in NICHES:
            print(f"Unknown niche: {niche}")
            continue
        generate_for_niche(niche, NICHES[niche])
    print("\nDone.")
