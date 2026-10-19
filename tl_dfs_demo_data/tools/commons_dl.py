"""Search Wikimedia Commons for freely licensed photos and download candidates.

Usage: python -I commons_dl.py <out_dir>
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

OUT = sys.argv[1]
UA = "NorthbrookDemoDataBuilder/1.0 (Odoo demo data; contact yuvaraj@thoughtlogik.com)"
API = "https://commons.wikimedia.org/w/api.php"
OK_LIC = re.compile(r"^(CC0|Public domain|PD|CC BY(-SA)? ?\d|CC BY(-SA)?$|CC-BY|CC-BY-SA)", re.I)

QUERIES = {
    "kjeldahl": ["Kjeldahl distillation apparatus", "Kjeldahl", "nitrogen distillation laboratory"],
    "digestion": ["Kjeldahl digestion", "digestion block laboratory", "Kjeldahl digestion tubes"],
    "dumas": ["elemental analyzer", "nitrogen analyzer laboratory", "CHN analyzer"],
    "soxhlet": ["Soxhlet extractor", "Soxhlet apparatus", "solvent extraction laboratory"],
    "fibre": ["fiber analyzer", "crude fibre determination", "filtration apparatus laboratory"],
    "moisture": ["moisture analyzer", "moisture balance", "analytical balance"],
    "circulator": ["laboratory thermostat circulator", "refrigerated circulator", "immersion circulator laboratory", "Thermostat Labor"],
    "chiller": ["laboratory chiller", "recirculating chiller"],
    "waterbath": ["laboratory water bath", "water bath laboratory", "Wasserbad Labor"],
    "oven": ["laboratory oven", "drying oven laboratory", "Trockenschrank"],
    "muffle": ["muffle furnace", "laboratory furnace"],
    "vacuumoven": ["vacuum oven laboratory", "vacuum drying oven"],
    "mill": ["laboratory mill", "hammer mill laboratory", "grinder laboratory sample"],
    "homogeniser": ["homogenizer laboratory", "stomacher", "ultra turrax", "disperser laboratory"],
    "centrifuge": ["laboratory centrifuge", "benchtop centrifuge"],
    "titration": ["titrator", "automatic titrator", "burette titration"],
    "glassware": ["laboratory glassware", "beakers laboratory"],
    "flask": ["volumetric flask"],
    "thimble": ["extraction thimble", "Soxhlet thimble"],
    "tubes": ["test tubes rack laboratory"],
    "engineer": ["laboratory technician equipment", "service engineer laboratory"],
    "lab": ["food testing laboratory", "food analysis laboratory"],
    "shakingbath": ["shaking water bath"],
    "scrubber": ["fume hood laboratory"],
}


def api(params):
    params = dict(params, format="json")
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def strip_html(s):
    return re.sub(r"<[^>]+>", "", s or "").strip()


def main():
    os.makedirs(OUT, exist_ok=True)
    meta = {}
    for key, qs in QUERIES.items():
        seen = 0
        for q in qs:
            if seen >= 8:
                break
            try:
                data = api({
                    "action": "query", "generator": "search",
                    "gsrsearch": q + " filetype:bitmap", "gsrnamespace": 6, "gsrlimit": 12,
                    "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime",
                    "iiurlwidth": 1024,
                })
            except Exception as e:  # noqa
                print("ERR", q, e)
                continue
            pages = sorted((data.get("query") or {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
            for p in pages:
                if seen >= 8:
                    break
                ii = (p.get("imageinfo") or [{}])[0]
                if ii.get("mime") not in ("image/jpeg", "image/png", "image/webp"):
                    continue
                if (ii.get("width") or 0) < 400:
                    continue
                em = ii.get("extmetadata") or {}
                lic = strip_html((em.get("LicenseShortName") or {}).get("value"))
                if not OK_LIC.match(lic or ""):
                    continue
                title = p["title"]
                if any(title == m["title"] for m in meta.values()):
                    continue
                fname = f"{key}_{seen:02d}.jpg"
                turl = ii.get("thumburl") or ii.get("url")
                try:
                    req = urllib.request.Request(turl, headers={"User-Agent": UA})
                    with urllib.request.urlopen(req, timeout=60) as r:
                        blob = r.read()
                except Exception as e:  # noqa
                    print("DLERR", title, e)
                    continue
                with open(os.path.join(OUT, fname), "wb") as f:
                    f.write(blob)
                meta[fname] = {
                    "title": title,
                    "author": strip_html((em.get("Artist") or {}).get("value"))[:200],
                    "license": lic,
                    "license_url": strip_html((em.get("LicenseUrl") or {}).get("value")),
                    "source": ii.get("descriptionurl"),
                    "query": q,
                }
                seen += 1
                time.sleep(0.3)
        print(key, seen, flush=True)
    with open(os.path.join(OUT, "meta.json"), "w") as f:
        json.dump(meta, f, indent=1)


if __name__ == "__main__":
    main()
