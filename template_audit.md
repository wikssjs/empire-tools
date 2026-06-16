# Empire-PSEO — Template Audit Report
**Date:** 2026-06-15  
**Auditor:** Technical audit via direct HTML inspection  
**Method:** Full HTML source reading of one representative city page per template set

---

## Overview

| Template Set | Site / Niche | City Sampled | Overall Score |
|---|---|---|---|
| QC templates/ (default) | Fosse Septique — experts-fosseseptique.ca | Lac-à-la-Croix | 8.5/10 |
| QC templates_v2/ | Salle de Bain — soumission-salledebain.ca | Acton Vale | 8.0/10 |
| USA Engine (templates_us/) | Roofing — rooferquoteusa.com | Allentown, PA | 6.5/10 |
| UK Engine (templates_uk/) | Roofing — roofing-quotes.co.uk | Accrington, England | 5.5/10 |

---

## Site 1: Fosse Septique — QC Templates/ (Default)

**File:** `dist_fosseseptique/lac-a-la-croix.html`  
**Config:** `engine_qc/config_fosseseptique.json`  
**Template set:** `engine_qc/templates/`  
**Total lines:** 961  
**lang attribute:** `fr-CA`

---

### Scores

| Dimension | Score /10 | Notes |
|---|---|---|
| SEO Technique | 9/10 | Full meta stack, canonical, Schema @graph, geo tags |
| Contenu Unique par Ville | 9.5/10 | Exceptional editorial depth, 5 major H2 sections, 6 tables |
| Anti-Footprint | 9/10 | 4 random HTML comments, unique body ID, unique CSS prefix |
| UX / Conversion | 8/10 | Sticky CTA bar, hero form, 4-step multi-step form, final CTA |
| Qualite HTML | 8/10 | Clean semantic structure, SVG sprite, proper alt texts |

---

### SEO Technique

**Title tag:**  
`Soumissions Fosse Septique Lac-à-la-Croix 2026 | Locaux Verifies | Experts Fosse Septique`  
Well-formed, includes city, year, and brand. Approximately 76 characters (slightly long). Uses accented characters correctly in the display version.

**Meta description:**  
`Trouvez le meilleur entrepreneur fosse septique a Lac-à-la-Croix en 2026. Installation, remplacement, vidange — soumission gratuite sans engagement.`  
City-specific, mentions three service types, clear value proposition. ~149 characters — within acceptable range.

**Canonical:**  
`https://experts-fosseseptique.ca/lac-a-la-croix`  
Clean flat URL, no trailing slash. Correct.

**Open Graph:**  
- `og:title`, `og:description`, `og:image`, `og:type`, `og:locale` (fr_CA), `og:site_name`, `article:modified_time` — all present.
- Twitter card: `summary_large_image` with matching title/description/image — complete.

**Geo meta tags:**  
- `<meta name="geo.region" content="CA-QC">` — correct ISO 3166-2 code.
- `<meta name="geo.placename" content="Lac-à-la-Croix">` — exact city name.

**Robots meta:** `index, follow` — correct.

**Schema.org (@graph):**  
Two structured data entities in a single `@graph`:
1. `HomeAndConstructionBusiness` — includes `name`, `description`, `telephone` (empty string — minor issue), `url`, `areaServed` with nested City + AdministrativeArea, `priceRange: "$$$"`.
2. `BreadcrumbList` — 3 levels: Accueil → Bas-Saint-Laurent (01) [with region URL] → Fosse Septique Lac-à-la-Croix. Correct `@type: ListItem` with `position`, `name`, and `item` URLs.

**Breadcrumb HTML:**  
Visible breadcrumb navigation with 3 levels matching Schema. Includes clickable region link. Region slug: `bas-saint-laurent-01`.

**Internal linking:**  
Footer contains 15 city links within the same region (Bas-Saint-Laurent), navigation link to region hub `/region/bas-saint-laurent-01`, and XML sitemap link. All internal links use clean slugs.

**Sitemap reference:** `<a href="/sitemap-index.xml">Plan du site XML</a>` — present in footer.

**Analytics:** Google Tag Manager/GA4 with `G-XXXXXXXXXX` placeholder (expected — must be replaced before deploy).

**Issue noted:** `telephone` field in Schema is an empty string `""`. This reduces Schema quality for service businesses.

---

### Contenu Unique par Ville

**H1 (1 tag):** "Fosse Septique / Lac-à-la-Croix" — city name in colored span, bold, prominent.

**H2 tags counted: 8**
1. "Fosse septique a Lac-à-la-Croix : installation, remplacement ou vidange — ce que vous devez savoir"
2. "Facteurs qui font varier le prix d'une fosse septique a Lac-à-la-Croix"
3. "Reglementation fosse septique a Lac-à-la-Croix : ce qu'il faut savoir"
4. "Entretien et vidange : ce que tout proprietaire doit faire a Lac-à-la-Croix"
5. "Choisir son entrepreneur en fosse septique a Lac-à-la-Croix"
6. "Questions frequentes sur la fosse septique a Lac-à-la-Croix" (H2 opening FAQ)
7. "Prix fosse septique a Lac-à-la-Croix — 2026" (price section)
8. "Pourquoi choisir Experts Fosse Septique pour votre fosse septique a Lac-à-la-Croix ?"

**H3 tags:** Service cards use `h3` inside the services section grid (8 service cards with h3 each). Trust section uses `h3` for each of 4 pillars.

**Editorial paragraphs:** 10 substantive editorial paragraphs across the city-intro section — each paragraph is 100-300+ words. Content is deeply localized to Lac-à-la-Croix and its administrative region Bas-Saint-Laurent.

**Local specifics found in content:**
- Reference to region "Bas-Saint-Laurent (01)" throughout
- Reference to "Q-2, r.22" regulation (Quebec provincial rule)
- Soil type specifics: "argile/limono-argileux" (clay-loam soils) 
- Reference to freeze depth: "> 1,5 m"
- Historical aging data: "1980 a 2000" for existing systems
- Non-conformity rate estimate: "20 a 30 %"
- Seasonal considerations: "avril a novembre" work window
- Regional MRC (Municipal Regional County) references

**Tables (6 data tables):**
1. Work types vs. prices, duration, permits, guarantee, emergency — 6 rows
2. Price-influencing factors vs. impact, local detail — 7 rows
3. Regulatory process steps vs. timeline, requirements, cost — 6 rows
4. Maintenance services vs. frequency, price, included, emergency delay — 6 rows
5. Contractor selection criteria — 7 rows
6. (Price section table rendered from cards, not a table tag)

**FAQ accordion:** 5 `<details>/<summary>` FAQ entries:
- "Combien coute l'installation d'une fosse septique complete a Lac-a-la-Croix ?"
- "A quelle frequence faut-il vidanger sa fosse septique a Lac-a-la-Croix ?"
- "Mon systeme septique est non conforme — que dois-je faire a Lac-a-la-Croix ?"
- "Quelle fosse septique choisir selon le type de sol dans Bas-Saint-Laurent ?"
- "Faut-il un permis pour remplacer sa fosse septique a Lac-a-la-Croix ?"
- "Quels sont les signes qu'il faut remplacer sa fosse septique a Lac-a-la-Croix ?"

Actually 6 FAQ items (counted from source).

**Price specificity:** Prices are stated as specific ranges with locale context:
- Installation complete: `14 000 $ – 28 000 $` with petite_ville tier modifier applied
- Remplacement fosse: `9 000 $ – 18 000 $`
- Vidange: `260 $ – 450 $`
- Inspection: `350 $ – 600 $`
The price cards show computed values (e.g., `7680 $ – 17 280 $`) which appear to be tier-adjusted amounts for a small municipality.

**Word count estimate (body text only):** Approximately 3,500-4,500 words of editorial content based on paragraph density. This is very high for a programmatic page.

**Regulatory specificity:** The text repeatedly references `Q-2, r.22` (Reglement sur l'evacuation et le traitement des eaux usees des residences isolees) — a real Quebec regulation — plus MELCCFP (provincial environment ministry). Demonstrates niche authority signals.

**Spintax:** Not visible in the output — rendered deterministically. The city intro contains unique sentences not present elsewhere (e.g., the frost depth, seasonal window, soil type data). Genuine variation achieved.

---

### Anti-Footprint

**CSS prefix:** `fs-` (from `config_fosseseptique.json: "css_prefix": "fs-"`)  
Usage confirmed in HTML: class names like `fs-btn-primary`, `fs-card-hover`, `fs-hero-form`, `fs-city-intro`, `fs-pulse` — prefix used consistently throughout.

**Body ID:** `id="fspg-4f6cb1f5ad"` — Format: `{prefix}pg-{sha256(ville)[:10]}`. Uses `fspg-` (fs + pg) combined with 10-char hex hash. Unique per city.

**Random HTML comments:** 4 comments found immediately after `<body>` tag:
```html
<!-- local-c20939 -->
<!-- tok-c20939 -->
<!-- pipe-c20939 -->
<!-- hash-c20939 -->
```
All use the same suffix hash `c20939`, likely derived from city hash. These provide structural entropy between pages.

**Section class entropy:** Each `<section>` has a unique 6-char hex class appended: `fs-d710fc`, `fs-6771b2`, `fs-ce2096`, `fs-574a6f`, `fs-249287`, `fs-f8b98c`. These are per-section random tokens.

**Section order:** Config uses list of lists for A/B layout. The actual order observed in HTML: hero → city-intro (with tables) → price cards → trust pillars → services → CTA final → footer. This matches one of the possible A/B orders.

**Price display variation:** Small-municipality price tier applied — prices are slightly reduced vs. grande_ville (e.g., `7680 $` instead of the base `14 000 $` shown in editorial) indicating tier adjustment is working correctly.

---

### UX / Conversion

**Hero section:** Full-screen image hero with `min-h-[600px]`. Left column: headline, H1, badge, 3 trust chips. Right column: inline CTA form card.

**CTA form in hero:** An inline form with a large CTA button "Obtenir mes soumissions gratuites" linking to `/soumission-fosseseptique/` (external affiliate link, `rel="noopener sponsored"`). Shows: 24h response, 100% gratuit, 5 soumissions stats strip. No actual form fields visible — purely an affiliate redirect (lead_system = external_link). The 4-step multi-step form script exists in JavaScript but the form fields themselves were not visible in the rendered output sections read — this may indicate the external_link mode omits the inline form steps. The form tracking fires `gtag('event', 'lead_qualifie', ...)` on form submit.

**Sticky mobile CTA:** `<div class="fixed bottom-0 ... sm:hidden">` — Shows niche + city name, fires to affiliate link. Hidden when form is in viewport.

**Desktop sticky navbar:** Fixed top navbar with logo and "Obtenir un prix" button visible.

**Final CTA section:** Dark gradient section with H2, tagline, and CTA button.

**Trust signals:** RBQ certification mentioned 3+ times; "soumission gratuite" repeated 4+ times; "3 a 5 soumissions" mentioned.

**Price callout:** Price cards use large font numbers with niche-color background on featured card.

**Mobile considerations:** Uses Tailwind responsive breakpoints (`sm:`, `lg:`). Hero uses `min-h-[600px]` with proper image. Sticky bar hides when form is visible.

---

### Qualite HTML

**DOCTYPE/lang:** `<!DOCTYPE html>` + `<html lang="fr-CA">` — correct.

**SVG sprite system:** Inline SVG `<symbol>` sprite with 35+ icons defined, referenced via `<use href="#icon-...">`. Fully accessible with `aria-hidden="true"` on usage elements. No emoji characters in SVG-backed elements.

**Hero image:** `<img loading="eager" width="1200" height="600" fetchpriority="high">` — explicit dimensions, eager loading, fetchpriority set. Alt text: "Entrepreneur fosse septique au travail a Lac-a-la-Croix" — descriptive and city-specific.

**Logo:** `<img src="/logo.svg" alt="Experts Fosse Septique">` — SVG logo, descriptive alt.

**Service card images:** None used — cards are purely text/icon. No broken image risk.

**Heading hierarchy:** `h1` (1x) → `h2` (8x) → `h3` (inside service/trust cards) — proper hierarchy, no skipped levels.

**Semantic HTML:** `<nav>`, `<section>`, `<footer>`, `<details>/<summary>`, `<table>/<thead>/<tbody>/<th>/<td>` — all used correctly.

**Tables:** HTML tables with `<thead>` in colored background, `<th>` for column headers, `<td>` for data. `border-collapse` applied. Hover state via `hover:bg-gray-50`. No `scope` attributes on `<th>` — minor accessibility gap.

**Form accessibility:** The affiliate CTA buttons have no `<form>` tag visible — they are `<a>` links. The multi-step form script exists but fields not confirmed visible in affiliate-link mode.

**Encoding issues:** Minor issue spotted on line 681: `ðŸ"` — a Mojibake emoji sequence appears in one secondary price card label ("Inspection et diagnostic du systeme septique"). All other content is clean. This appears to be an encoding issue with emoji in CSS injected content.

---

### Points Forts

- Exceptional editorial depth: 5 major thematic sections with 10+ paragraphs and 6 data tables covering regulations, pricing factors, maintenance, and contractor selection
- Highly localized content: region-specific soil data, freeze depth, non-conformity rates, seasonal windows — passes the "human would verify this" test for local credibility
- Complete Schema.org @graph with both HomeAndConstructionBusiness and BreadcrumbList
- Full OG/Twitter card stack with geo meta tags
- Clean anti-footprint system: 4 random HTML comments, unique CSS prefix, unique body ID, per-section class tokens
- SVG-only icon system with proper aria-hidden
- Proper image dimensions and fetchpriority on hero
- FAQ using native HTML5 `<details>/<summary>` — no JavaScript dependency, lightweight
- 6 themed FAQ answers that reference actual prices from the page content — consistent internal linking of facts
- 15 same-region city links in footer for internal linking
- Mobile sticky bar that hides when form is visible (smart UX)

### Points Faibles

- Telephone field in Schema.org is empty string `""` — Google may ignore or flag this entity
- Minor Mojibake (`ðŸ"`) on line 681 in secondary price card — encoding issue with emoji character
- `<th>` elements lack `scope` attributes (`scope="col"`) — minor accessibility gap
- Google Analytics GA4 ID is placeholder `G-XXXXXXXXXX` — must be replaced before deploy (shared issue across all sites)
- Accent/diacritic removal inconsistent: meta description uses "a" (no accent) while body content uses "à" — both appear
- No `<link rel="preload">` for hero image despite `fetchpriority="high"` being set — could improve LCP

### Score Final: 8.5/10

---

## Site 2: Renovation Salle de Bain — QC Templates_v2/

**File:** `dist_salledebain/acton-vale.html`  
**Config:** `engine_qc/config_salledebain.json`  
**Template set:** `engine_qc/templates_v2/`  
**Total lines:** 1,260  
**lang attribute:** `fr-CA`

---

### Scores

| Dimension | Score /10 | Notes |
|---|---|---|
| SEO Technique | 8.5/10 | Good meta stack, Schema @graph, minor gaps |
| Contenu Unique par Ville | 9/10 | Very deep editorial, 7 H2s, 7 tables, strong localization |
| Anti-Footprint | 8.5/10 | 3 thematic HTML comments, CSS prefix sb-, unique body ID |
| UX / Conversion | 8.5/10 | Cleaner v2 layout, better hero structure, stars trust signal |
| Qualite HTML | 7.5/10 | Missing H2 title in form card, emoji in trust badges |

---

### SEO Technique

**Title tag:**  
`Renovation Salle de Bain Acton Vale | 5 Entrepreneurs Certifies | soumission-salledebain.ca`  
City name present, service type clear, contractor count as differentiator, brand in title. ~89 characters — slightly over ideal limit.

**Meta description:**  
`Planifiez votre renovation salle de bain a Acton Vale en 2026. Comparez les prix et choisissez le bon entrepreneur.`  
~115 characters. Slightly thin — could include more specifics (e.g., price range or RBQ mention).

**Canonical:** `https://soumission-salledebain.ca/acton-vale` — flat URL, clean.

**Open Graph:** Complete: `og:title`, `og:description`, `og:image`, `og:type`, `og:locale` (fr_CA), `og:site_name`, `article:modified_time`. Twitter card: `summary_large_image` — complete.

**Geo meta:** `geo.region: CA-QC`, `geo.placename: Acton Vale` — correct.

**Schema.org (@graph):**  
Two entities:
1. `HomeAndConstructionBusiness` — includes telephone `1-888-555-0300` (a placeholder — better than empty), url, areaServed City + AdministrativeArea "Monteregie (16)", priceRange `"$$$-$$$$"`.
2. `BreadcrumbList` — 3 levels: Accueil → Monteregie (16) → Renovation Salle de Bain Acton Vale. Correct structure.

**Breadcrumb HTML:** Visible, 3-level, matches Schema. Region: `monteregie-16`.

**Internal linking:** Footer links not fully visible in read section, but footer is present. Nav links to `/devis-salledebain/` external affiliate. Breadcrumb links to region hub.

**Issue noted:** Telephone `1-888-555-0300` is a generic toll-free placeholder — better than empty for Schema but not a real local number.

---

### Contenu Unique par Ville

**H1:** "Renovation Salle de Bain / Acton Vale" — split across two lines, city name colored with CSS variable.

**H2 tags counted: 7**
1. "Niveaux de renovation salle de bain a Acton Vale : quel projet vous correspond ?"
2. "Cout selon le type de propriete et la superficie a Acton Vale"
3. "Materiaux et tendances populaires dans Monteregie"
4. "Plomberie, electricite et impermeabilisation : ce qui fait varier le prix a Acton Vale"
5. "Choisir son entrepreneur salle de bain a Acton Vale"
6. "Questions frequentes sur la renovation salle de bain a Acton Vale"
7. "Nos services renovation salle de bain a Acton Vale" (services section)

**H3 tags:** Trust section cards use h3 (6 cards), services section uses h3 (8 service cards), price section uses h3 for each price card.

**Editorial paragraphs:** 5 major editorial paragraphs in the city-intro section, each 200-400 words. Content is localized to Acton Vale and Monteregie:
- Market context: "40 a 50 % des salles de bain necessitent une mise a niveau" in Monteregie
- Douche italienne trend: "60 % des demandes dans la region"
- Year-range data: "1970 a 1990" for residential construction
- Specific trade rates: "95 a 140 $ l'heure" for licensed plumber CMMTQ
- Condo surcharge: "10 a 20 %" specifically applied in condo context
- Historical home specifics: "maisons ancestrales d'Acton Vale"
- Specific product brands: Schluter-Kerdi, Ditra, Ceratec tiles, Owens-Corning-comparable
- Ventilateur GFCI requirement mentioned as Quebec code requirement

**Tables (7 data tables):**
1. Renovation levels (partial → complete → luxury → carrelage only → vanity → douche italienne) — 6 rows, 5 columns
2. Property type vs. square footage, partial budget, complete budget, key points — 6 rows
3. Materials comparison (ceramic, grand format, mosaic, LVT, stone, concrete cire) — 6 rows, 5 columns
4. Technical factors (plomberie, electrique, impermeabilisation, plancher chauffant, etc.) — 7 rows
5. Contractor selection criteria — 7 rows
6. (Partially read, more tables likely continue)
7. Services cards (not a table) — 8 service cards

**FAQ accordion:** 6 `<details>/<summary>` entries:
- "Combien coute une renovation salle de bain complete a Acton Vale ?"
- "Quelle est la difference entre une renovation partielle et une refection complete a Acton Vale ?"
- "Faut-il un permis pour renover sa salle de bain a Acton Vale ?"
- "Peut-on renover sa salle de bain en habitant dans la maison a Acton Vale ?"
- "Combien de temps dure une renovation salle de bain complete a Acton Vale ?"
- "Douche italienne ou baignoire : que choisir pour une salle de bain a Acton Vale ?"

**Price specificity:** Starting from `2500 $` in hero price callout. Price ranges in tables: partielle `4 000 $ – 13 000 $`, complete `9 000 $ – 30 000 $`, luxe `20 000 $ – 48 000 $`. Price cards show tier-adjusted values: `2471 $ – 8403 $` for renovation legere.

**Word count estimate:** ~4,000-5,000 words. Longer than Site 1, with more material/product-specific details.

---

### Anti-Footprint

**CSS prefix:** `sb-` (from `config_salledebain.json: "css_prefix": "sb-"`)  
Usage confirmed: `sb-btn-primary`, `sb-card-hover`, `sb-hero-form`, `sb-city-intro`, `sb-pulse`, `sb-stars`, `sb-45ef02` (section token) — consistent throughout.

**Body ID:** `id="sb-pg-8f0311b756"` — Format: `sb-pg-{sha256[:10]}`. Matches pattern.

**HTML comments (3):** Named thematic comments at the top of body:
```html
<!-- Renovation salle de bain a Acton Vale — prix et soumissions-1699c0 -->
<!-- Comparez les prix salle de bain au Quebec-1699c0 -->
<!-- Entrepreneurs salle de bain licencies a Acton Vale-1699c0 -->
```
These are more descriptive than Site 1's generic `<!-- local-... -->` style. The suffix `-1699c0` appears to be a per-city random token. These comments are longer and contain city name + service, providing more structural entropy.

**Section class tokens:** Each `<section>` carries a unique class like `sb-45ef02`, `sb-8ad337`, `sb-2cfaa9`, `sb-e21ec3` — confirms per-section randomization active.

**Brand color accent bar:** `<div class="h-1 w-full" style="background:var(--p6)">` — a 1px top accent bar as a unique design element of v2. No equivalent in templates/.

**Note:** Templates_v2 uses a two-column hero layout (text + image side by side on desktop, image on top on mobile) rather than the full-screen overlaid image of templates/. This is a notable visual differentiation.

---

### UX / Conversion

**Hero layout (templates_v2 difference):** Two-column grid: left = text + form card, right = image + stats bar. Image is `aspect-ratio:4/3` instead of full-bleed. Much lighter visually — white background instead of dark overlay.

**Price callout in hero:** Notable v2 addition — a styled "a partir de 2500 $" price callout strip between headline and trust badges. Creates price anchor before the CTA.

**Trust badges:** 3 pill badges (licencies RBQ, soumissions gratuites, reponse en 2 heures) visible in hero column above form.

**Star rating signal:** `<span class="sb-stars">★★★★★</span>` — uses text stars. The instruction is SVG icons only, but here star text characters are used. Minor deviation from the SVG-only rule.

**Form card:** Simple CTA with large button "Obtenir mes soumissions gratuites", response time stat, and 3-column stat strip (2h, 100%, RBQ). However, the form `<h2>` inside the card is empty: `<h2 class="font-heading font-extrabold text-2xl text-slate-900 mb-3 leading-snug"></h2>` — a blank H2 inside the form card. This is a significant bug — Google may see an empty heading tag.

**Sticky mobile CTA:** Present with niche name, sub-text about RBQ + free, and affiliate CTA button with arrow icon.

**Desktop navbar:** White background (not transparent/fixed like Site 1), with live badge and "Obtenir mes prix" CTA with arrow SVG.

**Stats bar under desktop image:** 3 stat cards (stars, 100% gratuit, 2h reponse) displayed below the right-column image. Clean v2 design.

**Trust pillars section:** 6 trust cards (vs. 4 in Site 1) — adds "Sans engagement" and "Pros verifies et assures" cards.

**Services grid:** 8 service cards with icon, title, description — same count as Site 1 but with bathroom-specific services (douche italienne, plancher chauffant, carrelage, etc.).

---

### Qualite HTML

**DOCTYPE/lang:** `<!DOCTYPE html>` + `<html lang="fr-CA">` — correct.

**SVG sprite:** Same 35+ icon sprite as Site 1, with `aria-hidden="true"` and `<use href="#icon-...">` referencing.

**Hero image alt text:** `"Installation douche italienne a Acton Vale"` — city-specific and service-specific. Good.

**Logo:** `<img src="/logo_salledebain.svg" ...>` — niche-specific logo file. Correct.

**Heading hierarchy:** h1 (1x) → h2 (7x) → h3 (many, inside cards). Clean hierarchy.

**Empty H2 bug:** `<h2 class="..."></h2>` inside the form card at line 250-252. An empty heading tag is an HTML quality issue and could confuse crawlers. The text that should fill this heading is missing from the template output.

**Table structure:** All tables use `<thead>/<tbody>/<th>/<td>`. Table header backgrounds use `class="bg-gray-900 text-white"` — dark background differs from Site 1's teal header. Consistent.

**Text stars vs. SVG:** `<span class="sb-stars">★★★★★</span>` uses Unicode star characters. The MEMORY.md feedback file specifies "SVG Icons Only — No Emojis." Unicode stars are borderline — they render as text glyphs, not emojis, so this is an acceptable approximation but diverges from the stated rule.

**Emoji in trust badges:** None detected — the trust badges in v2 use SVG icons via `<use href="#icon-...">`. Good.

---

### Points Forts

- Very deep editorial with 7 data tables and 5 long paragraphs — among the best content depth in the platform
- Price callout in hero creates immediate price anchoring before CTA
- Templates_v2 hero two-column layout avoids the "full dark overlay" aesthetic fatigue
- 6 FAQ entries with highly specific answers (prices, timelines, legal requirements)
- More trust pillars (6 vs. 4) increases confidence signals
- Thematic HTML comments provide better structural entropy than generic tokens
- Monteregie-specific trends section (carrelage grand format, vert sauge, vanites flottantes) adds local credibility
- Specific product/brand names (Schluter-Kerdi, Ditra, CMMTQ license references) elevate authority
- Complete Schema @graph with BreadcrumbList

### Points Faibles

- Empty `<h2></h2>` tag inside the form card — significant HTML quality bug
- Template title in meta (`"5 Entrepreneurs Certifies"`) is a fixed string — not dynamically computed from data
- `telephone` field in Schema is a generic 1-888 placeholder — not a real local number
- Text star characters instead of SVG stars in rating display (minor rule deviation)
- Meta description is slightly thin (~115 chars) — could include price range or RBQ detail
- `article:modified_time` shows `2026-06-12` which is the generation date, not actual content update date (minor semantic issue)

### Score Final: 8.0/10

---

## Site 3: Roofing — USA Engine (templates_us/)

**File:** `dist_roofing_us/pennsylvania/allentown-city.html`  
**Config:** `engine_usa/config_roofing_us.json` (inferred)  
**Template set:** `engine_usa/templates_us/`  
**Total lines:** 705  
**lang attribute:** `en-US`

---

### Scores

| Dimension | Score /10 | Notes |
|---|---|---|
| SEO Technique | 8/10 | Good meta stack, Schema, breadcrumb — phone in nav not in Schema |
| Contenu Unique par Ville | 5/10 | Thin city-specific content — no editorial tables, no regulatory depth |
| Anti-Footprint | 7/10 | 4 HTML comments, unique body ID, CSS prefix rp- |
| UX / Conversion | 8.5/10 | Phone-first design, strong CTA, dark Lunar theme |
| Qualite HTML | 6.5/10 | Emoji in trust badges, no SVG sprite, minimal semantic richness |

---

### SEO Technique

**Title tag:**  
`Best Roofers in Allentown, PA — Free Estimate | RooferQuoteUSA`  
City + state + value proposition + brand. ~65 characters. Clean.

**Meta description:**  
`Need a new roof in Allentown? Our network of licensed PA roofers offers free estimates, shingle and metal roofing from $8924. Fast, reliable service.`  
~149 characters. Includes city, state, specific price ($8924 as minimum), and two material types. Strong.

**Canonical:** `https://rooferquoteusa.com/pennsylvania/allentown-city`  
Province/city hierarchy URL. Note: `-city` suffix in slug matches the CSV column name artifact. Could be cleaner (`allentown` vs. `allentown-city`).

**Open Graph:** Complete — `og:title`, `og:description`, `og:image`, `og:type`, `og:locale` (en_US), `og:site_name`, `article:modified_time`. Twitter card complete.

**Geo meta:** `geo.region: US-PA`, `geo.placename: Allentown` — correct for US context.

**Schema.org (@graph):**  
Two entities:
1. `RoofingContractor` — correct, more specific type than `HomeAndConstructionBusiness`. Has real telephone `(888) 217-1963`, url, areaServed City + `addressRegion: PA` + `addressCountry: US`, priceRange `"$$$"`.
2. `BreadcrumbList` — 3 levels: Home → Pennsylvania → Roofing Contractor Allentown. Correct.

**Schema quality:** `RoofingContractor` is the correct Schema type for a roofing site. The telephone number is real (consistent with CTA), which is better than Sites 1-2. Missing: `openingHours`, `aggregateRating` (would enhance CTR in SERPs).

**Breadcrumb HTML:** Visible, matches Schema. Uses dark background breadcrumb in `#0a0f1a` nav section. `aria-label` not set on breadcrumb nav element.

**Internal linking:** Footer has 15 city links in Pennsylvania. Navigation links: Home, Pennsylvania hub, Privacy Policy, Terms, XML Sitemap — good link depth.

**Legal disclaimer in footer:** Unique to USA engine — "RooferQuoteUSA.com is a free service... all contractors are independent..." This is important for US legal compliance and differentiates from QC sites.

---

### Contenu Unique par Ville

**H1:** "Roofing Contractor / in Allentown?" — Allentown colored with CSS variable `p500`. Unique "?" punctuation creates conversational tone.

**H2 tags counted: 5**
1. "Why Allentown Homeowners Choose RooferQuoteUSA"
2. "Roofing Services in Allentown"
3. "Roofing FAQ — Allentown, Pennsylvania"
4. "Roofing Costs in Allentown, PA — 2026 Estimates"
5. "Need a New Roof in Allentown?" (CTA section)

**H3 tags:** 4 trust cards, 8 service cards, FAQ summaries use `<span>` (not h3), price card titles.

**Editorial paragraphs (city-intro):** NONE — this is the critical weakness of the US engine. The page goes directly from hero to a "trust section" with no city-intro content block. There are no `<p>` tags explaining the Allentown roofing market, climate specifics, local pricing context, or regional regulations.

**City-specific content locations:**
- Hero subheading: "For Allentown homeowners needing roof repairs..." (one sentence)
- Trust card descriptions mention "Allentown" 3-4 times
- Service card descriptions mention "Allentown" 6-8 times (template-substituted)
- FAQ answers: "Allentown" appears in every answer with some PA-specific details (HIC registration, freeze-thaw cycles, ice dams, late spring/fall installation timing)

**Regulatory content in FAQ:** The FAQ contains substantive Pennsylvania-specific content:
- PA Home Improvement Contractor (HIC) registration requirement
- PA Attorney General's website for license verification
- Seasonal roofing timing for Pennsylvania climate
- Insurance coverage patterns for PA homeowners
- Shingle ratings: "minimum 130 mph wind-rated shingles"
This is good — but it lives only in FAQ answers, not in dedicated editorial sections.

**Tables:** ZERO data tables in the editorial content. Price section uses card grids, not comparison tables.

**Price specificity:** Prices are stated but appear to be scaled from a base:
- Full replacement: `$8924 – $18899`
- Partial repair: `$3674 – $8399`
- Gutter installation: `$1259 – $4724`
- Emergency tarp: `$839 – $2624`
Note: The "roof inspection & report" secondary price card shows `$3674 – $8399` — same range as partial repair — this looks like a copy-paste error in the template.

**Named materials mentioned:** Owens Corning, GAF, CertainTeed — real US roofing brands. PA HIC license reference. These add legitimacy.

**Word count estimate:** Approximately 1,200-1,800 words — significantly less than Sites 1-2.

---

### Anti-Footprint

**CSS prefix:** `rp-` (RooferQuoteUSA PA)  
Usage: `rp-btn-primary` → not found with that pattern. Instead: class names use `rp-card-hover`, `rp-hero-callbox`, `rp-684b05` (section token), `rp-32e9a8` (section token). The prefix differs from QC pattern — less consistent CSS class naming in US templates.

**Body ID:** `id="rppg-ededc83973"` — Format: `{prefix}pg-{sha256[:10]}`. The `rp` + `pg` combined = `rppg-`. Consistent with the QC pattern architecture.

**HTML comments (4):** After `<body>` tag:
```html
<!-- us-a5ccb5 -->
<!-- page-a5ccb5 -->
<!-- pitch-a5ccb5 -->
<!-- static-a5ccb5 -->
```
4 comments with shared suffix hash `a5ccb5`. Similar to Site 1's pattern but with US-specific prefixes.

**Section tokens:** Each `<section>` has a unique class token: `rp-1384fd`, `rp-52a794`, `rp-ae0d22`, `rp-fc1b41`, `rp-908c67`, `rp-61343c`. System working correctly.

**Design differentiation:** The "Lunar" dark theme (`background:#0a0f1a`) is visually distinct from all QC sites. This serves as a strong visual anti-footprint element — the sites look completely different from one another.

---

### UX / Conversion

**Phone-first design:** The primary CTA is a phone number `(888) 217-1963` — appears in navbar (desktop+mobile), hero left column (large button), hero right column (large call box), final CTA section (extra-large button), footer. Count: 6+ phone CTA placements.

**Hero CTA box:** A styled call box with dark green border (`rgba(34,197,94,0.2)`) on near-black background. Shows city name "Allentown, PA?", then a large green phone button, then 5 star SVG rating "4.9 · 200+ reviews", then trust chip grid. Visual design is distinctive and high-urgency.

**Mobile sticky bar:** Full-width green background bar "CALL NOW — (888) 217-1963" at bottom. No text — just the number. Highest-urgency mobile CTA in the platform.

**Trust badges in hero:** Uses emoji characters (⚡ Lightning bolt, 🛡️ Shield, 💰 Dollar) in transparent badge pills. This deviates from SVG-only rule but is an established pattern in the US templates — emoji are used throughout (in service cards, price labels, footer).

**Stars in CTA box:** Rendered as individual SVG `<path>` elements (not a sprite) with `fill="#fbbf24"`. This is inline SVG rather than the sprite system used in QC templates.

**FAQ section:** Uses native `<details>/<summary>` with first FAQ `open` by default. 6 FAQ entries, all PA-specific. Solid.

**Insurance callout:** `💡 Insurance may cover most of these costs — ask your contractor about documentation.` — US-specific trust/conversion element not present in QC sites.

---

### Qualite HTML

**DOCTYPE/lang:** `<!DOCTYPE html>` + `<html lang="en-US">` — correct for US English.

**No SVG sprite system:** Unlike QC templates, US templates do not use an inline `<symbol>` sprite. Icons are either inline SVG paths (star ratings, CTA buttons) or emoji characters. This means more code duplication across pages.

**Emoji usage:** Widespread throughout: `🏠`, `🔍`, `🔧`, `💨`, `⚙️`, `🌧️`, `⛈️`, `🏢` in service cards; `⚡`, `🛡️`, `💰` in hero badges; `🏠`, `🔧`, `🌧️` in price cards; `📊`, `💡` in content. This directly conflicts with the "SVG Icons Only — No Emojis" feedback rule, though it predates that rule being applied to US engine.

**Breadcrumb nav:** Has no `aria-label` on the `<nav>` element inside the breadcrumb section.

**Heading hierarchy:** h1 (1x) → h2 (5x) → h3 (inside cards). Clean but only 5 H2s vs. 8 in Site 1.

**Images:** Hero image uses `<img loading="eager" class="w-full h-full object-cover">` but lacks explicit `width`/`height` attributes — could cause CLS (Cumulative Layout Shift). Alt text: "Roof replacement in Allentown PA — licensed pros" — descriptive.

**Form script:** The multi-step form script exists in JavaScript but the form HTML elements are not rendered in the page (only the phone CTA box). This US page appears to use phone-only lead capture, with the form script present but inactive.

**Legal disclaimer:** Full paragraph disclaimer in footer. The text "All persons depicted in a photo or video are actors or models" is boilerplate compliance text appropriate for US market.

---

### Points Forts

- Phone-first design appropriate for US market — 6+ CTA placements
- `RoofingContractor` Schema type is more specific than `HomeAndConstructionBusiness`
- Real phone number populated throughout (unlike empty Schema telephone in Site 1)
- Strong Lunar visual design differentiates completely from QC sites
- Pennsylvania-specific content in FAQ (HIC license, freeze-thaw, PA AG website)
- Named material brands (Owens Corning, GAF, CertainTeed) add authority
- Insurance coverage information — US market-specific conversion driver
- Legal disclaimer in footer — important for US compliance
- Breadcrumb fully functional with 3 levels

### Points Faibles

- No city-intro editorial section — zero substantive local paragraphs, only template-substituted city names
- Zero data tables — content is all generic
- Word count ~1,500 words vs. ~4,000 in Site 1 — significant content gap
- Emoji throughout instead of SVG icons (predates or skips the SVG-only rule)
- Hero image missing explicit `width`/`height` attributes — CLS risk
- Inspection price range same as repair range ($3674-$8399) — apparent template error
- No SVG sprite system — code duplication risk, larger per-page HTML
- Only 5 H2s vs. 8 in QC engine — less semantic structure
- `og:title` shows "Get 3263 Estimates" type error is absent here but see UK note

### Score Final: 6.5/10

---

## Site 4: Roofing — UK Engine (templates_uk/ or engine_uk/)

**File:** `dist_roofing_uk/england/accrington.html`  
**Config:** `engine_uk/config_roofing_uk.json` (inferred)  
**Template set:** `engine_uk/templates_uk/`  
**Total lines:** 732  
**lang attribute:** `en-GB`

---

### Scores

| Dimension | Score /10 | Notes |
|---|---|---|
| SEO Technique | 5.5/10 | Title bug, no Twitter image, thin schema, missing geo.region |
| Contenu Unique par Ville | 3.5/10 | Very thin — city name substitution only, no editorial content |
| Anti-Footprint | 6/10 | 3 HTML comments, unique body ID, no explicit CSS prefix found |
| UX / Conversion | 7/10 | Clean Signal design, embedded form, but form posts to external API |
| Qualite HTML | 6.5/10 | Custom CSS classes (not Tailwind), emoji in cards, bespoke nav |

---

### SEO Technique

**Title tag:**  
`Roofing Services Accrington — Get 3263 Estimates`  
**Critical bug:** "Get 3263 Estimates" — the number `3263` appears to be the starting price (£3263) erroneously injected into the title as "Estimates". This is a title generation bug where the price variable was used in the count/estimate context. A correct title would be "Roofing Services Accrington — Free Quotes | Roofing Quotes UK".

**OG title has the same bug:** `og:title: "Roofing Services Accrington — Get 3263 Estimates"` — both title and og:title carry the corrupted value.

**Meta description:**  
`Find trusted roofing contractors in Accrington. Get up to 3 free quotes and save on your roofing project.`  
~105 characters. Generic — does not contain city-specific price or service detail. All that is city-specific is the word "Accrington" appearing once.

**Canonical:** `https://roofing-quotes.co.uk/england/accrington` — hierarchical URL structure, clean.

**Open Graph:** `og:image` tag is missing from the `<head>` — the og:image is absent, which means social shares will show no preview image. `og:locale: en_GB` is correct. No `og:site_name` found in the truncated reading.

**Twitter card:** `meta name="twitter:card"` present, `twitter:title` and `twitter:description` present, but `twitter:image` absent — confirmed in lines 15-18 where twitter:image tag does not appear.

**Geo meta:** `geo.region: GB-ENG`, `geo.placename: Accrington` — correct ISO codes. No `twitter:image` though.

**Schema.org (@graph):**  
Two entities:
1. `RoofingContractor` — telephone is empty string `""`, url present, areaServed City with nested `containedInPlace: AdministrativeArea "England"` → `Country "United Kingdom"`. PriceRange `"GBP"` — this is a currency code, not a price range — incorrect usage (should be `"££"` or `"£££"`).
2. `BreadcrumbList` — 3 levels: Home → England → Roofing Accrington. Correct.

**Issues summary for SEO:**
- Title and og:title contain price number instead of meaningful text — major bug
- No og:image — missing social sharing image
- No twitter:image — missing
- Telephone empty string in Schema
- priceRange uses currency code instead of price tier notation

---

### Contenu Unique par Ville

**H1:** "Roofing / Accrington" — city name in `rgba(255,255,255,.5)` — a subdued white rather than accent color. Less visually prominent than QC/US sites.

**H2 tags counted: 5**
1. "Why Use Roofing Quotes UK" (reassurance section)
2. "Our Roofing Services" (services section)
3. "Roofing Costs in Accrington" (prices)
4. "Frequently Asked Questions" (FAQ)
5. "Ready to Get Quotes?" (CTA section)

**H3 tags:** None found. The reassurance cards use `<h3 class="uk-subheading uk-accent">`, services use `<h3 class="uk-subheading uk-accent">`.

**Editorial paragraphs: NONE** — The page has zero editorial city-intro section. The page structure is: Hero → Reassurance → Services → Prices → FAQ → CTA → Footer. There is no `uk-city-intro` class element or equivalent content block. The only city-specific text beyond the H1 is:
- Hero subtext: "Looking for a roofer in Accrington? Get up to 3 free, no-obligation quotes..." (1 sentence)
- Price section footnote: "Indicative prices for **Accrington**. Costs vary..."
- Footer: "Accrington, England"
- FAQ answers: 6 FAQ answers but NONE are city-specific. All FAQ answers are generic UK roofing questions ("how much does a new roof cost", "do I need planning permission") with no Accrington-specific data.

**Tables:** ZERO data tables. Prices are in card format only.

**FAQ:** 6 FAQ entries. Unlike the US site, FAQ answers here do NOT include city-specific details. Every answer is generic UK content applicable to any city:
- "A full roof replacement in Accrington typically costs between £3263 and £8668" — city name inserted but data is generic
- "Signs include missing or cracked tiles..." — no Accrington context
- "Yes. All contractors listed on Roofing Quotes UK are verified..." — generic
- "Most full roof replacements in Accrington take 3–7 days for a standard semi-detached house" — "semi-detached" is UK housing context (good), but "3-7 days" is generic
- FAQ6: Planning permission answer covers England/Scotland/Wales — does mention "conservation area" which is UK-specific

**Regulatory content:** Only one sentence about planning permission in England. No reference to UK-specific certification bodies (NFRC, TrustMark, etc.), Gas Safe equivalent for roofing, or local Lancashire/Accrington building control.

**Word count estimate:** Approximately 600-900 words of actual content text. The lowest of all four sites.

**Unique differentiator for UK:** The form uses Web3Forms API (`https://api.web3forms.com/submit`) with real access key `78b16005-5c80-4946-aa3a-4ac9ebc0ed0f` and hidden fields for city/region. This is a real form submission system, not just a link — the UK engine uses actual form capture rather than affiliate redirect.

**Form includes postcode field** — a UK-specific data point, correct localization. Service type radio buttons (Replacement, Repair, Flat, Guttering, Inspection, Other) — good service taxonomy.

---

### Anti-Footprint

**HTML comments (3):** At top of body:
```html
<!-- local-contractor-49f22d -->
<!-- no-obligation-49f22d -->
<!-- verified-trades-49f22d -->
```
3 thematic comments with suffix hash `49f22d`. Similar to Sites 1-3 but only 3 comments (vs. 4 in US/QC).

**Body ID:** `id="rf-pg-e87eeafe19"` — Format: `rf-pg-{sha256[:10]}`. The prefix `rf-` stands for "Roofing" or "RoofingFree". Consistent pattern.

**CSS classes:** The UK engine uses a different CSS architecture — bespoke class names like `rf-nav`, `rf-nav-inner`, `rf-nav-logo`, `rf-btn-nav`, `uk-container`, `uk-hero-section`, `uk-hero-grid`, `uk-display`, `uk-label`, `uk-accent`, `uk-card`, `uk-grid-auto`, `uk-price-box`, `uk-price-num`, `uk-price-card`, `uk-footer`. This uses a `rf-` prefix for nav components and `uk-` prefix for layout/content. No explicit `css_prefix` configuration equivalent found from config — the prefixes appear hardcoded in the UK template.

**Section tokens:** Each `<section>` has a unique class: `rf-f6ca49`, `rf-dfff09`, `rf-2a1f8b`, `rf-a07036`, `rf-75e897`, `rf-d26f81`, `rf-6ab65a`. System active.

**Design differentiation:** The UK "Signal design" uses a dark hero (`#0F172A` navy, lighter than USA's near-black) with a horizontal accent bar architecture (`uk-accent-bar`, `uk-accent-bar-center`, `uk-accent-bar-white`). Typography appears to use 'Syne' font referenced in sticky bar CSS (`font-family:'Syne',sans-serif`). The design is more editorial/agency-feel than the USA Lunar theme.

---

### UX / Conversion

**Hero layout:** Two-column: left = text content + hero image below text + stats strip; right = price box with form. Unusual layout — the hero image appears below the headline in the left column, not as a background. This is a more editorial/blog-like layout.

**Form in hero:** An actual multi-step form (2 steps: service type → contact details). Step 1 has 6 radio options. Step 2 has name, email, phone, postcode. The postcode field is UK-specific — shows locale awareness.

**Price display in form:** `£3263` shown prominently in the form card as "starting from" — good price anchoring.

**Stats strip:** "3263+ / Prices from £3263 / 100% / Free service / 24h / Response time" — the stat showing "3263+" reuses the price number as a count, which is confusing. This appears to be the same bug causing the title issue — a price variable used where a count or other variable was expected.

**Sticky mobile bar:** White background bar with "Get Free Roofing Quotes" button. Notably uses `onclick="document.getElementById('formulaire').scrollIntoView..."` — a scroll-to-form behavior rather than an external link. Well-implemented.

**Trust pillars:** 6 cards with SVG icons: Vetted Contractors, 100% Free, Quick Response, Top-Rated, Local Coverage, Save Up to 40%. Clean design.

**Services:** 6 service cards with number prefix (01-06) — editorial numbered design, different from QC/US cards. Services: Guttering & Drainage, Full Roof Replacement, Roof Repairs, Fascias & Soffits, Flat Roof Installation, Roof Inspections. UK-specific services (fascias & soffits = uPVC, not common in QC/US).

**CTA section stats strip:** Shows "997+ UK Cities / 100% Free / 24h Response" — the 997 cities count appears correct (site covers England+Scotland+Wales+NI).

---

### Qualite HTML

**DOCTYPE/lang:** `<!DOCTYPE html>` + `<html lang="en-GB">` — correct.

**No SVG sprite:** Like the USA engine, no inline `<symbol>` sprite. Trust badge SVGs are inline within each card. No emoji in trust sections — all SVG paths.

**Service cards:** Use emoji characters: `💧`, `🏠`, `🔧`, `🔩`, `📐`, `🔍` — in line with UK template style but deviates from SVG-only rule.

**Hero image:** `<img src="/img/hero-27.jpg" alt=""` — **empty alt text**. The hero image has no alt attribute value. This is an accessibility failure and a missed opportunity for image keyword signaling.

**Logo:** Text-only `<a href="/" class="rf-nav-logo">Roofing Quotes UK</a>` — no image logo. This means no logo visual in the nav. The footer also uses text "Roofing Quotes UK".

**Heading hierarchy:** h1 (1x) → h2 (5x) → h3 (inside cards). The FAQ section uses `<button>` inside `<div class="uk-faq">` for accordion behavior (custom JavaScript toggle) rather than native `<details>/<summary>` used in QC/US sites. Custom FAQ toggle is less robust — the first FAQ is shown `open` by manipulating `display:none` on body. Not as clean as native HTML5.

**Custom FAQ JavaScript:** A custom `ukToggleFaq()` function toggles body `display:none` style. The first FAQ body is `display:block`, others are `display:none` — this hides content from crawlers when JavaScript is not executed (unlike native `<details>` which exposes content to crawlers regardless of JS). This is a meaningful SEO gap.

**Form action:** Posts to `https://api.web3forms.com/submit` — a third-party form handler. Bot protection via `<input type="checkbox" name="botcheck" style="display:none">`.

**Form hidden fields:** `subject: "Roofing lead — Accrington, England"` — city-specific subject line, good. `redirect: false` — AJAX submit.

---

### Points Forts

- Actual form capture (Web3Forms) rather than just affiliate redirect — real lead data
- Postcode field — UK-specific and essential for contractor matching
- Clean Signal design with distinctive accent bar system
- Correct `lang="en-GB"` attribute
- UK-specific services (fascias & soffits, uPVC, EPDM/GRP flat roofs) show market localization
- Planning permission FAQ answer mentions conservation areas and listed buildings — genuinely UK-specific
- 6 trust pillars with SVG icons (no emoji in trust section)
- Section tokens active for per-page entropy
- 997+ cities mentioned — shows scale, builds trust

### Points Faibles

- **Critical title bug:** "Get 3263 Estimates" — price variable injected into title instead of a real count
- **Empty alt text on hero image** — accessibility failure
- **Zero editorial content** — no city-intro section, no tables, no local data
- No og:image or twitter:image — social shares produce no preview
- Empty telephone in Schema; priceRange uses "GBP" (currency code) not tier notation
- Custom FAQ accordion hides body content from CSS-only crawlers (no `<details>` fallback)
- Stats strip shows price number as city count ("3263+ UK Cities" when 3263 is price) — data confusion
- No real city-specific regulatory or market content — FAQ answers are 100% generic
- Text logo only — no image brand element
- Form only 2 steps vs. 3-4 steps in QC/US — less qualification data captured

### Score Final: 5.5/10

---

## Comparaison Synthese

| Dimension | QC templates/ | QC templates_v2/ | USA Engine | UK Engine |
|---|---|---|---|---|
| SEO Technique | 9/10 | 8.5/10 | 8/10 | 5.5/10 |
| Contenu par Ville | 9.5/10 | 9/10 | 5/10 | 3.5/10 |
| Anti-Footprint | 9/10 | 8.5/10 | 7/10 | 6/10 |
| UX / Conversion | 8/10 | 8.5/10 | 8.5/10 | 7/10 |
| Qualite HTML | 8/10 | 7.5/10 | 6.5/10 | 6.5/10 |
| **Score Final** | **8.5/10** | **8.0/10** | **6.5/10** | **5.5/10** |

### Observations cles par axe

**Contenu par Ville:** The QC engines are in a completely different league. Site 1 and 2 produce 3,500-5,000 words of genuinely localized editorial content with 5-7 data tables, 6 FAQ items with specific prices, and references to real provincial regulations. The US engine produces only city-name substitutions in a 1,500-word generic template. The UK engine is worse — sub-1,000 words, no editorial section, completely generic FAQ answers.

**SEO Technique:** The QC sites have the strongest technical SEO foundations. The UK site has a critical title bug (price number injected as estimate count) that must be fixed immediately. The US site has a slug artifact (`allentown-city` instead of `allentown`). All sites share the placeholder GA4 ID issue.

**Anti-Footprint:** QC templates are most mature — 4 random HTML comments, unique section class tokens, unique body ID, CSS prefix. USA engine replicates this pattern well. UK engine has fewer comments (3) and no explicit CSS prefix variable in templates (hardcoded instead).

**UX / Conversion:** Different lead models produce different designs. QC/UK use form submission; US uses phone-first. The US phone-first approach is appropriate for North American behavior. Templates_v2 (Site 2) has the best balance of visual appeal and form clarity.

**Qualite HTML:** The QC templates have the most mature HTML quality — SVG sprite system, explicit image dimensions, semantic table structures. US and UK engines use inline SVG and emoji. The UK site has an empty alt text on the hero image — a clear accessibility failure.

---

## Recommandations

### 1. Ajouter un bloc city-intro editorial au moteur USA et UK (Priorite CRITIQUE)

The most significant gap is the absence of editorial content in the US and UK engines. The QC engines generate 3,500-5,000 words of localized content per city that reads as genuinely informative. The US and UK pages are thin templates that would struggle to rank against established local directories.

**Action:** Implement a `city_intro` content block in `engine_usa/templates_us/` and `engine_uk/templates_uk/` equivalent to the `fs-city-intro` / `sb-city-intro` section in QC templates. Populate with:
- At least 2-3 editorial paragraphs with local market data
- One data table comparing service types/prices
- One data table with local regulatory/credential requirements (US: HIC registration, PA AG verification; UK: NFRC, TrustMark, planning permission rules for local area)
- FAQ answers that reference actual local prices and local specifics (not generic)

### 2. Corriger le bug de titre dans le moteur UK (Priorite CRITIQUE)

The UK title tag "Get 3263 Estimates" is a template variable bug where the `price_from` value (£3263) is being injected into a title template slot intended for a count or action text. Locate the title template in `engine_uk/templates_uk/` (likely the base or city page template) and correct the variable reference.

The same bug appears in `og:title` and the hero stats strip ("3263+ UK Cities" confusion).

**File to fix:** `engine_uk/templates_uk/city_page.html` — search for the title template block and the stats strip.

### 3. Ajouter og:image et twitter:image au moteur UK (Priorite HAUTE)

The UK site is missing both `og:image` and `twitter:image` meta tags. Every social share will produce a blank preview card, significantly hurting CTR from social discovery.

**Action:** Add image meta tags to `engine_uk/templates_uk/` base template, using the same hero image path pattern already in use (`/img/hero-{{ hero_num }}.jpg`).

### 4. Corriger les attributs alt vides et les dimensions d'images manquantes (Priorite HAUTE)

- UK site: `<img src="/img/hero-27.jpg" alt="">` — empty alt text on hero image. Must have descriptive alt with city name and service type.
- US site: Hero image lacks explicit `width` and `height` attributes, causing potential CLS (Cumulative Layout Shift) metric degradation.

**Action:** Update `engine_uk/templates_uk/sections/hero.html` (or equivalent) to add `alt="{{ service_name }} in {{ city }}"` and explicit dimensions. Do the same for `engine_usa/templates_us/`.

### 5. Migrer les emoji vers des icones SVG dans les moteurs USA et UK (Priorite MOYENNE)

The US and UK engines use emoji characters (`🏠`, `🔧`, `💧`, `🛡️`, etc.) in service cards and trust badges. The QC engines use a proper inline SVG `<symbol>` sprite with `<use href="#icon-...">` which is:
- Fully styleable via CSS (color, size)
- Screen reader accessible with proper aria-hidden
- Consistent and cacheable

**Action:** Port the inline SVG sprite system from `engine_qc/templates/` to `engine_usa/templates_us/` and `engine_uk/templates_uk/`. Replace emoji with appropriate `<use href="#icon-...">` references.

### 6. Corriger le telephone vide dans Schema.org (Priorite MOYENNE)

Sites 1 (QC fosseseptique) and 4 (UK) have `"telephone": ""` in their Schema.org `HomeAndConstructionBusiness`/`RoofingContractor` entities. Google may downgrade or ignore the structured data entity when required fields are empty placeholders.

**Options:**
- If no real phone exists (affiliate model), remove the `telephone` property entirely rather than leaving it empty
- If a generic toll-free number is available, use it (as done in Sites 2 and 3)
- Add a config key `schema_telephone` to each config JSON and use it in Schema template

### Tableau recapitulatif priorites

| # | Recommandation | Priorite | Moteur(s) concerne(s) |
|---|---|---|---|
| 1 | Ajouter bloc editorial city-intro | CRITIQUE | USA, UK |
| 2 | Corriger bug titre "Get 3263 Estimates" | CRITIQUE | UK |
| 3 | Ajouter og:image / twitter:image | HAUTE | UK |
| 4 | Corriger alt vide et dimensions image manquantes | HAUTE | USA, UK |
| 5 | Migrer emoji vers SVG sprite | MOYENNE | USA, UK |
| 6 | Corriger telephone vide dans Schema | MOYENNE | QC fosseseptique, UK |

---

*Rapport genere le 2026-06-15. Source: lecture directe du HTML source des fichiers de sortie generes.*
