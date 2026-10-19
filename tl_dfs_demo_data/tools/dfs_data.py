# Master data definitions for tl_dfs_demo_data (used by the image + XML generators).

# ---------------------------------------------------------------- categories
# key: (name, parent_key, public_name)
CATEGORIES = [
    ("lab_equipment", "Laboratory Equipment", None),
    ("protein", "Protein Analysis (Kjeldahl/Dumas)", "lab_equipment"),
    ("digestion", "Digestion Systems", "lab_equipment"),
    ("fat", "Fat Extraction (Soxhlet)", "lab_equipment"),
    ("fibre", "Fibre Analysis", "lab_equipment"),
    ("moisture", "Moisture & Dry Matter", "lab_equipment"),
    ("circulators", "Heating & Cooling Circulators", "lab_equipment"),
    ("baths", "Water Baths & Ovens", "lab_equipment"),
    ("sampleprep", "Sample Preparation (Mills, Homogenisers)", "lab_equipment"),
    ("spares", "Spares & Accessories", None),
    ("consumables", "Consumables & Glassware", None),
    ("services", "Services", None),
    ("svc_field", "Field Services", "services"),
    ("svc_contract", "Service Contracts", "services"),
]
# public (eCommerce) categories: key -> (name, sequence)
PUBLIC_CATEGORIES = [
    ("protein", "Protein Analysis (Kjeldahl/Dumas)", 10),
    ("fat", "Fat Extraction (Soxhlet)", 20),
    ("fibre", "Fibre Analysis", 30),
    ("moisture", "Moisture & Dry Matter", 40),
    ("digestion", "Digestion Systems", 50),
    ("circulators", "Heating & Cooling Circulators", 60),
    ("baths", "Water Baths & Ovens", 70),
    ("sampleprep", "Sample Preparation", 80),
    ("spares", "Spares & Accessories", 90),
    ("consumables", "Consumables & Glassware", 100),
    ("services", "Services", 110),
]

# ---------------------------------------------------------------- vendors
VENDORS = [
    # key, name, street, city, zip, country, email, phone, website
    ("kjelmark", "Kjelmark Analytik GmbH", "Industriestrasse 14", "Hamburg", "22041", "de",
     "orders@kjelmark-analytik.example", "+49 40 5550 1200", "https://www.kjelmark-analytik.example"),
    ("estrava", "Estrava Scientific S.r.l.", "Via dell'Industria 27", "Milano", "20151", "it",
     "export@estrava-scientific.example", "+39 02 5550 7781", "https://www.estrava-scientific.example"),
    ("calderbrook", "Calderbrook Thermal Ltd", "Unit 4, Charnwood Business Park", "Loughborough", "LE11 1QD", "uk",
     "sales@calderbrook-thermal.example", "+44 1509 555 210", "https://www.calderbrook-thermal.example"),
    ("feinwaage", "Feinwaage Instruments AG", "Seestrasse 101", "Zürich", "8002", "ch",
     "trade@feinwaage.example", "+41 44 555 34 00", "https://www.feinwaage.example"),
    ("pentland", "Pentland Sample Prep Ltd", "12 Attercliffe Road", "Sheffield", "S4 7WZ", "uk",
     "orders@pentland-sampleprep.example", "+44 114 555 0190", "https://www.pentland-sampleprep.example"),
    ("meridian", "Meridian Lab Supplies Ltd", "Brackmills Industrial Estate, Caswell Road", "Northampton", "NN4 7PW", "uk",
     "trade@meridianlabsupplies.example", "+44 1604 555 400", "https://www.meridianlabsupplies.example"),
]

# ---------------------------------------------------------------- products
# kind: equip (storable, serial), spare_lot (storable, lot), spare (storable, untracked),
#       consu (storable untracked), consu_exp (storable, lot + expiry), service, sub (subscription)
# image: real photo key (from Commons selection) or render spec "r:<template>:<color>"
P = []


def prod(key, name, code, categ, pub, kind, price, cost, vendor, image, desc, weight=0.0,
         optional=(), role=None, uom=None, published=True, warranty=None):
    P.append(dict(key=key, name=name, code=code, categ=categ, pub=pub, kind=kind, price=price,
                  cost=cost, vendor=vendor, image=image, desc=desc, weight=weight,
                  optional=list(optional), role=role, uom=uom, published=published, warranty=warranty))


W12 = "12-month return-to-base warranty, upgradeable to on-site cover."
W24 = "24-month on-site warranty (parts and labour) when installed by Northbrook engineers."

# Protein analysis
prod("kd40", "NA-KD40 Automatic Kjeldahl Distillation Unit", "NA-KD40", "protein", "protein", "equip", 14950, 9150,
     "kjelmark", "r:analyser:#b3262d",
     "Fully automatic steam distillation with integrated colorimetric titration, automatic alkali and boric acid dosing, "
     "touch-screen method library and USB/LIMS export. Distillation time under 4 minutes per sample; recovery >= 99.5 %.",
     68, optional=("kt8", "tubes250", "cat_tabs", "boric", "svc_install", "svc_training", "svc_extw"), warranty=W24)
prod("kd20", "NA-KD20 Semi-Automatic Kjeldahl Distillation Unit", "NA-KD20", "protein", "protein", "equip", 8450, 5050,
     "kjelmark", "kjeldahl_06",
     "Compact steam distillation unit with programmable NaOH dosing and safety door interlock. Ideal for routine "
     "protein determination in feed, dairy and cereal laboratories.",
     42, optional=("kt8", "tubes250", "boric", "svc_install"), warranty=W24)
prod("dn100", "NA-DN100 Dumas Combustion Nitrogen / Protein Analyser", "NA-DN100", "protein", "protein", "equip", 38500, 24600,
     "kjelmark", "dumas_04",
     "Combustion (Dumas) nitrogen analyser with 120-position autosampler, thermal-conductivity detection and helium-saving "
     "mode. Results in under 4 minutes without chemical digestion.",
     95, optional=("tin_caps", "comb_tube", "svc_install", "svc_training", "svc_extw"), warranty=W24)
prod("kt8", "NA-KT8 Kjeldahl Titration Module", "NA-KT8", "protein", "protein", "equip", 6200, 3700,
     "kjelmark", "titration_00",
     "Add-on potentiometric titration module with 20 mL burette and pH electrode; connects to NA-KD series distillers.",
     9, warranty=W12)

# Digestion
prod("db20", "NA-DB20 Block Digester, 20 Positions", "NA-DB20", "digestion", "digestion", "equip", 5850, 3420,
     "kjelmark", "digestion_01",
     "Aluminium block digester for 20 x 250 mL tubes, 420 deg C max, 20-step temperature programs and integrated lift.",
     38, optional=("sc4", "tubes250", "cat_tabs", "pcb_db"), warranty=W24)
prod("db8", "NA-DB8 Block Digester, 8 Positions", "NA-DB8", "digestion", "digestion", "equip", 3450, 2010,
     "kjelmark", "digestion_00",
     "Bench-top digestion block for 8 x 250 mL Kjeldahl tubes with exhaust manifold.",
     21, optional=("sc4", "tubes250"), warranty=W12)
prod("sc4", "NA-SC4 Fume Scrubber Unit", "NA-SC4", "digestion", "digestion", "equip", 2250, 1290,
     "kjelmark", "r:scrubber:#2b6cb0",
     "Three-stage neutralisation scrubber for acid fumes generated during Kjeldahl digestion.",
     16, warranty=W12)

# Fat extraction
prod("fx6", "NA-FX6 Automatic Soxhlet Fat Extraction System, 6 Positions", "NA-FX6", "fat", "fat", "equip", 16800, 10100,
     "estrava", "soxhlet_02",
     "Automated Soxhlet / Randall extraction for 6 samples with solvent recovery up to 90 %, sealed heating plates and "
     "built-in solvent sensor.",
     45, optional=("thimbles", "pet_ether", "thimble_holder", "svc_install", "svc_training"), warranty=W24)
prod("fx2", "NA-FX2 Compact Solvent Extraction Unit, 2 Positions", "NA-FX2", "fat", "fat", "equip", 7900, 4700,
     "estrava", "soxhlet_00",
     "Two-position solvent extractor for low-throughput laboratories and teaching.",
     19, optional=("thimbles", "pet_ether"), warranty=W12)
prod("hy6", "NA-HY6 Acid Hydrolysis Unit, 6 Positions", "NA-HY6", "fat", "fat", "equip", 9300, 5500,
     "estrava", "soxhlet_04",
     "Acid hydrolysis prior to total fat extraction (Weibull-Stoldt) with automatic rinsing.",
     31, warranty=W12)

# Fibre
prod("fb6", "NA-FB6 Crude Fibre Analyser, 6 Positions", "NA-FB6", "fibre", "fibre", "equip", 11200, 6650,
     "estrava", "r:analyser:#2f855a",
     "Crude fibre, ADF and NDF determination with hot and cold extraction in glass crucibles.",
     36, optional=("filter_bags", "svc_install"), warranty=W24)
prod("fb24", "NA-FB24 Dietary Fibre Analyser (Filter Bag Technique)", "NA-FB24", "fibre", "fibre", "equip", 13500, 8100,
     "estrava", "r:analyser:#276749",
     "Processes up to 24 filter bags simultaneously for crude fibre, ADF and NDF; reduced reagent consumption.",
     40, optional=("filter_bags",), warranty=W24)

# Moisture
prod("mb120", "NA-MB120 Halogen Moisture Analyser, 120 g", "NA-MB120", "moisture", "moisture", "equip", 2650, 1530,
     "feinwaage", "moisture_00",
     "Halogen moisture analyser, 120 g x 1 mg, 40-230 deg C, 100 method memory and GLP printout.",
     6, optional=("lamp_mb", "al_dishes"), warranty=W24)
prod("mb60", "NA-MB60 Moisture Balance, 60 g", "NA-MB60", "moisture", "moisture", "equip", 1450, 840,
     "feinwaage", "r:balance:#4a5568",
     "Entry-level infra-red moisture balance, 60 g x 1 mg.",
     4.5, optional=("al_dishes",), warranty=W12)
prod("dm50", "NA-DM50 Microwave Dry Matter Analyser", "NA-DM50", "moisture", "moisture", "equip", 18900, 11800,
     "feinwaage", "r:analyser:#553c9a",
     "Rapid microwave drying with integrated balance: total solids in dairy, meat and sauces in 2-5 minutes.",
     34, optional=("svc_install", "svc_training"), warranty=W24)

# Circulators
prod("rc12", "NA-RC12 Refrigerated / Heating Circulator, -25 to 150 deg C, 12 L", "NA-RC12", "circulators", "circulators", "equip",
     4350, 2560, "calderbrook", "r:circulator:#2c5282",
     "Refrigerated bath circulator, 12 L, +/-0.02 K stability, natural refrigerants, pressure/suction pump.",
     41, optional=("pump_rc",), warranty=W24)
prod("hc8", "NA-HC8 Heating Immersion Circulator, 8 L", "NA-HC8", "circulators", "circulators", "equip", 1690, 980,
     "calderbrook", "r:circulator:#c05621",
     "Heating circulator with 8 L stainless bath, 20-150 deg C, PID control.",
     12, warranty=W12)
prod("ch600", "NA-CH600 Recirculating Chiller, 600 W", "NA-CH600", "circulators", "circulators", "equip", 3250, 1910,
     "calderbrook", "r:chiller:#2b6cb0",
     "Compact recirculating chiller for condensers, rotary evaporators and distillation units.",
     38, warranty=W12)

# Baths & ovens
prod("wb22", "NA-WB22 Digital Water Bath, 22 L", "NA-WB22", "baths", "baths", "equip", 895, 505,
     "calderbrook", "waterbath_03",
     "General purpose digital water bath, ambient +5 to 99 deg C, gable lid and concentric ring set.",
     11, warranty=W12)
prod("swb28", "NA-SWB28 Shaking Water Bath, 28 L", "NA-SWB28", "baths", "baths", "equip", 2180, 1270,
     "calderbrook", "r:bath:#2c7a7b",
     "Reciprocating shaking water bath 20-200 strokes/min, universal tray.",
     29, warranty=W12)
prod("do110", "NA-DO110 Forced-Air Drying Oven, 110 L", "NA-DO110", "baths", "baths", "equip", 2450, 1430,
     "calderbrook", "oven_02",
     "Forced convection oven to 250 deg C, +/-0.5 K, ideal for moisture by oven-drying reference methods.",
     55, warranty=W12)
prod("mf9", "NA-MF9 Muffle Furnace, 1100 deg C, 9 L", "NA-MF9", "baths", "baths", "equip", 3600, 2150,
     "calderbrook", "muffle_05",
     "Ashing furnace for crude ash determination, ceramic fibre insulation, 9-segment programmer.",
     38, warranty=W12)
prod("vo50", "NA-VO50 Vacuum Drying Oven, 50 L", "NA-VO50", "baths", "baths", "equip", 4200, 2480,
     "calderbrook", "oven_05",
     "Vacuum oven for gentle drying of heat-sensitive samples (sugars, dairy powders).",
     62, warranty=W12)

# Sample prep
prod("lm200", "NA-LM200 Laboratory Hammer Mill", "NA-LM200", "sampleprep", "sampleprep", "equip", 5950, 3500,
     "pentland", "r:mill:#744210",
     "Hammer mill for grain, feed and oilseeds, 0.5-2 mm screens, cyclone collection.",
     48, optional=("screen_1mm",), warranty=W12)
prod("km10", "NA-KM10 Knife Mill, 1 L Bowl", "NA-KM10", "sampleprep", "sampleprep", "equip", 6800, 4050,
     "pentland", "r:mill:#975a16",
     "Knife mill for homogenising meat, cheese and moist foods; 1 L bowl, 10,000 rpm, gravity lid.",
     22, warranty=W12)
prod("hg400", "NA-HG400 Paddle Blender Homogeniser, 400 mL", "NA-HG400", "sampleprep", "sampleprep", "equip", 3150, 1860,
     "pentland", "r:blender:#4a5568",
     "Paddle blender for microbiology sample preparation in sterile bags (80-400 mL).",
     18, warranty=W12)
prod("hs25", "NA-HS25 High-Shear Homogeniser", "NA-HS25", "sampleprep", "sampleprep", "equip", 1250, 720,
     "pentland", "r:homogeniser:#2d3748",
     "Handheld high-shear disperser 3,000-25,000 rpm with 10 mm and 18 mm generators.",
     3, warranty=W12)
prod("cf16", "NA-CF16 Benchtop Centrifuge, 16 Place", "NA-CF16", "sampleprep", "sampleprep", "equip", 2950, 1720,
     "pentland", "centrifuge_00",
     "Benchtop centrifuge with swing-out and angle rotors, max 6,000 rpm, imbalance detection.",
     27, warranty=W12)

# Spares (lot tracked / untracked)
prod("heater_kd", "NA-KD Steam Generator Heating Element", "SP-KD-HE01", "spares", "spares", "spare_lot", 245, 128,
     "kjelmark", "r:part:#b7791f", "Replacement 2 kW heating element for NA-KD20/KD40 steam generators.", 0.6)
prod("splash_kd", "NA-KD Distillation Splash Head Assembly", "SP-KD-SH02", "spares", "spares", "spare", 185, 92,
     "kjelmark", "r:part:#4a5568", "Borosilicate splash head with PTFE seal kit.", 0.4)
prod("pcb_db", "NA-DB Temperature Controller PCB", "SP-DB-PCB1", "spares", "spares", "spare_lot", 420, 230,
     "kjelmark", "r:pcb:#276749", "Main controller board for NA-DB8/DB20 block digesters.", 0.3)
prod("thimble_holder", "NA-FX Extraction Thimble Holder Set (6)", "SP-FX-TH06", "spares", "spares", "spare", 165, 84,
     "estrava", "r:part:#718096", "Stainless steel thimble holders for NA-FX6 (set of 6).", 0.5)
prod("lamp_mb", "NA-MB Halogen Lamp Replacement", "SP-MB-HL01", "spares", "spares", "spare_lot", 89, 41,
     "feinwaage", "r:lamp:#d69e2e", "400 W halogen radiator for NA-MB120 moisture analyser.", 0.1)
prod("pump_rc", "NA-RC Circulator Pump Assembly", "SP-RC-PA01", "spares", "spares", "spare_lot", 365, 198,
     "calderbrook", "r:part:#2c5282", "Pressure/suction pump assembly for NA-RC series circulators.", 1.2)
prod("comb_tube", "NA-DN Quartz Combustion Tube", "SP-DN-QT01", "spares", "spares", "spare_lot", 310, 165,
     "kjelmark", "r:tube:#a0aec0", "Quartz combustion tube for NA-DN100 Dumas analyser.", 0.5)
prod("peri_tubing", "Peristaltic Pump Tubing Set", "SP-GEN-PT01", "spares", "spares", "spare", 58, 24,
     "meridian", "r:part:#c53030", "Pharmed tubing set for alkali and boric acid pumps.", 0.2)
prod("screen_1mm", "NA-LM Mill Screen 1.0 mm", "SP-LM-S10", "spares", "spares", "spare", 120, 58,
     "pentland", "r:part:#718096", "Stainless steel 1.0 mm screen for NA-LM200 hammer mill.", 0.3)

# Consumables & glassware
prod("tubes250", "Kjeldahl Digestion Tubes 250 mL (pack of 20)", "CG-KDT-250", "consumables", "consumables", "consu", 96, 44,
     "meridian", "tubes_00", "Borosilicate digestion tubes, 42 x 300 mm, pack of 20.", 4)
prod("cat_tabs", "Kjeldahl Catalyst Tablets Cu/Ti (1000)", "CG-KCT-1000", "consumables", "consumables", "consu_exp", 165, 78,
     "meridian", "r:pack:#2b6cb0", "Copper/titanium catalyst tablets, 5 g, mercury free. Shelf life 36 months.", 5)
prod("boric", "Boric Acid Receiver Solution 4 %, 5 L", "CG-BAS-5L", "consumables", "consumables", "consu_exp", 38, 15,
     "meridian", "r:bottle:#2f855a", "Ready-to-use boric acid receiving solution with mixed indicator. Shelf life 18 months.", 5.5)
prod("thimbles", "Cellulose Extraction Thimbles 33 x 80 mm (pack of 25)", "CG-CET-3380", "consumables", "consumables", "consu", 42, 17,
     "meridian", "r:pack:#975a16", "Single-thickness cellulose thimbles for Soxhlet extraction.", 0.4)
prod("filter_bags", "Fibre Filter Bags (pack of 100)", "CG-FFB-100", "consumables", "consumables", "consu", 135, 64,
     "estrava", "r:pack:#276749", "Heat-sealable filter bags for NA-FB24 fibre analyser.", 0.3)
prod("pet_ether", "Petroleum Ether 40-60, 2.5 L", "CG-PE-25L", "consumables", "consumables", "consu", 45, 21,
     "meridian", "r:bottle:#744210", "Analytical reagent grade extraction solvent (hazardous - ships by road only).", 2.2)
prod("beakers", "Glass Beakers 250 mL (pack of 12)", "CG-GB-250", "consumables", "consumables", "consu", 28, 11,
     "meridian", "glassware_02", "Low-form borosilicate beakers with spout, pack of 12.", 1.5)
prod("volflask", "Volumetric Flask 100 mL, Class A", "CG-VF-100A", "consumables", "consumables", "consu", 14, 5.5,
     "meridian", "flask_04", "Class A volumetric flask with PE stopper, batch certified.", 0.15)
prod("al_dishes", "Aluminium Moisture Dishes (pack of 100)", "CG-AMD-100", "consumables", "consumables", "consu", 32, 12,
     "feinwaage", "r:pack:#a0aec0", "Disposable 90 mm aluminium sample pans for moisture analysers.", 0.5)
prod("tin_caps", "Tin Foil Sample Capsules for Dumas (pack of 500)", "CG-TFC-500", "consumables", "consumables", "consu", 95, 44,
     "kjelmark", "r:pack:#718096", "Pressed tin capsules 6 x 12 mm for combustion analysis.", 0.2)
prod("buchner", "Porcelain Buchner Funnel 90 mm", "CG-PBF-90", "consumables", "consumables", "consu", 36, 15,
     "meridian", "fibre_06", "Porcelain filter funnel for vacuum filtration.", 0.6)
prod("dounce", "Glass Tissue Homogeniser Set (3 sizes)", "CG-GTH-SET", "consumables", "consumables", "consu", 74, 32,
     "meridian", "homogeniser_00", "Dounce-type glass homogenisers, 2/7/15 mL with pestles.", 0.6)

# Services
prod("svc_install", "Installation & Commissioning (per engineer day)", "SV-INST", "svc_field", "services", "service", 850, 320,
     None, "r:service:#2b6cb0",
     "On-site installation, IQ/OQ commissioning and handover by a factory-trained Northbrook engineer, per engineer day.",
     role="install", uom="day")
prod("svc_cal", "Annual Calibration Visit", "SV-CAL", "svc_field", "services", "service", 395, 150,
     None, "r:service:#2f855a", "UKAS-traceable calibration with certificate for one instrument.")
prod("svc_pm", "Preventive Maintenance Visit", "SV-PMV", "svc_field", "services", "service", 495, 190,
     None, "r:service:#744210", "Scheduled preventive maintenance including wear-part inspection and performance check.")
prod("svc_callout", "Engineer Call-out (per hour)", "SV-CALLOUT", "svc_field", "services", "service", 95, 45,
     None, "r:service:#c53030", "Breakdown call-out, charged per hour on site (minimum 2 hours), travel charged separately.",
     uom="hour", role="fse")
prod("svc_training", "Operator Training (half day)", "SV-TRAIN", "svc_field", "services", "service", 450, 160,
     None, "r:service:#553c9a", "On-site application training for up to 4 operators.")
prod("svc_extw", "Extended Warranty +12 Months", "SV-EXTW", "svc_contract", "services", "service", 690, 210,
     None, "r:service:#4a5568", "Extends manufacturer's warranty by a further 12 months (parts and labour).")
prod("sc_gold", "Service Contract - Gold (annual)", "SC-GOLD", "svc_contract", "services", "sub", 2400, 900,
     None, "r:contract:#b7791f",
     "Two preventive maintenance visits and one calibration per year, 24-hour response, parts and labour included.")
prod("sc_silver", "Service Contract - Silver (annual)", "SC-SILVER", "svc_contract", "services", "sub", 1450, 560,
     None, "r:contract:#718096",
     "One preventive maintenance visit with calibration per year, 48-hour response, labour included.")

PRODUCTS = P

# ---------------------------------------------------------------- customers
# key, name, street, city, zip, tags, phone, email-domain, payment term key, pricelist key, contacts[]
# contact: (key, name, function, avatar or None)
CUSTOMERS = [
    ("dalesway", "Dalesway Dairies Ltd", "Hellifield Road", "Skipton", "BD23 4AL", ["dairy"], "+44 1756 555 120",
     "dalesway-dairies.example", "30eom", "trade",
     [("rhughes", "Rachel Hughes", "QA Manager", "res_partner_address_13"),
      ("msutton", "Mark Sutton", "Laboratory Manager", "res_partner_address_1"),
      ("jpike", "Joanne Pike", "Procurement Manager", "res_partner_address_14")],
     [("dalesway_settle", "Dalesway Dairies - Settle Creamery", "Station Road", "Settle", "BD24 9AA")]),
    ("cotswold", "Cotswold Creamery Co-operative", "Bath Road", "Stroud", "GL5 3QF", ["dairy"], "+44 1453 555 300",
     "cotswoldcreamery.example", "30", "trade",
     [("acollins", "Andrew Collins", "Technical Manager", "res_partner_address_10"),
      ("sbell", "Sarah Bell", "Laboratory Supervisor", "res_partner_address_16")], []),
    ("highland", "Highland Grain Millers Ltd", "Longman Industrial Estate", "Inverness", "IV1 1SU", ["cereals"],
     "+44 1463 555 440", "highlandgrain.example", "30", "trade",
     [("cfraser", "Callum Fraser", "QA Manager", "res_partner_address_11"),
      ("imackenzie", "Isla Mackenzie", "Procurement Officer", "res_partner_address_17")], []),
    ("fenland", "Fenland Cereals plc", "Cromwell Road", "Wisbech", "PE14 0RG", ["cereals"], "+44 1945 555 610",
     "fenlandcereals.example", "30eom", "key",
     [("pgrant", "Peter Grant", "Head of Quality", "res_partner_address_15")], []),
    ("ironbridge", "Ironbridge Brewing Company Ltd", "Wharfage", "Telford", "TF8 7AW", ["beverages"],
     "+44 1952 555 088", "ironbridgebrewing.example", "30", "trade",
     [("jholloway", "Jack Holloway", "Head Brewer", "res_partner_address_18"),
      ("eward", "Emma Ward", "Laboratory Technician", "res_partner_address_28")], []),
    ("thamesvalley", "Thames Valley Brewery Ltd", "Kennet Side", "Reading", "RG1 3EA", ["beverages"],
     "+44 118 555 7720", "thamesvalleybrewery.example", "30", "trade",
     [("oreed", "Oliver Reed", "Quality Manager", "res_partner_address_2")], []),
    ("pennine", "Pennine Meat Processors Ltd", "Tong Street", "Bradford", "BD4 9PH", ["meat"], "+44 1274 555 930",
     "penninemeat.example", "30eom", "key",
     [("skaye", "Stuart Kaye", "Technical Director", "res_partner_address_24"),
      ("ncross", "Natalie Cross", "QA Manager", "res_partner_address_30"),
      ("glomas", "Gary Lomas", "Purchasing Manager", "res_partner_address_25")], []),
    ("severn", "Severn Valley Poultry Ltd", "Battlefield Enterprise Park", "Shrewsbury", "SY1 3AF", ["meat"],
     "+44 1743 555 260", "severnvalleypoultry.example", "30", "trade",
     [("hdavies", "Helen Davies", "QA Manager", "res_partner_address_31")], []),
    ("albion", "Albion Analytical Services Ltd", "Trafford Park Road", "Manchester", "M17 1HH", ["contract_lab"],
     "+44 161 555 4100", "albion-analytical.example", "30eom", "key",
     [("jwhitaker", "Dr James Whitaker", "Laboratory Director", "res_partner_address_27"),
      ("glee", "Grace Lee", "Senior Analyst", "res_partner_address_32"),
      ("nbrooks", "Nathan Brooks", "Procurement Manager", "res_partner_address_3")],
     [("albion_runcorn", "Albion Analytical - Runcorn Laboratory", "Manor Park", "Runcorn", "WA7 1SS")]),
    ("northgate", "Northgate Food Testing Laboratories Ltd", "Pepper Road", "Leeds", "LS10 2RU", ["contract_lab"],
     "+44 113 555 0870", "northgatelabs.example", "30", "trade",
     [("kwalsh", "Dr Karen Walsh", "Technical Manager", "res_partner_address_33")], []),
    ("wessex", "University of Wessex - School of Food Science", "University Road", "Southampton", "SO17 1BJ",
     ["education"], "+44 23 8055 5000", "wessex-uni.example", "30", "edu",
     [("mhart", "Prof. Michael Hart", "Head of School", "res_partner_address_34"),
      ("akowalski", "Dr Anna Kowalski", "Teaching Laboratory Manager", None),
      ("lgrant", "Lisa Grant", "Procurement Services", None)], []),
    ("caledonian", "Caledonian University - Department of Nutrition", "Cowcaddens Road", "Glasgow", "G4 0BA",
     ["education"], "+44 141 555 3000", "caledonian-uni.example", "30", "edu",
     [("ecampbell", "Dr Euan Campbell", "Senior Lecturer", "res_partner_address_4")], []),
    ("wmpal", "West Midlands Public Analyst Laboratory", "Lancaster Circus", "Birmingham", "B7 4AB",
     ["public_analyst"], "+44 121 555 6600", "wmpublicanalyst.example", "30", "edu",
     [("rkumar", "Dr Rajesh Kumar", "Public Analyst", "res_partner_address_5"),
      ("sroberts", "Sian Roberts", "Laboratory Manager", None)], []),
    ("kentss", "Kent County Scientific Services", "Penenden Heath Road", "Maidstone", "ME14 2NY",
     ["public_analyst"], "+44 1622 555 410", "kentscientific.example", "30", "edu",
     [("pfisher", "Paul Fisher", "Senior Scientist", "res_partner_address_7")], []),
    ("cambrian", "Cambrian Spring Waters Ltd", "Llanfaes", "Brecon", "LD3 8DY", ["beverages"], "+44 1874 555 190",
     "cambrianspring.example", "30", "trade",
     [("rllewellyn", "Rhys Llewellyn", "QA Manager", None),
      ("bjones", "Bethan Jones", "Laboratory Analyst", None)], []),
    ("northumbria", "Northumbria Bakeries Ltd", "Shields Road", "Newcastle upon Tyne", "NE6 2YD", ["cereals"],
     "+44 191 555 2840", "northumbriabakeries.example", "30", "trade",
     [("crobson", "Chris Robson", "Technical Manager", None)], []),
]

TAGS = [
    ("dairy", "Dairy", 10), ("meat", "Meat", 1), ("cereals", "Cereals", 3), ("beverages", "Beverages", 4),
    ("contract_lab", "Contract Lab", 5), ("education", "Education", 6), ("public_analyst", "Public Analyst", 7),
    ("vendor", "Manufacturer / Supplier", 8),
]

# ---------------------------------------------------------------- HR
DEPARTMENTS = [
    ("management", "Management", None),
    ("sales", "Sales", "management"),
    ("field_service", "Field Service", "management"),
    ("tech_support", "Technical Support", "management"),
    ("warehouse", "Warehouse & Logistics", "management"),
    ("finance", "Finance", "management"),
]
JOBS = [
    ("md", "Managing Director", "management"),
    ("ops_dir", "Operations Director", "management"),
    ("sales_mgr", "Sales Manager", "sales"),
    ("kam", "Key Account Manager", "sales"),
    ("sales_eng", "Sales Engineer", "sales"),
    ("inside_sales", "Inside Sales Coordinator", "sales"),
    ("fs_mgr", "Field Service Manager", "field_service"),
    ("fse", "Field Service Engineer", "field_service"),
    ("install_eng", "Installation Engineer", "field_service"),
    ("cal_tech", "Calibration Technician", "field_service"),
    ("ts_mgr", "Technical Support Manager", "tech_support"),
    ("app_spec", "Applications Specialist", "tech_support"),
    ("ts_eng", "Technical Support Engineer", "tech_support"),
    ("wh_sup", "Warehouse Supervisor", "warehouse"),
    ("logistics", "Logistics Coordinator", "warehouse"),
    ("fin_mgr", "Finance Manager", "finance"),
    ("accounts", "Accounts Assistant", "finance"),
]
# key, name, job, dept, manager, image, login(user) or None, roles, default role, calendar
EMPLOYEES = [
    ("dwhitfield", "David Whitfield", "md", "management", None, "employee_md", None, [], None, "std"),
    ("cashworth", "Claire Ashworth", "ops_dir", "management", "dwhitfield", "employee_vad", None, [], None, "std"),
    ("slockwood", "Simon Lockwood", "sales_mgr", "sales", "dwhitfield", "employee_stw", "simon.lockwood", ["sales_eng"], "sales_eng", "std"),
    ("hprice", "Hannah Price", "kam", "sales", "slockwood", "employee_chs", "hannah.price", ["sales_eng"], "sales_eng", "std"),
    ("tfletcher", "Tom Fletcher", "sales_eng", "sales", "slockwood", "employee_qdp", "tom.fletcher", ["sales_eng"], "sales_eng", "std"),
    ("psharma", "Priya Sharma", "sales_eng", "sales", "slockwood", "employee_jod", "priya.sharma", ["sales_eng"], "sales_eng", "std"),
    ("emorgan", "Ellie Morgan", "inside_sales", "sales", "slockwood", "employee_jth", "ellie.morgan", [], None, "std"),
    ("gevans", "Gareth Evans", "fs_mgr", "field_service", "cashworth", "employee_jve", "gareth.evans", ["fse", "install"], "fse", "field"),
    ("dokafor", "Daniel Okafor", "fse", "field_service", "gevans", "employee_han", "daniel.okafor", ["fse", "install"], "fse", "field"),
    ("rpatel", "Ravi Patel", "fse", "field_service", "gevans", "employee_fme", "ravi.patel", ["fse", "calibration"], "fse", "field"),
    ("ldoyle", "Liam Doyle", "install_eng", "field_service", "gevans", "employee_lur", "liam.doyle", ["install", "fse"], "install", "field"),
    ("sturner", "Sophie Turner", "cal_tech", "field_service", "gevans", "employee_hne", "sophie.turner", ["calibration"], "calibration", "field"),
    ("mbennett", "Marcus Bennett", "fse", "field_service", "gevans", "employee_ngh", "marcus.bennett", ["fse", "calibration"], "fse", "field"),
    ("lchen", "Laura Chen", "ts_mgr", "tech_support", "cashworth", "employee_jog", "laura.chen", [], None, "std"),
    ("bharris", "Ben Harris", "app_spec", "tech_support", "lchen", "employee_jgo", "ben.harris", ["sales_eng"], "sales_eng", "std"),
    ("awright", "Amelia Wright", "ts_eng", "tech_support", "lchen", "employee_mit", "amelia.wright", [], None, "std"),
    ("kmurray", "Kevin Murray", "wh_sup", "warehouse", "cashworth", "employee_al", None, [], None, "std"),
    ("zclarke", "Zoe Clarke", "logistics", "warehouse", "kmurray", "employee_awa", None, [], None, "std"),
    ("fmacleod", "Fiona MacLeod", "fin_mgr", "finance", "dwhitfield", "employee_niv", None, [], None, "std"),
    ("mlin", "Mei Lin", "accounts", "finance", "fmacleod", "employee_fpi", None, [], None, "std"),
]
