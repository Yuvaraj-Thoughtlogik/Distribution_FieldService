"""Build all images for tl_dfs_demo_data.

python -I gen_images.py <img_dl_dir> <module_dir>
"""
import json
import os
import shutil
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dfs_data as D  # noqa: E402

DL, MOD = sys.argv[1], sys.argv[2]
IMG = os.path.join(MOD, "static", "img")
FONT_B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_R = "/System/Library/Fonts/Supplemental/Arial.ttf"
ODOO = "/Users/yuvaraj/Documents/Odoo/Odoo20"


def font(size, bold=True):
    return ImageFont.truetype(FONT_B if bold else FONT_R, size)


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def mix(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


S = 2048  # supersampled canvas


def canvas():
    im = Image.new("RGB", (S, S), (255, 255, 255))
    d = ImageDraw.Draw(im)
    for y in range(S):
        c = mix((250, 251, 253), (226, 230, 236), y / S)
        d.line([(0, y), (S, y)], fill=c)
    return im


def shadow(im, box):
    sh = Image.new("L", (S, S), 0)
    ImageDraw.Draw(sh).ellipse(box, fill=110)
    sh = sh.filter(ImageFilter.GaussianBlur(40))
    dark = Image.new("RGB", (S, S), (120, 125, 135))
    im.paste(dark, (0, 0), sh)


def vgrad_rect(im, box, c_top, c_bot, radius=40):
    x0, y0, x1, y1 = [int(v) for v in box]
    g = Image.new("RGB", (x1 - x0, y1 - y0))
    gd = ImageDraw.Draw(g)
    for y in range(y1 - y0):
        gd.line([(0, y), (x1 - x0, y)], fill=mix(c_top, c_bot, y / max(1, y1 - y0)))
    m = Image.new("L", g.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, g.size[0] - 1, g.size[1] - 1], radius=radius, fill=255)
    im.paste(g, (x0, y0), m)


def badge(d, x, y, code, accent):
    d.text((x, y), "NORTHBROOK", font=font(44), fill=(60, 66, 78))
    d.text((x, y + 54), code, font=font(36, False), fill=shade(accent, 0.8))


def display(d, box, text="", color=(120, 220, 160)):
    d.rounded_rectangle(box, radius=18, fill=(28, 34, 44))
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0 + 14, y0 + 14, x1 - 14, y1 - 14], radius=10, fill=(36, 48, 62))
    if text:
        d.text((x0 + 34, y0 + (y1 - y0) / 2 - 30), text, font=font(56), fill=color)


def body_box(im, d, box, accent, code, top=(244, 246, 249), bot=(205, 211, 220)):
    shadow(im, (box[0] + 30, box[3] - 50, box[2] - 30, box[3] + 60))
    vgrad_rect(im, box, top, bot, 50)
    d.rounded_rectangle(box, radius=50, outline=(170, 176, 188), width=4)


def r_analyser(im, d, accent, code):
    box = (430, 420, 1620, 1640)
    body_box(im, d, box, accent, code)
    vgrad_rect(im, (430, 420, 1620, 640), shade(accent, 1.15), shade(accent, 0.85), 50)
    d.rectangle([430, 590, 1620, 640], fill=shade(accent, 0.85))
    display(d, (1180, 720, 1560, 960), "98.6%")
    # window / door
    d.rounded_rectangle((520, 720, 1110, 1460), radius=30, fill=(200, 214, 228), outline=(150, 160, 175), width=6)
    for i in range(5):
        x = 590 + i * 100
        d.rounded_rectangle((x, 900, x + 50, 1380), radius=20, fill=(235, 242, 248), outline=(160, 175, 190), width=4)
    d.ellipse((1300, 1060, 1440, 1200), fill=shade(accent, 1.0), outline=(90, 90, 90), width=4)
    badge(d, 1180, 1300, code, accent)
    d.text((480, 455), "NORTHBROOK", font=font(64), fill=(255, 255, 255))


def r_scrubber(im, d, accent, code):
    box = (520, 600, 1520, 1640)
    body_box(im, d, box, accent, code)
    for i, x in enumerate((600, 900, 1200)):
        d.rounded_rectangle((x, 380, x + 240, 1100), radius=60, fill=(225, 238, 246), outline=(150, 165, 180), width=6)
        d.rectangle((x + 20, 760 + i * 40, x + 220, 1080), fill=mix(accent, (230, 240, 250), 0.5))
    d.rectangle((520, 1100, 1520, 1180), fill=shade(accent, 0.9))
    display(d, (620, 1260, 1000, 1460), "ON")
    badge(d, 1080, 1290, code, accent)


def r_balance(im, d, accent, code):
    shadow(im, (380, 1480, 1670, 1640))
    vgrad_rect(im, (380, 1100, 1670, 1560), (245, 246, 248), (200, 205, 214), 60)
    d.rounded_rectangle((380, 1100, 1670, 1560), radius=60, outline=(165, 170, 182), width=4)
    # hood
    d.chord((520, 520, 1300, 1300), 180, 360, fill=shade(accent, 1.1), outline=(70, 70, 80), width=6)
    d.rectangle((520, 905, 1300, 1110), fill=shade(accent, 0.9))
    d.ellipse((780, 650, 1040, 860), fill=(255, 210, 120), outline=(120, 90, 40), width=5)
    display(d, (1340, 1180, 1620, 1360), "5.21")
    badge(d, 460, 1380, code, accent)


def r_circulator(im, d, accent, code):
    box = (480, 760, 1580, 1640)
    body_box(im, d, box, accent, code)
    d.rectangle((520, 780, 1540, 900), fill=(190, 198, 208))
    # controller head
    vgrad_rect(im, (980, 360, 1540, 820), shade(accent, 1.15), shade(accent, 0.8), 40)
    display(d, (1030, 430, 1490, 620), "-20.0")
    for i in range(3):
        d.ellipse((1060 + i * 140, 660, 1150 + i * 140, 750), fill=(235, 235, 240), outline=(80, 80, 90), width=4)
    d.rectangle((560, 800, 940, 880), fill=(160, 205, 235))
    for i in range(10):
        d.rectangle((560 + i * 100, 1040, 600 + i * 100, 1400), fill=shade((205, 211, 220), 0.85))
    badge(d, 560, 1460, code, accent)


def r_chiller(im, d, accent, code):
    box = (620, 380, 1430, 1660)
    body_box(im, d, box, accent, code)
    vgrad_rect(im, (620, 380, 1430, 620), shade(accent, 1.1), shade(accent, 0.85), 50)
    display(d, (720, 440, 1100, 580), "10.0")
    for i in range(14):
        d.rectangle((700, 760 + i * 46, 1350, 780 + i * 46), fill=(150, 156, 168))
    badge(d, 700, 1460, code, accent)


def r_bath(im, d, accent, code):
    box = (300, 900, 1750, 1600)
    body_box(im, d, box, accent, code)
    d.polygon([(330, 900), (1720, 900), (1600, 640), (450, 640)], fill=(210, 216, 226), outline=(150, 158, 170))
    d.line([(450, 640), (1600, 640)], fill=(140, 148, 160), width=8)
    d.rectangle((300, 900, 1750, 960), fill=shade(accent, 0.95))
    display(d, (380, 1060, 800, 1260), "37.0")
    d.ellipse((880, 1090, 1020, 1230), fill=(230, 232, 238), outline=(80, 80, 90), width=5)
    badge(d, 1180, 1110, code, accent)


def r_mill(im, d, accent, code):
    box = (520, 1000, 1530, 1660)
    body_box(im, d, box, accent, code)
    d.polygon([(700, 380), (1350, 380), (1150, 820), (900, 820)], fill=shade(accent, 1.1), outline=(70, 60, 50))
    d.rectangle((880, 820, 1170, 1010), fill=(150, 156, 168))
    d.rounded_rectangle((1300, 1230, 1480, 1560), radius=30, fill=(220, 232, 240), outline=(140, 150, 165), width=5)
    display(d, (600, 1120, 980, 1300), "18000")
    badge(d, 600, 1400, code, accent)


def r_blender(im, d, accent, code):
    box = (420, 560, 1640, 1640)
    body_box(im, d, box, accent, code)
    d.rounded_rectangle((520, 680, 1180, 1500), radius=30, fill=(214, 224, 236), outline=(130, 140, 155), width=6)
    d.rounded_rectangle((640, 760, 1060, 1420), radius=40, fill=(245, 248, 252), outline=(170, 175, 185), width=4)
    display(d, (1250, 720, 1560, 900), "60s")
    badge(d, 1240, 1300, code, accent)


def r_homogeniser(im, d, accent, code):
    shadow(im, (600, 1560, 1450, 1680))
    d.rounded_rectangle((600, 1540, 1450, 1640), radius=30, fill=(60, 66, 78))
    d.rectangle((1250, 300, 1310, 1560), fill=(170, 176, 188))
    vgrad_rect(im, (820, 380, 1160, 1000), shade(accent, 1.4), shade(accent, 0.9), 70)
    d.rectangle((1160, 560, 1260, 640), fill=(120, 126, 138))
    d.rectangle((960, 1000, 1020, 1380), fill=(200, 204, 212))
    d.rounded_rectangle((900, 1180, 1080, 1520), radius=30, fill=(220, 236, 248), outline=(140, 160, 180), width=5)
    badge(d, 640, 1690 - 280, code, accent)


def r_part(im, d, accent, code):
    shadow(im, (560, 1380, 1480, 1520))
    vgrad_rect(im, (620, 700, 1420, 1420), shade(accent, 1.3), shade(accent, 0.7), 120)
    d.ellipse((760, 840, 1280, 1280), fill=(225, 228, 234), outline=(100, 106, 118), width=10)
    d.ellipse((900, 980, 1140, 1140), fill=shade(accent, 0.6))
    for i in range(8):
        import math
        a = i * math.pi / 4
        cx, cy = 1020 + 330 * math.cos(a), 1060 + 330 * math.sin(a)
        d.ellipse((cx - 30, cy - 30, cx + 30, cy + 30), fill=(200, 204, 212), outline=(90, 90, 100), width=4)
    d.text((620, 1560), code, font=font(80), fill=(60, 66, 78))


def r_pcb(im, d, accent, code):
    shadow(im, (420, 1400, 1640, 1520))
    d.rounded_rectangle((420, 640, 1640, 1440), radius=30, fill=shade(accent, 0.9), outline=(30, 70, 40), width=6)
    for i in range(4):
        d.rectangle((520 + i * 260, 760, 700 + i * 260, 940), fill=(30, 32, 36))
    for i in range(12):
        d.line([(480, 1000 + i * 30), (1580, 1000 + i * 30)], fill=(200, 170, 80), width=4)
    d.rectangle((1300, 1220, 1560, 1380), fill=(230, 230, 230))
    d.text((620, 1560), code, font=font(80), fill=(60, 66, 78))


def r_lamp(im, d, accent, code):
    shadow(im, (700, 1460, 1350, 1560))
    d.ellipse((620, 420, 1420, 1220), fill=(255, 244, 200), outline=shade(accent, 0.8), width=12)
    d.ellipse((760, 560, 1080, 800), fill=(255, 255, 240))
    d.rectangle((860, 1180, 1180, 1460), fill=(190, 196, 206), outline=(100, 100, 110), width=6)
    for i in range(4):
        d.line([(860, 1230 + i * 55), (1180, 1230 + i * 55)], fill=(120, 126, 138), width=8)
    d.text((620, 1580), code, font=font(80), fill=(60, 66, 78))


def r_tube(im, d, accent, code):
    shadow(im, (300, 1150, 1750, 1260))
    d.rounded_rectangle((300, 900, 1750, 1140), radius=110, fill=(232, 238, 246), outline=(150, 165, 185), width=8)
    d.rounded_rectangle((340, 940, 1710, 980), radius=20, fill=(255, 255, 255))
    d.text((620, 1400), code, font=font(80), fill=(60, 66, 78))


def r_pack(im, d, accent, code):
    shadow(im, (500, 1520, 1600, 1640))
    d.polygon([(500, 700), (1300, 700), (1300, 1600), (500, 1600)], fill=(214, 180, 130), outline=(120, 90, 50))
    d.polygon([(1300, 700), (1560, 520), (1560, 1420), (1300, 1600)], fill=(180, 145, 100), outline=(120, 90, 50))
    d.polygon([(500, 700), (760, 520), (1560, 520), (1300, 700)], fill=(232, 202, 155), outline=(120, 90, 50))
    d.rectangle((580, 900, 1220, 1360), fill=(255, 255, 255), outline=shade(accent, 0.9), width=8)
    d.rectangle((580, 900, 1220, 1000), fill=accent)
    d.text((610, 920), "NORTHBROOK", font=font(52), fill=(255, 255, 255))
    d.text((610, 1060), code, font=font(56), fill=(50, 50, 60))
    d.text((610, 1150), "Laboratory supplies", font=font(40, False), fill=(90, 90, 100))


def r_bottle(im, d, accent, code):
    shadow(im, (640, 1560, 1410, 1660))
    d.rounded_rectangle((640, 640, 1410, 1620), radius=90, fill=mix(accent, (255, 255, 255), 0.55), outline=shade(accent, 0.7), width=8)
    d.rounded_rectangle((860, 400, 1190, 660), radius=30, fill=(40, 44, 52))
    d.rectangle((700, 900, 1350, 1380), fill=(255, 255, 255), outline=shade(accent, 0.8), width=6)
    d.rectangle((700, 900, 1350, 990), fill=accent)
    d.text((730, 915), "NORTHBROOK", font=font(50), fill=(255, 255, 255))
    d.text((730, 1060), code, font=font(56), fill=(50, 50, 60))
    d.text((730, 1160), "Reagent", font=font(44, False), fill=(90, 90, 100))


def r_service(im, d, accent, code):
    d.ellipse((424, 344, 1624, 1544), fill=accent)
    d.ellipse((504, 424, 1544, 1464), outline=(255, 255, 255), width=18)
    # wrench
    w = Image.new("L", (S, S), 0)
    wd = ImageDraw.Draw(w)
    wd.rounded_rectangle((980, 700, 1080, 1260), radius=50, fill=255)
    wd.ellipse((880, 560, 1180, 860), fill=255)
    wd.rectangle((990, 520, 1070, 700), fill=0)
    w = w.rotate(-40, center=(1024, 944))
    im.paste((255, 255, 255), (0, 0), w)
    d.text((1024, 1700), code, font=font(110), fill=(50, 56, 68), anchor="mm")


def r_contract(im, d, accent, code):
    shadow(im, (520, 1600, 1520, 1700))
    d.rectangle((520, 300, 1520, 1640), fill=(255, 255, 255), outline=(170, 176, 188), width=6)
    d.rectangle((520, 300, 1520, 460), fill=accent)
    d.text((570, 340), "SERVICE CONTRACT", font=font(72), fill=(255, 255, 255))
    for i in range(9):
        d.line([(600, 560 + i * 80), (1440 - (i % 3) * 120, 560 + i * 80)], fill=(200, 205, 214), width=14)
    d.ellipse((1140, 1240, 1420, 1520), fill=shade(accent, 1.1), outline=shade(accent, 0.6), width=10)
    d.text((1280, 1380), "NA", font=font(90), fill=(255, 255, 255), anchor="mm")
    d.text((600, 1450), code, font=font(80), fill=(50, 56, 68))


RENDER = {k[2:]: v for k, v in globals().items() if k.startswith("r_")}


def render(template, color, code):
    im = canvas()
    d = ImageDraw.Draw(im)
    RENDER[template](im, d, hex2rgb(color), code)
    return im.resize((1024, 1024), Image.LANCZOS)


def save_jpg(im, path, maxpx=1024):
    im = im.convert("RGB")
    im.thumbnail((maxpx, maxpx), Image.LANCZOS)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, "JPEG", quality=85, optimize=True, progressive=True)


def logo(path, text, initials, color, shape="circle", size=512):
    s = size * 2
    im = Image.new("RGBA", (s, s), (255, 255, 255, 0))
    d = ImageDraw.Draw(im)
    c = hex2rgb(color)
    if shape == "circle":
        d.ellipse((40, 40, s - 40, s - 40), fill=c)
    elif shape == "square":
        d.rounded_rectangle((40, 40, s - 40, s - 40), radius=160, fill=c)
    elif shape == "shield":
        d.polygon([(80, 80), (s - 80, 80), (s - 80, s * 0.55), (s / 2, s - 60), (80, s * 0.55)], fill=c)
    elif shape == "hex":
        import math
        pts = [(s / 2 + (s / 2 - 50) * math.cos(math.pi / 3 * i + math.pi / 6), s / 2 + (s / 2 - 50) * math.sin(math.pi / 3 * i + math.pi / 6)) for i in range(6)]
        d.polygon(pts, fill=c)
    d.text((s / 2, s / 2 - (40 if text else 0)), initials, font=font(int(s * 0.34)), fill=(255, 255, 255), anchor="mm")
    if text:
        d.text((s / 2, s * 0.74), text, font=font(int(s * 0.07)), fill=(255, 255, 255, 230), anchor="mm")
    im = im.resize((size, size), Image.LANCZOS)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, "PNG", optimize=True)


def company_logo(path):
    W, H = 1600, 480
    im = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    d = ImageDraw.Draw(im)
    navy, teal = (22, 54, 92), (0, 150, 136)
    # flask mark
    d.polygon([(150, 60), (250, 60), (250, 180), (380, 410), (20, 410), (150, 180)], fill=navy)
    d.polygon([(95, 290), (305, 290), (365, 395), (35, 395)], fill=teal)
    d.rectangle((135, 40, 265, 80), fill=navy)
    d.text((440, 110), "Northbrook", font=font(170), fill=navy)
    d.text((446, 300), "ANALYTICAL", font=font(92, False), fill=teal)
    im = im.resize((800, 240), Image.LANCZOS)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, "PNG", optimize=True)


def main():
    meta = json.load(open(os.path.join(DL, "meta.json")))
    used = {}
    crops = {"oven_02.jpg": (0, 0, 1.0, 0.86)}
    for p in D.PRODUCTS:
        out = os.path.join(IMG, "products", p["key"] + ".jpg")
        if p["image"].startswith("r:"):
            _r, tpl, col = p["image"].split(":")
            save_jpg(render(tpl, col, p["code"]), out)
        else:
            src = p["image"] + ".jpg"
            im = Image.open(os.path.join(DL, src))
            im.verify()
            im = Image.open(os.path.join(DL, src)).convert("RGB")
            if src in crops:
                x0, y0, x1, y1 = crops[src]
                w, h = im.size
                im = im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))
            save_jpg(im, out)
            used.setdefault(src, []).append("products/%s.jpg" % p["key"])
    # website / misc photos
    for src, dst in (("lab_01.jpg", "misc/food_testing_lab.jpg"), ("scrubber_03.jpg", "misc/lab_fume_hood.jpg")):
        im = Image.open(os.path.join(DL, src)).convert("RGB")
        save_jpg(im, os.path.join(IMG, dst))
        used.setdefault(src, []).append(dst)

    company_logo(os.path.join(IMG, "company", "northbrook_logo.png"))
    logo(os.path.join(MOD, "static", "description", "icon.png"), "", "NA", "#16365c", "square", 256)

    colors = ["#1f6f8b", "#8b1f41", "#2f855a", "#b7791f", "#553c9a", "#2c5282", "#c05621", "#276749",
              "#744210", "#2b6cb0", "#97266d", "#285e61", "#9c4221", "#434190", "#22543d", "#702459"]
    shapes = ["circle", "square", "shield", "hex"]
    for i, c in enumerate(D.CUSTOMERS):
        name = c[1]
        words = [w for w in name.replace("-", " ").split() if w[0].isupper() and w not in ("Ltd", "plc", "Co", "of", "The")]
        initials = "".join(w[0] for w in words[:2])
        generic = {"University", "Department", "School", "County", "West", "Public", "Food"}
        short = next((w for w in words if w not in generic), words[0]).upper()[:11]
        if words[0] == "University" and "of" in name.split():
            initials = "U" + name.split("of ")[1][0]
        logo(os.path.join(IMG, "partners", c[0] + ".png"), short, initials, colors[i % len(colors)], shapes[i % 4])
    for i, v in enumerate(D.VENDORS):
        words = v[1].split()
        logo(os.path.join(IMG, "partners", v[0] + ".png"), words[0].upper()[:11], words[0][:2].upper(),
             colors[(i + 5) % len(colors)], shapes[(i + 1) % 4])

    # people (Odoo LGPL demo avatars)
    os.makedirs(os.path.join(IMG, "people"), exist_ok=True)
    for c in D.CUSTOMERS:
        for ct in c[10]:
            if ct[3]:
                shutil.copy(os.path.join(ODOO, "odoo/addons/base/static/img", ct[3] + ".webp"),
                            os.path.join(IMG, "people", ct[3] + ".webp"))
    for e in D.EMPLOYEES:
        shutil.copy(os.path.join(ODOO, "addons/hr/static/img", e[5] + "-image.webp"),
                    os.path.join(IMG, "people", e[5] + ".webp"))

    # attribution
    lines = ["# Image attribution", "",
             "Photographs below are from Wikimedia Commons and are used under the licence stated. "
             "They were resized (max 1024 px) and re-encoded as JPEG; `oven_02` was cropped to remove a manufacturer badge.",
             "", "| File in module | Original | Author | Licence | Source |", "|---|---|---|---|---|"]
    for src, dsts in sorted(used.items()):
        m = meta[src]
        author = " ".join(m["author"].split()).replace("|", "/")
        lines.append("| %s | %s | %s | %s | %s |" % (", ".join(dsts), m["title"].replace("|", "/"), author or "unknown",
                                                    m["license"], m["source"]))
    lines += ["", "Product renders (all other `products/*.jpg`), company/partner logos and the module icon were generated "
              "programmatically with Pillow for this module and carry no third-party rights.", "",
              "People avatars in `people/` are copied from Odoo's LGPL-3 demo data "
              "(`odoo/addons/base/static/img/res_partner_address_*.webp`, `addons/hr/static/img/employee_*-image.webp`).", ""]
    with open(os.path.join(IMG, "ATTRIBUTION.md"), "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
