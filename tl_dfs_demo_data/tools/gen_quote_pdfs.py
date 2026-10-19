"""Generate the PDF Quote Builder documents for tl_dfs_demo_data.

Usage (from the Odoo venv, reportlab + Pillow required):
    python gen_quote_pdfs.py <module_dir>

Writes static/pdf/*.pdf:
  quote_cover.pdf, quote_about_us.pdf          -> quotation headers
  quote_service_support.pdf, quote_terms.pdf   -> quotation footers
  datasheet_<key>.pdf                          -> product datasheets (one per flagship instrument)

Text boxes named after Odoo's sale.pdf.form.field mappings (name, partner_id__name, order_date,
validity_date, user_id__name, ... / quantity, price_unit, tax_excl_price ...) are filled in by
Odoo when the quotation PDF is printed.
"""
import os
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dfs_data as D  # noqa: E402

MOD = sys.argv[1]
OUT = os.path.join(MOD, "static", "pdf")
IMG = os.path.join(MOD, "static", "img")
LOGO = os.path.join(IMG, "company", "northbrook_logo.png")

W, H = A4
NAVY = colors.HexColor("#16365C")
TEAL = colors.HexColor("#009688")
INK = colors.HexColor("#1F2937")
MUTED = colors.HexColor("#6B7280")
LINE = colors.HexColor("#D9DEE5")
SOFT = colors.HexColor("#F3F6F9")
WHITE = colors.white

COMPANY = {
    "name": "Northbrook Analytical Ltd",
    "address": "Unit 7, Kingston Business Park, Tanners Drive, Milton Keynes MK14 5BN",
    "phone": "+44 1908 555 100",
    "email": "info@northbrook-analytical.example",
    "web": "www.northbrook-analytical.example",
    "reg": "Registered in England & Wales No. 08451276  |  VAT GB123456782",
}
PRODUCTS = {p["key"]: p for p in D.PRODUCTS}


# ------------------------------------------------------------------ helpers
def new_canvas(filename, title):
    c = canvas.Canvas(os.path.join(OUT, filename), pagesize=A4)
    c.setTitle(title)
    c.setAuthor(COMPANY["name"])
    c.setSubject("Quotation document")
    return c


def wrap(c, text, x, y, width, font="Helvetica", size=9.5, leading=None, color=INK):
    """Draw word-wrapped text, return the y below the last line."""
    leading = leading or size * 1.45
    c.setFont(font, size)
    c.setFillColor(color)
    for para in text.split("\n"):
        line = ""
        for word in para.split():
            trial = (line + " " + word).strip()
            if c.stringWidth(trial, font, size) > width:
                c.drawString(x, y, line)
                y -= leading
                line = word
            else:
                line = trial
        if line:
            c.drawString(x, y, line)
            y -= leading
    return y


def field(c, name, x, y, width, height=7 * mm, size=10, on=WHITE, color=INK):
    """Borderless text box, named after an Odoo form-field mapping, filled in when printing.

    Every field uses the same font: reportlab writes a duplicate /Font key in the AcroForm
    resources when fields mix fonts, which PyPDF2 (and so Odoo) refuses to read.
    """
    c.acroForm.textfield(
        name=name, tooltip=name, x=x, y=y, width=width, height=height,
        borderWidth=0, borderColor=on, fillColor=on, textColor=color,
        fontName="Helvetica-Bold", fontSize=size,
        forceBorder=False, maxlen=200,
    )


def logo(c, x, y, height):
    img = ImageReader(LOGO)
    iw, ih = img.getSize()
    c.drawImage(img, x, y, height * iw / ih, height, mask="auto")


def page_footer(c, label, page_no=None, dark=False):
    color = colors.HexColor("#A8B6C8") if dark else MUTED
    c.setStrokeColor(colors.HexColor("#2C4A70") if dark else LINE)
    c.setLineWidth(0.6)
    c.line(18 * mm, 16 * mm, W - 18 * mm, 16 * mm)
    c.setFont("Helvetica", 7.5)
    c.setFillColor(color)
    c.drawString(18 * mm, 11 * mm, f"{COMPANY['name']}  |  {COMPANY['phone']}  |  {COMPANY['email']}  |  {COMPANY['web']}")
    right = label + (f"  |  {page_no}" if page_no else "")
    c.drawRightString(W - 18 * mm, 11 * mm, right)


def band(c, title, kicker):
    """White page + top band used on inner pages."""
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.rect(0, H - 38 * mm, W, 38 * mm, stroke=0, fill=1)
    c.setFillColor(TEAL)
    c.rect(0, H - 39.5 * mm, W, 1.5 * mm, stroke=0, fill=1)
    c.setFillColor(colors.HexColor("#7FD3C9"))
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(18 * mm, H - 15 * mm, kicker.upper())
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(18 * mm, H - 27 * mm, title)
    # white logo plate on the right
    c.setFillColor(WHITE)
    c.roundRect(W - 70 * mm, H - 30 * mm, 52 * mm, 17 * mm, 2 * mm, stroke=0, fill=1)
    logo(c, W - 67 * mm, H - 27.5 * mm, 12 * mm)


def section_title(c, x, y, text):
    c.setFillColor(TEAL)
    c.rect(x, y - 1, 3, 11, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x + 8, y, text)
    return y - 7 * mm


def photo(c, key, x, y, w, h):
    path = os.path.join(IMG, "products", f"{key}.jpg")
    img = ImageReader(path)
    iw, ih = img.getSize()
    # cover-crop into the box
    scale = max(w / iw, h / ih)
    dw, dh = iw * scale, ih * scale
    c.saveState()
    p = c.beginPath()
    p.roundRect(x, y, w, h, 3 * mm)
    c.clipPath(p, stroke=0, fill=0)
    c.drawImage(img, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh)
    c.restoreState()


# ------------------------------------------------------------------ headers
def cover():
    c = new_canvas("quote_cover.pdf", "Quotation - Cover")
    c.setFillColor(NAVY)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    # hero photo on the upper half
    photo(c, "fx6", 0, H * 0.47, W, H * 0.53)
    c.setFillColor(NAVY)
    c.setFillAlpha(0.55)
    c.rect(0, H * 0.47, W, H * 0.53, stroke=0, fill=1)
    c.setFillAlpha(1)
    c.setFillColor(TEAL)
    c.rect(0, H * 0.47 - 2 * mm, W, 2 * mm, stroke=0, fill=1)

    c.setFillColor(WHITE)
    c.roundRect(18 * mm, H - 38 * mm, 62 * mm, 20 * mm, 2 * mm, stroke=0, fill=1)
    logo(c, 21 * mm, H - 35 * mm, 14 * mm)

    c.setFillColor(colors.HexColor("#7FD3C9"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(18 * mm, H * 0.47 + 42 * mm, "FOOD TESTING & LABORATORY EQUIPMENT")
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 40)
    c.drawString(18 * mm, H * 0.47 + 24 * mm, "Quotation")
    c.setFont("Helvetica", 12)
    c.drawString(18 * mm, H * 0.47 + 14 * mm, "Supply, installation and lifetime support of analytical instruments")

    # details card
    top = H * 0.47 - 18 * mm
    c.setFillColor(WHITE)
    c.roundRect(18 * mm, top - 92 * mm, W - 36 * mm, 92 * mm, 3 * mm, stroke=0, fill=1)
    rows = [
        ("Prepared for", "partner_id__name", True),
        ("Quotation reference", "name", True),
        ("Your reference", "client_order_ref", False),
        ("Date issued", "order_date", False),
        ("Valid until", "validity_date", False),
        ("Your account manager", "user_id__name", False),
        ("Contact e-mail", "user_id__email", False),
    ]
    y = top - 14 * mm
    for label, fname, bold in rows:
        c.setFont("Helvetica", 9)
        c.setFillColor(MUTED)
        c.drawString(26 * mm, y + 2 * mm, label.upper())
        field(c, fname, 78 * mm, y, W - 104 * mm, 8 * mm, size=12 if bold else 10.5, color=INK if bold else NAVY)
        c.setStrokeColor(LINE)
        c.setLineWidth(0.5)
        c.line(26 * mm, y - 2.5 * mm, W - 26 * mm, y - 2.5 * mm)
        y -= 11.5 * mm

    c.setFillColor(colors.HexColor("#A8B6C8"))
    c.setFont("Helvetica", 8)
    c.drawString(18 * mm, 24 * mm, COMPANY["address"])
    c.drawString(18 * mm, 19 * mm, f"{COMPANY['phone']}  |  {COMPANY['email']}  |  {COMPANY['web']}")
    c.drawString(18 * mm, 14 * mm, COMPANY["reg"])
    c.showPage()
    c.save()


def about_us():
    c = new_canvas("quote_about_us.pdf", "Quotation - About Northbrook Analytical")
    band(c, "Why Northbrook Analytical", "About us")
    y = H - 54 * mm
    y = wrap(c, (
        "For more than 25 years Northbrook Analytical has helped UK food producers, contract laboratories, "
        "universities and public analysts get reliable results from their laboratory instruments. We are not just a "
        "reseller: our own factory-trained engineers install, validate, calibrate and repair every instrument we supply, "
        "so you deal with one partner for the whole life of the equipment."), 18 * mm, y, W - 36 * mm, size=10.5)

    # key figures
    y -= 6 * mm
    stats = [("25+", "years supporting UK labs"), ("1,800", "instruments under service"),
             ("48 h", "typical engineer response"), ("ISO 17025", "traceable calibration")]
    bw = (W - 36 * mm - 3 * 4 * mm) / 4
    for i, (big, small) in enumerate(stats):
        x = 18 * mm + i * (bw + 4 * mm)
        c.setFillColor(SOFT)
        c.roundRect(x, y - 22 * mm, bw, 22 * mm, 2 * mm, stroke=0, fill=1)
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 17)
        c.drawCentredString(x + bw / 2, y - 11 * mm, big)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 8)
        c.drawCentredString(x + bw / 2, y - 17 * mm, small)
    y -= 32 * mm

    col_w = (W - 36 * mm - 8 * mm) / 2
    left = [
        ("One partner, whole lifecycle", "Application advice, supply, installation & commissioning, IQ/OQ "
         "documentation, operator training, calibration and repair - all from one team."),
        ("Engineers across the UK", "Field engineers based in the South East, Midlands, North and Scotland "
         "keep travel time short and first-time-fix rates high."),
        ("Spares held in Milton Keynes", "Over 1,200 spare-part lines held in stock for next-day dispatch, "
         "with serial-number traceability on every instrument we deliver."),
    ]
    right = [
        ("Application expertise", "Protein (Kjeldahl & Dumas), fat extraction, fibre, moisture and sample "
         "preparation for dairy, meat, cereals, beverages and contract testing."),
        ("Accredited calibration", "Calibration certificates traceable to national standards, aligned with "
         "ISO/IEC 17025 and your UKAS audit requirements."),
        ("Transparent service plans", "Silver and Gold service contracts with guaranteed response times, "
         "included preventive maintenance and discounted parts."),
    ]
    for col, items in ((0, left), (1, right)):
        x = 18 * mm + col * (col_w + 8 * mm)
        yy = y
        for head, body in items:
            c.setFillColor(TEAL)
            c.circle(x + 2.2 * mm, yy + 1.2 * mm, 1.6 * mm, stroke=0, fill=1)
            c.setFillColor(NAVY)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x + 7 * mm, yy, head)
            yy = wrap(c, body, x + 7 * mm, yy - 5.5 * mm, col_w - 7 * mm, size=9.5) - 6 * mm
    y = yy - 2 * mm

    y = section_title(c, 18 * mm, y, "Industries we serve")
    inds = ["Dairy", "Meat & fish", "Cereals & bakery", "Beverages & brewing", "Contract laboratories",
            "Universities & research", "Public analysts", "Animal feed"]
    x = 18 * mm
    c.setFont("Helvetica-Bold", 9)
    for name in inds:
        tw = c.stringWidth(name, "Helvetica-Bold", 9) + 8 * mm
        if x + tw > W - 18 * mm:
            x = 18 * mm
            y -= 10 * mm
        c.setFillColor(colors.HexColor("#E0F2F1"))
        c.roundRect(x, y - 2.5 * mm, tw, 7.5 * mm, 3.7 * mm, stroke=0, fill=1)
        c.setFillColor(colors.HexColor("#00695C"))
        c.drawCentredString(x + tw / 2, y, name)
        x += tw + 3 * mm
    y -= 16 * mm

    # testimonial
    c.setFillColor(SOFT)
    c.roundRect(18 * mm, y - 30 * mm, W - 36 * mm, 32 * mm, 3 * mm, stroke=0, fill=1)
    c.setFillColor(TEAL)
    c.setFont("Helvetica-Bold", 34)
    c.drawString(23 * mm, y - 12 * mm, "“")
    wrap(c, ("Northbrook installed and validated our new Kjeldahl line in two days and trained the whole shift. "
             "Two years on, calibration visits are booked before we even ask."),
         35 * mm, y - 8 * mm, W - 60 * mm, font="Helvetica-Oblique", size=10.5)
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(NAVY)
    c.drawString(35 * mm, y - 25 * mm, "QA Laboratory Manager, UK dairy co-operative")
    page_footer(c, "About us")
    c.showPage()
    c.save()


# ------------------------------------------------------------------ footers
def service_support():
    c = new_canvas("quote_service_support.pdf", "Quotation - Installation, Warranty & Service")
    band(c, "Installation, warranty & service", "After the order")
    y = H - 54 * mm
    y = section_title(c, 18 * mm, y, "From order to first result")
    steps = [("1", "Order confirmed", "Delivery slot agreed; pre-installation checklist sent (services, bench space)."),
             ("2", "Delivery", "Serial-numbered instruments delivered by our own crew or specialist courier."),
             ("3", "Installation & IQ/OQ", "Engineer installs, commissions and documents IQ/OQ on site."),
             ("4", "Training", "Operator training and hand-over of method files and certificates."),
             ("5", "Lifetime support", "Warranty, calibration reminders and service plan start automatically.")]
    sw = (W - 36 * mm - 4 * 3 * mm) / 5
    for i, (num, head, body) in enumerate(steps):
        x = 18 * mm + i * (sw + 3 * mm)
        c.setFillColor(SOFT)
        c.roundRect(x, y - 44 * mm, sw, 46 * mm, 2 * mm, stroke=0, fill=1)
        c.setFillColor(TEAL)
        c.circle(x + 7 * mm, y - 5 * mm, 4.2 * mm, stroke=0, fill=1)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(x + 7 * mm, y - 6.6 * mm, num)
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 9.5)
        c.drawString(x + 3 * mm, y - 15 * mm, head)
        wrap(c, body, x + 3 * mm, y - 21 * mm, sw - 6 * mm, size=8, leading=11)
    y -= 56 * mm

    y = section_title(c, 18 * mm, y, "Warranty")
    y = wrap(c, ("New instruments carry the warranty shown on each product line: 24 months on-site (parts and labour) "
                 "when installed by Northbrook engineers, otherwise 12 months return-to-base. Extended warranty can be "
                 "added at any time during the first year. Consumables, glassware and wear parts are excluded."),
             18 * mm, y, W - 36 * mm, size=9.5) - 6 * mm

    y = section_title(c, 18 * mm, y, "Service plans")
    cols = ["", "Pay as you go", "Silver", "Gold"]
    rows = [("Engineer response (working days)", "Best effort", "3 days", "48 hours"),
            ("Preventive maintenance visits / year", "-", "1", "2"),
            ("Calibration with certificate", "Chargeable", "Included", "Included"),
            ("Labour & travel on breakdown", "Chargeable", "Included", "Included"),
            ("Parts discount", "-", "10 %", "20 %"),
            ("Loan instrument if not fixed on site", "-", "-", "Included"),
            ("Annual price per instrument (ex VAT)", "Visit from GBP 495", "GBP 1,450", "GBP 2,400")]
    widths = [70 * mm, 34 * mm, 34 * mm, W - 36 * mm - 138 * mm]
    row_h = 8.5 * mm
    x0 = 18 * mm
    c.setFillColor(NAVY)
    c.rect(x0, y - row_h + 2 * mm, sum(widths), row_h, stroke=0, fill=1)
    x = x0
    for i, col in enumerate(cols):
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 9.5)
        if i:
            c.drawCentredString(x + widths[i] / 2, y - 3.5 * mm, col)
        x += widths[i]
    y -= row_h
    for r, row in enumerate(rows):
        if r % 2 == 0:
            c.setFillColor(SOFT)
            c.rect(x0, y - row_h + 2 * mm, sum(widths), row_h, stroke=0, fill=1)
        x = x0
        for i, val in enumerate(row):
            c.setFillColor(INK if i == 0 else (TEAL if val == "Included" else INK))
            c.setFont("Helvetica-Bold" if (i == 3 or r == len(rows) - 1) else "Helvetica", 9)
            if i == 0:
                c.drawString(x + 3 * mm, y - 3.5 * mm, val)
            else:
                c.drawCentredString(x + widths[i] / 2, y - 3.5 * mm, val)
            x += widths[i]
        y -= row_h
    y -= 8 * mm

    y = section_title(c, 18 * mm, y, "Getting help")
    wrap(c, ("Technical Support: support@northbrook-analytical.example  |  +44 1908 555 120  |  Mon-Fri 08:00-17:30.\n"
             "Log a ticket 24/7 on our website support page - quote the instrument serial number shown on your "
             "delivery note and asset register for the fastest response."), 18 * mm, y, W - 36 * mm, size=9.5)
    page_footer(c, "Installation, warranty & service")
    c.showPage()
    c.save()


TERMS = [
    ("1. Definitions", "\"We\", \"us\" means Northbrook Analytical Ltd. \"You\" means the customer named on the quotation. "
     "\"Goods\" means instruments, spares and consumables; \"Services\" means installation, training, calibration, "
     "maintenance and repair."),
    ("2. Quotations", "Quotations are valid until the date shown and are based on the quantities quoted. Prices are in "
     "pounds sterling and exclude VAT, which is charged at the prevailing rate."),
    ("3. Orders", "A contract is formed when we confirm your purchase order or signed quotation in writing. Changes "
     "after confirmation may affect price and delivery."),
    ("4. Delivery", "Delivery dates are estimates. Goods are delivered DAP to your UK site unless stated otherwise. "
     "Please inspect deliveries and report damage or shortages within 3 working days."),
    ("5. Installation", "Where installation is quoted you will provide the services listed in our pre-installation "
     "checklist. Delays caused by an unprepared site may be charged at our standard day rate."),
    ("6. Payment", "Payment is due 30 days from the end of the month of invoice unless other terms are agreed. We may "
     "charge interest on overdue sums under the Late Payment of Commercial Debts (Interest) Act 1998."),
    ("7. Title and risk", "Risk passes on delivery. Title to the Goods remains with us until we have received payment "
     "in full."),
    ("8. Warranty", "We warrant that Goods will be free from defects in materials and workmanship for the period stated "
     "on the quotation. The warranty does not cover misuse, consumables, wear parts or unauthorised repair."),
    ("9. Service contracts", "Service contracts run for 12 months from the start date and renew automatically unless "
     "either party gives 30 days' written notice before the renewal date."),
    ("10. Liability", "Our total liability is limited to the price of the Goods or Services concerned. We are not liable "
     "for loss of profit, loss of data or indirect loss. Nothing limits liability for death or personal injury caused "
     "by negligence."),
    ("11. Returns", "Standard stock items may be returned unused within 14 days with our prior authorisation, subject to "
     "a 15 % restocking charge. Special-order items cannot be returned."),
    ("12. Data protection", "We process personal data in accordance with UK GDPR and our privacy notice, available on "
     "our website."),
    ("13. Governing law", "These terms are governed by the laws of England and Wales and the courts of England have "
     "exclusive jurisdiction."),
]


def terms():
    c = new_canvas("quote_terms.pdf", "Quotation - Terms & Acceptance")
    band(c, "Terms of sale & acceptance", "The small print")
    col_w = (W - 36 * mm - 8 * mm) / 2
    y_start = H - 52 * mm
    x, y = 18 * mm, y_start
    bottom = 104 * mm
    for head, body in TERMS:
        needed = 5 * mm + 4.2 * mm * (len(body) * 4.6 / (col_w / mm * 2.83))  # rough estimate
        if y - needed < bottom and x == 18 * mm:
            x, y = 18 * mm + col_w + 8 * mm, y_start
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x, y, head)
        y = wrap(c, body, x, y - 4.5 * mm, col_w, size=8, leading=10.8) - 3 * mm

    # acceptance block
    top = 96 * mm
    c.setFillColor(SOFT)
    c.roundRect(18 * mm, 22 * mm, W - 36 * mm, top - 22 * mm, 3 * mm, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(24 * mm, top - 9 * mm, "Acceptance of quotation")
    c.setFont("Helvetica", 8.5)
    c.setFillColor(MUTED)
    c.drawString(24 * mm, top - 15 * mm,
                 "Sign online from the link in our e-mail, or sign below and return with your purchase order.")
    half = (W - 48 * mm) / 2
    # (label, field, column, row): the customer name gets the full width.
    cells = [("Customer", "partner_id__name", 0, 0, W - 48 * mm),
             ("Quotation", "name", 0, 1, half), ("Total excl. VAT", "amount_untaxed", 1, 1, half),
             ("Total incl. VAT", "amount_total", 1, 2, half)]
    yy = top - 25 * mm
    for label, fname, col, row, width in cells:
        xx = 24 * mm + col * half
        y_row = yy - row * 10 * mm
        c.setFont("Helvetica", 8)
        c.setFillColor(MUTED)
        c.drawString(xx, y_row + 2 * mm, label.upper())
        field(c, fname, xx + 30 * mm, y_row, width - 34 * mm, 7 * mm, size=10, on=SOFT)
    yy -= 2 * 10 * mm
    yy -= 16 * mm
    sig_w = (W - 48 * mm - 16 * mm) / 3
    for i, label in enumerate(("Name", "Signature", "Date")):
        xx = 24 * mm + i * (sig_w + 8 * mm)
        c.setStrokeColor(INK)
        c.setLineWidth(0.6)
        c.line(xx, yy, xx + sig_w, yy)
        c.setFont("Helvetica", 8)
        c.setFillColor(MUTED)
        c.drawString(xx, yy - 4 * mm, label.upper())
    page_footer(c, "Terms of sale")
    c.showPage()
    c.save()


# ------------------------------------------------------------------ product datasheets
DATASHEETS = {
    "kd40": [("Method", "Steam distillation + colorimetric titration"), ("Distillation time", "< 4 min / sample"),
             ("Recovery", ">= 99.5 %"), ("Detection range", "0.1 - 200 mg N"), ("Reagent dosing", "NaOH, H3BO3, water - automatic"),
             ("Data", "Touch screen, USB, LIMS export"), ("Power", "230 V, 2.3 kW"), ("Dimensions (WxDxH)", "440 x 520 x 780 mm")],
    "kd20": [("Method", "Steam distillation"), ("Distillation time", "4 - 6 min / sample"), ("Recovery", ">= 99.5 %"),
             ("Reagent dosing", "Programmable NaOH"), ("Safety", "Door interlock, tube sensor"), ("Power", "230 V, 2.1 kW"),
             ("Dimensions (WxDxH)", "400 x 450 x 760 mm")],
    "dn100": [("Method", "Dumas combustion, TCD detection"), ("Analysis time", "< 4 min"), ("Sample weight", "Up to 1 g organic"),
              ("Autosampler", "120 positions"), ("Carrier gas", "Helium or argon, helium-saving mode"),
              ("Repeatability", "< 0.5 % RSD"), ("Power", "230 V, 3.5 kW"), ("Dimensions (WxDxH)", "650 x 600 x 820 mm")],
    "db20": [("Positions", "20 x 250 mL tubes"), ("Temperature", "Ambient to 420 deg C"), ("Programs", "20 programs, 20 steps"),
             ("Uniformity", "+/- 1 deg C"), ("Lift", "Integrated automatic lift"), ("Power", "230 V, 2.6 kW")],
    "fx6": [("Method", "Soxhlet, hot extraction (Randall), continuous flow"), ("Positions", "6"),
            ("Solvent recovery", "Up to 90 %"), ("Temperature", "Up to 285 deg C"), ("Safety", "Sealed plates, solvent sensor"),
            ("Sample size", "0.5 - 15 g"), ("Power", "230 V, 2.0 kW")],
    "fb6": [("Parameters", "Crude fibre, ADF, NDF"), ("Positions", "6 glass crucibles"),
            ("Extraction", "Hot and cold, automatic reagent pre-heating"), ("Run time", "~ 2 h per batch"),
            ("Power", "230 V, 1.8 kW")],
    "mb120": [("Capacity / readability", "120 g / 1 mg"), ("Temperature range", "40 - 230 deg C"),
              ("Heating", "Halogen lamp"), ("Methods", "100 stored methods"), ("Compliance", "GLP / ISO printout"),
              ("Interface", "USB, RS-232")],
    "rc12": [("Working temperature", "-25 to +150 deg C"), ("Stability", "+/- 0.02 K"), ("Bath volume", "12 L"),
             ("Cooling capacity", "0.5 kW at 20 deg C"), ("Pump", "Pressure / suction, 22 L/min"),
             ("Refrigerant", "Natural (R290)")],
}


def datasheet(key):
    p = PRODUCTS[key]
    c = new_canvas(f"datasheet_{key}.pdf", f"Datasheet - {p['name']}")
    band(c, p["code"], "Product datasheet")
    y = H - 50 * mm
    c.setFillColor(NAVY)
    y = wrap(c, p["name"], 18 * mm, y, W - 36 * mm, font="Helvetica-Bold", size=15, leading=19)
    y -= 3 * mm
    ph = 74 * mm
    photo(c, key, 18 * mm, y - ph, 80 * mm, ph)
    tx = 104 * mm
    ty = wrap(c, p["desc"], tx, y - 4 * mm, W - tx - 18 * mm, size=10, leading=14)
    if p.get("warranty"):
        ty -= 3 * mm
        c.setFillColor(colors.HexColor("#E0F2F1"))
        c.roundRect(tx, ty - 12 * mm, W - tx - 18 * mm, 14 * mm, 2 * mm, stroke=0, fill=1)
        wrap(c, "Warranty: " + p["warranty"], tx + 3 * mm, ty - 3.5 * mm, W - tx - 24 * mm,
             font="Helvetica-Bold", size=8.5, leading=11, color=colors.HexColor("#00695C"))
    y = y - ph - 10 * mm

    y = section_title(c, 18 * mm, y, "Key specifications")
    for i, (label, value) in enumerate(DATASHEETS[key]):
        if i % 2 == 0:
            c.setFillColor(SOFT)
            c.rect(18 * mm, y - 2.6 * mm, W - 36 * mm, 7.5 * mm, stroke=0, fill=1)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 9)
        c.drawString(21 * mm, y, label)
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(80 * mm, y, value)
        y -= 7.5 * mm
    y -= 6 * mm

    opts = [PRODUCTS[o] for o in p.get("optional", []) if o in PRODUCTS]
    if opts:
        y = section_title(c, 18 * mm, y, "Recommended accessories & services")
        for o in opts[:7]:
            c.setFillColor(TEAL)
            c.circle(21 * mm, y + 1.1 * mm, 1 * mm, stroke=0, fill=1)
            c.setFillColor(INK)
            c.setFont("Helvetica", 9)
            c.drawString(25 * mm, y, f"{o['name']}")
            c.setFillColor(MUTED)
            c.drawRightString(W - 18 * mm, y, o["code"])
            y -= 6 * mm

    # "your quotation" box filled from the order line
    box_h = 30 * mm
    by = 24 * mm
    c.setFillColor(NAVY)
    c.roundRect(18 * mm, by, W - 36 * mm, box_h, 3 * mm, stroke=0, fill=1)
    c.setFillColor(colors.HexColor("#7FD3C9"))
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(24 * mm, by + box_h - 8 * mm, "YOUR QUOTATION")
    # price_unit / discount are passed through unformatted by Odoo, so show the formatted line totals.
    cells = [("Quotation", "name", 42 * mm), ("Qty", "quantity", 22 * mm), ("Line total (ex VAT)", "tax_excl_price", 50 * mm),
             ("Line total (inc VAT)", "tax_incl_price", 50 * mm)]
    x = 24 * mm
    for label, fname, w in cells:
        c.setFillColor(colors.HexColor("#A8B6C8"))
        c.setFont("Helvetica", 7.5)
        c.drawString(x, by + 13 * mm, label.upper())
        field(c, fname, x - 1, by + 4 * mm, w - 3 * mm, 7.5 * mm, size=11, on=NAVY, color=WHITE)
        x += w
    page_footer(c, f"Datasheet {p['code']}")
    c.showPage()
    c.save()


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    cover()
    about_us()
    service_support()
    terms()
    for k in DATASHEETS:
        datasheet(k)
    print("written:", sorted(os.listdir(OUT)))
