#!/usr/bin/env python3
"""
Fix two issues in all 8 QC V3 configs:
1. Move faq_templates from root → content.faq_templates
2. Add UTM params to affiliate.base_url (before # fragment)
"""
import json, os

BASE = os.path.join(os.path.dirname(__file__), '..', 'engine_qc')

# UTM params per config: utm_source=domain, utm_medium=organic, utm_campaign=niche
UTM = {
    'config_cloture.json':          ('soumission-cloture.ca',       'cloture'),
    'config_chauffage.json':         ('experts-chauffage-qc.ca',     'chauffage'),
    'config_beton.json':             ('prix-beton-qc.ca',            'beton'),
    'config_portes-fenetres.json':   ('soumission-fenetres.ca',      'portes-fenetres'),
    'config_agrandissement.json':    ('soumission-agrandissement.ca', 'agrandissement'),
    'config_ceramique.json':         ('experts-ceramique-qc.ca',     'ceramique'),
    'config_toiture-plate.json':     ('soumission-toiture-plate.ca', 'toiture-plate'),
    'config_nettoyage-conduits.json':('experts-conduits.ca',         'nettoyage-conduits'),
}

FAQS = {
    'config_cloture.json': [
        {'q': '{Combien coute|Quel est le prix d\'} une cloture en bois a {ville} ?',
         'a': 'Une cloture en bois a {ville} coute generalement entre {service1_min}$ et {service1_max}$ pour une installation complete. Le prix depend du type de bois (cedre, pin traite), de la hauteur (4 pi vs 6 pi) et de la longueur lineaire. Le cedre dure 20-25 ans sans traitement special.'},
        {'q': 'Faut-il un permis pour installer une cloture a {ville} ?',
         'a': 'Oui, la majorite des municipalites du Quebec exigent un permis pour les clotures depassant 1 metre (3 pi) en cour avant, ou 2 metres (6 pi) en cour arriere. A {ville}, le permis coute generalement entre 75$ et 200$. Nous nous occupons des demarches pour vous.'},
        {'q': 'Cloture en aluminium ou en vinyle — laquelle choisir ?',
         'a': 'L\'aluminium (entre {service2_min}$ et {service2_max}$) est ideal pour une apparence classique et une durabilite de 30+ ans. Le vinyle est sans entretien, resistant au gel et aux insectes, mais moins rigide. Pour une cloture decorative a {ville}, l\'aluminium reste le choix premium.'},
        {'q': 'Combien de temps prend l\'installation d\'une cloture ?',
         'a': 'Une cloture standard de 30 metres lineaires prend 1 a 2 jours d\'installation. Les delais peuvent varier selon les conditions du sol (roc, argile), le type de cloture choisi et la saison. Nous planifions les travaux apres verification des lignes de propriete.'},
        {'q': 'Quelle cloture resiste le mieux aux hivers du Quebec ?',
         'a': 'Le vinyle et l\'aluminium sont les plus resistants au gel, au sel de voirie et aux cycles de gel-degel typiques des hivers quebecois. Le bois traite sous pression reste populaire mais necessite une teinture aux 3-5 ans. Nos installers utilisent du beton pour les poteaux — profondeur minimale de 4 pi sous la ligne de gel.'},
        {'q': 'Quel est le cout d\'une cloture pour une grande cour a {ville} ?',
         'a': 'Pour une propriete typique de {ville} avec 60-80 metres de perimetre, prevoyez entre {service3_min}$ et {service3_max}$ en vinyle ou aluminium standard. Nous offrons des soumissions gratuites avec mesures precises pour eviter les surprises.'},
    ],
    'config_chauffage.json': [
        {'q': 'Combien coute le remplacement d\'une fournaise au Quebec ?',
         'a': 'Remplacer une fournaise au gaz naturel a {ville} coute entre {service1_min}$ et {service1_max}$ installation incluse, selon la capacite (BTU), l\'efficacite (AFUE 80% vs 96%) et la marque. Les modeles haute efficacite permettent d\'economiser jusqu\'a 30% sur la facture annuelle.'},
        {'q': 'Quand faut-il remplacer sa fournaise ?',
         'a': 'Une fournaise dure en moyenne 15-20 ans. Signes qu\'il faut la remplacer : factures de chauffage en hausse, reparations frequentes, bruit inhabituel ou distribution de chaleur irreguliere. Apres 15 ans, il est plus economique de remplacer que de reparer.'},
        {'q': 'Thermopompe ou fournaise — que choisir pour {ville} ?',
         'a': 'Une thermopompe double fonction (chauffage + climatisation) coute entre {service2_min}$ et {service2_max}$ installee, mais peut etre subventionnee jusqu\'a 2 500$ via Hydro-Quebec Renoclimat. Elle est ideale si vous avez la climatisation centrale. Pour les hivers tres froids de {ville}, combiner une thermopompe avec une fournaise electrique d\'appoint est optimal.'},
        {'q': 'Est-ce que je peux obtenir une subvention pour ma fournaise ?',
         'a': 'Oui. Le programme Renoclimat d\'Hydro-Quebec offre jusqu\'a 2 000$ pour le remplacement d\'une fournaise au mazout par un systeme propre. Les municipalites comme {ville} peuvent aussi avoir leurs propres programmes. Nos techniciens vous aident a remplir les formulaires.'},
        {'q': 'Combien coute une urgence de chauffage la nuit ?',
         'a': 'Un appel de service d\'urgence (panne de chauffage hors heures) coute generalement entre 150$ et 350$ pour le deplacement et le diagnostic, en plus des pieces. Pour eviter ce scenario, un contrat d\'entretien annuel (environ 120-180$/an) inclut souvent la priorite en cas de panne.'},
        {'q': 'Quelle est la difference entre entretien annuel et reparation de fournaise ?',
         'a': 'L\'entretien preventif annuel ({service3_min}$ a {service3_max}$) comprend le nettoyage de l\'echangeur de chaleur, le filtre, le bruleur et la verification du monoxyde de carbone. Une reparation corrective (piece brisee) est facturee separement. L\'entretien reduit les pannes de 70% selon les statistiques du secteur.'},
    ],
    'config_beton.json': [
        {'q': 'Combien coute une dalle de beton a {ville} ?',
         'a': 'Une dalle de beton standard (entree de garage, patio) coute entre {service1_min}$ et {service1_max}$ le pied carre a {ville}, incluant excavation, gravier compacte et finition lissee. Une entree typique de 400 pi2 revient a 4 000$-8 000$ selon l\'epaisseur (4 po vs 6 po) et l\'acces au chantier.'},
        {'q': 'Beton estampe ou dalle standard — quelle difference de prix ?',
         'a': 'Le beton estampe (motifs pierres, briques) coute entre {service2_min}$ et {service2_max}$ le pied carre, soit environ 2x le prix d\'une dalle ordinaire. La valeur ajoutee est esthetique — durabilite comparable. Une resurfaçage au beton estampe peut aussi donner un look neuf a une dalle existante.'},
        {'q': 'Est-ce qu\'il faut un permis pour une dalle de beton a {ville} ?',
         'a': 'Les dalles de patio et entrees de garage de moins de 50 cm de hauteur ne necessitent generalement pas de permis. Les fondations et murs de soutenement en beton necessitent toujours un permis de construction. Nous verifions les reglements de {ville} avant de commencer.'},
        {'q': 'Comment reparer des fissures dans mon beton ?',
         'a': 'Les fissures de moins de 3 mm (fissures de retrait normales) peuvent etre scellees avec un produit d\'injection epoxy ({service3_min}$ a {service3_max}$ selon la longueur). Les fissures structurales (>6 mm, deplacement vertical) indiquent un probleme de fondation qui necessite une evaluation approfondie.'},
        {'q': 'Quand peut-on couler du beton au Quebec ?',
         'a': 'La saison de coulage optimale est d\'avril a octobre, quand les temperatures restent au-dessus de 5 degres C jour et nuit. En dessous de ce seuil, des additifs antigel et des couvertures isolantes sont necessaires, ce qui augmente les couts. Evitez les coulages en periode de pluie ou de chaleur intense (+30 degres C).'},
        {'q': 'Combien de temps dure un beton bien installe a {ville} ?',
         'a': 'Un beton de qualite avec bonne preparation de sol dure 30-50 ans. Le gel-degel quebecois est le principal ennemi — il faut des barres d\'armature (rebar) ou fibre, un bon drainage, et un produit de scellant aux 3-5 ans. Nos travaux incluent une garantie de 5 ans sur la main d\'oeuvre.'},
    ],
    'config_portes-fenetres.json': [
        {'q': 'Combien coute le remplacement de fenetres a {ville} ?',
         'a': 'Remplacer une fenetre standard (double vitrage, PVC blanc) coute entre {service1_min}$ et {service1_max}$ par unite, pose incluse, a {ville}. Pour une maison de 10-12 fenetres, prevoyez 8 000$-18 000$. Les fenetres triple vitrage ou bois-aluminium coutent 40-80% de plus mais reduisent la facture d\'energie.'},
        {'q': 'Y a-t-il des subventions pour remplacer mes fenetres au Quebec ?',
         'a': 'Oui — le programme Renoclimat d\'Hydro-Quebec offre jusqu\'a 1 500$ pour le remplacement de fenetres homologuees ENERGY STAR. Les proprietes historiques peuvent aussi beneficier de credits patrimoniaux. Nos fenetres sont certifiees ENERGY STAR et nous completons les formulaires de subvention pour vous.'},
        {'q': 'PVC, bois ou aluminium — quel cadre de fenetre choisir ?',
         'a': 'Le PVC est le choix dominant a {ville} : prix entre {service2_min}$ et {service2_max}$, excellent isolant thermique, sans entretien. L\'aluminium convient aux grandes baies coulissantes modernes. Le bois offre le meilleur confort thermique mais necessite un entretien annuel. Le bois-aluminium combine les deux.'},
        {'q': 'Faut-il un permis pour changer ses fenetres ?',
         'a': 'Le remplacement a l\'identique (meme dimension, meme emplacement) ne necessite generalement pas de permis. Agrandir une ouverture ou changer l\'emplacement d\'une fenetre necessite un permis de renovation. Nous verifions les exigences specifiques de {ville} avant de commencer les travaux.'},
        {'q': 'Quels signes indiquent qu\'il faut remplacer ses fenetres ?',
         'a': 'Condensation entre les vitres (joint brise), courants d\'air, difficile a ouvrir/fermer, cadres pourris ou peints de facon repetes — ce sont des signes clairs. Des fenetres de plus de 20 ans perdent generalement 30-40% de leur efficacite thermique initiale.'},
        {'q': 'Combien de temps prend la pose de fenetres ?',
         'a': 'La pose d\'une fenetre standard prend 1-2 heures par unite. Une maison de 10 fenetres est completee en 1-2 jours. Nous travaillons dans l\'ordre qui minimise les courants d\'air — en commencant par les ouvertures principales. Les fenetres sont mesurees sur commande 3-6 semaines avant l\'installation.'},
    ],
    'config_agrandissement.json': [
        {'q': 'Combien coute un agrandissement de maison au Quebec ?',
         'a': 'Un agrandissement standard (ajout d\'une piece, extension arriere) coute entre {service1_min}$ et {service1_max}$ le pied carre a {ville}, incluant la structure, l\'isolation, les fenetres et les finitions de base. Une extension de 400 pi2 (environ 20x20 pi) revient a 80 000$-160 000$ selon la complexite.'},
        {'q': 'Faut-il un permis pour agrandir sa maison a {ville} ?',
         'a': 'Oui, tout agrandissement necessitant une modification de l\'enveloppe du batiment requiert un permis de construction a {ville}. Les documents requis incluent des plans d\'architecte, un calcul de charge du sol et une etude de conformite au reglement de zonage. Notre equipe prepare le dossier complet.'},
        {'q': 'Quelle est la difference entre un agrandissement et une renovation ?',
         'a': 'Une renovation modifie l\'interieur existant (cuisine, salle de bain) — couts entre {service2_min}$ et {service2_max}$ selon la portee. Un agrandissement ajoute de la superficie habitable en dehors de l\'enveloppe actuelle. Les deux peuvent necessiter un permis, mais l\'agrandissement exige toujours des plans certifies.'},
        {'q': 'Combien de temps prend un projet d\'agrandissement ?',
         'a': 'De la demande de permis a la finition, un agrandissement typique prend 4-8 mois. Le permis seul peut prendre 4-8 semaines a {ville}. La construction (fondation, structure, finitions) prend ensuite 8-16 semaines selon la complexite. La planification rigoureuse evite les delais couteux.'},
        {'q': 'Vaut-il mieux agrandir ou demenager ?',
         'a': 'Agrandir coute generalement 40-60% de moins que demenager vers une propriete plus grande dans la meme zone de {ville}, quand on inclut les frais de transaction, de demenagement et d\'adaptation. Un agrandissement bien concu augmente aussi la valeur de revente de 70-80% de son cout de construction.'},
        {'q': 'Comment choisir entre un ajout de plain-pied ou un second etage ?',
         'a': 'Un ajout au sol (entre {service3_min}$ et {service3_max}$ pour 200 pi2) necessite un terrain disponible et des fondations supplementaires. Ajouter un etage evite de reduire le terrain mais exige un renforcement structurel de la maison existante. Nous evaluons les deux options lors de la visite gratuite.'},
    ],
    'config_ceramique.json': [
        {'q': 'Combien coute la pose de ceramique au Quebec ?',
         'a': 'La pose de ceramique standard coute entre {service1_min}$ et {service1_max}$ le pied carre (materiau + main d\'oeuvre) a {ville}. Une salle de bain de 80 pi2 revient a 1 600$-3 200$. Le prix varie selon le format de la tuile (grand format = plus long a poser), le type de pose (droit, diagonal, chevron) et la preparation du sous-plancher.'},
        {'q': 'Ceramique ou plancher flottant — que choisir pour ma cuisine ?',
         'a': 'La ceramique est recommandee pour les cuisines et salles de bain : impermeabilite totale, duree de vie de 20-50 ans, facile a nettoyer. Le plancher flottant est plus chaud sous les pieds et moins couteux ({service2_min}$-{service2_max}$ pi2 vs ceramique). Pour les zones humides, la ceramique reste le standard professionnel.'},
        {'q': 'Peut-on poser de la ceramique par-dessus un ancien plancher ?',
         'a': 'Oui, si le sous-plancher est rigide, de niveau et sans flexion. Un plancher de bois qui bouge causera des fissures dans le coulis en quelques annees. Nous verifions systematiquement la stabilite et ajoutons une membrane decouplee (Schluter Ditra) si necessaire, ce qui ajoute 2-4$ par pied carre mais garantit la longevite.'},
        {'q': 'Combien de temps prend la pose de ceramique dans une salle de bain ?',
         'a': 'Une salle de bain complete (plancher + douche + dosseret) prend generalement 2-4 jours de travail pour 2 poseurs, plus 24-48 heures de sechage du coulis avant usage. Nous planifions les travaux pour minimiser le temps sans acces a la salle de bain.'},
        {'q': 'Comment choisir le bon format de ceramique pour mon espace ?',
         'a': 'Les petites tuiles (mosaic 2x2, metro 3x6) conviennent aux douches et petits espaces — elles epousent les courbes. Les grands formats (24x24, 12x24) agrandissent visuellement les pieces et reduisent les joints, mais necessitent un sous-plancher parfaitement plan. Nous vous montrons des echantillons lors de la consultation gratuite.'},
        {'q': 'Quelle est la difference entre ceramique, porcelaine et pierre naturelle ?',
         'a': 'La ceramique ({service3_min}$-{service3_max}$ pi2 pose incluse) est poreuse et convient aux murs et planchers interieurs legers. La porcelaine (plus dense, moins absorbante) est recommandee pour les zones a fort trafic et les espaces humides. La pierre naturelle (marbre, travertin) est luxueuse mais necessite un scellant regulier.'},
    ],
    'config_toiture-plate.json': [
        {'q': 'Combien coute la refection d\'un toit plat au Quebec ?',
         'a': 'Refaire un toit plat a {ville} coute entre {service1_min}$ et {service1_max}$ selon la superficie et le systeme choisi. Une maison standard (1000-1500 pi2 de toit) revient a 8 000$-20 000$ en membrane TPO ou EPDM. Le prix inclut l\'arrachage de l\'ancienne membrane, l\'isolant rigide et la nouvelle pose.'},
        {'q': 'TPO, EPDM ou bitume — quel systeme de toit plat choisir ?',
         'a': 'Le TPO (thermoplastique) est le standard actuel : blanc reflechissant, soude a chaud, duree de vie de 20-25 ans, entre {service2_min}$ et {service2_max}$ le pi2 installe. L\'EPDM (caoutchouc noir) est moins couteux mais absorbe la chaleur. Le bitume app (multicouche) reste solide pour les grandes surfaces commerciales.'},
        {'q': 'Comment detecter une fuite de toit plat ?',
         'a': 'Les signes : taches sur le plafond (souvent loin de la source reelle), cloques ou bulles sur la membrane, joints de membrane decollees, eau stagnante persistante plus de 48h. Une fuite de toit plat non traitee cause des dommages a l\'isolant et la structure pouvant couter 3-5x le cout de la reparation initiale.'},
        {'q': 'Peut-on reparer un toit plat plutot que tout refaire ?',
         'a': 'Si la membrane a moins de 15 ans et que la deterioration est localisee (moins de 20% de la surface), une reparation partielle entre {service3_min}$ et {service3_max}$ est viable. Au-dela, la refection complete est plus economique sur 10 ans. Nous faisons une inspection thermique pour evaluer l\'etendue des degats invisibles.'},
        {'q': 'Combien d\'annees dure un toit plat bien installe ?',
         'a': 'Un toit plat TPO ou EPDM installe selon les normes dure 20-30 ans avec un entretien minimal (inspection annuelle, nettoyage des drains). Le bitume multicouche dure 15-20 ans. Les garanties fabricant vont de 15 a 30 ans selon le systeme. L\'entretien preventif double la duree de vie.'},
        {'q': 'Quelle est la pente minimale pour un toit plat a {ville} ?',
         'a': 'Les codes du batiment quebecois exigent une pente minimale de 1/4 de pouce par pied (environ 2%) pour assurer l\'evacuation de l\'eau. Un toit parfaitement plat accumule l\'eau, accelere la deterioration et risque l\'effondrement en cas de neige lourde. Nous verifions et corrigeons la pente lors de la refection si necessaire.'},
    ],
    'config_nettoyage-conduits.json': [
        {'q': 'Combien coute le nettoyage de conduits a {ville} ?',
         'a': 'Le nettoyage de conduits de ventilation pour une maison standard (8-12 bouches d\'air) coute entre {service1_min}$ et {service1_max}$ a {ville}. Le prix inclut l\'inspection video, le nettoyage a la brosse et par aspiration industrielle, et un rapport de l\'etat des conduits. Les maisons avec systeme central de climatisation ajoutent 100-150$.'},
        {'q': 'A quelle frequence faut-il nettoyer ses conduits ?',
         'a': 'Sante Canada recommande un nettoyage tous les 3-5 ans pour une residence standard. Accelerez la frequence si vous avez des animaux (poils dans les conduits), apres des travaux de renovation (poussiere de gypse), ou si un membre de la famille souffre d\'allergies ou d\'asthme. Un conduit propre peut reduire la consommation energetique du systeme de chauffage de 25%.'},
        {'q': 'Quel est le lien entre conduits sales et qualite de l\'air interieur ?',
         'a': 'Les conduits accumulent poussiere, pollen, moisissures, peau morte et bacteries qui recirculent dans votre maison a chaque cycle du systeme. Des etudes montrent que l\'air interieur peut etre 5 fois plus pollue que l\'air exterieur. Le nettoyage professionnel reduit significativement les allergenes et les odeurs de renfermage.'},
        {'q': 'Inclure le nettoyage de la fournaise avec les conduits ?',
         'a': 'Oui, nous recommandons de combiner les deux : le paquet conduits + fournaise ({service2_min}$-{service2_max}$) inclut le nettoyage des conduits, du plenum, du serpentin de la bobine de refroidissement et du filtre HEPA. C\'est 30-40% moins cher que deux visites separees et garantit que l\'air propre reste propre dans tout le systeme.'},
        {'q': 'Comment savoir si mes conduits sont vraiment sales ?',
         'a': 'Signes visibles : poussiere visible autour des grilles, odeur de renfermage ou de poussiere brulee a la mise en marche du chauffage, pellicule de poussiere qui reapparait rapidement apres le menage. Notre inspection video (incluse dans le service) montre exactement l\'etat de vos conduits avant et apres le nettoyage.'},
        {'q': 'Le nettoyage de conduits est-il efficace contre les moisissures ?',
         'a': 'Un nettoyage professionnel elimine les moisissures visibles dans les conduits. Mais si la source d\'humidite n\'est pas corrigee (humidificateur mal calibre, infiltration d\'eau), elles reviendront. Nos techniciens identifient la source et appliquent un agent anti-moisissures certifie EPA ({service3_min}$-{service3_max}$ supplementaire) pour prevenir la recidive.'},
    ],
}


def add_utm(url, source, campaign):
    """Insert UTM params before the # fragment."""
    if '#' in url:
        base, fragment = url.split('#', 1)
        return f"{base}&utm_campaign={campaign}#{fragment}"
    elif '?' in url:
        return f"{url}&utm_campaign={campaign}"
    else:
        return f"{url}?utm_campaign={campaign}"


updated = []
errors = []

for filename, (source, campaign) in UTM.items():
    path = os.path.join(BASE, filename)
    if not os.path.exists(path):
        errors.append(f'NOT FOUND: {path}')
        continue
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Fix 1: Move faq_templates from root to content (clean up root if present)
    if filename in FAQS:
        data['content']['faq_templates'] = FAQS[filename]
        if 'faq_templates' in data:
            del data['faq_templates']  # remove stale root key

    # Fix 2: Add UTM to affiliate.base_url (only if not already present)
    aff = data.get('affiliate', {})
    base_url = aff.get('base_url', '')
    if base_url and 'utm_campaign' not in base_url:
        aff['base_url'] = add_utm(base_url, source, campaign)
        data['affiliate'] = aff

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    updated.append(filename)
    print(f'OK: {filename}')
    print(f'    UTM: {data["affiliate"]["base_url"][-80:]}')

print(f'\nDone: {len(updated)}/8 updated, {len(errors)} errors.')
