"""Generate the Service Agreement PDF and its Sign template data for tl_dfs_demo_data_custom.

Usage (Odoo venv, reportlab required):
    python gen_sign_contract.py <tl_dfs_demo_data_custom dir> <tl_dfs_demo_data dir> <signature .ttf>

The signature font is Odoo's own La Belle Aurore (web/static/fonts/sign/LaBelleAurore-Regular.ttf).
Northbrook's side is pre-signed in the PDF, so the template only has the Customer role.

Writes:
  static/pdf/service_agreement.pdf  - 3-page agreement (details, terms, signatures)
  data/sign_template_data.xml       - sign.template + sign.items placed on the boxes drawn in the PDF

Item keys match service.contract.line.get_auto_fills() (tl_field_service_customisation), so the
contract details are filled in automatically when a signature request is created from a contract.
"""
import os
import sys
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

MOD, DEMO, SIGNATURE_FONT = sys.argv[1], sys.argv[2], sys.argv[3]
pdfmetrics.registerFont(TTFont("Signature", SIGNATURE_FONT))

# Authorised signatory who pre-signs every agreement for Northbrook.
SIGNATORY = ("David Whitfield", "Managing Director")
PDF = os.path.join(MOD, "static", "pdf", "service_agreement.pdf")
XML = os.path.join(MOD, "data", "sign_template_data.xml")
LOGO = os.path.join(DEMO, "static", "img", "company", "northbrook_logo.png")

W, H = A4
NAVY = colors.HexColor("#16365C")
TEAL = colors.HexColor("#009688")
INK = colors.HexColor("#1F2937")
MUTED = colors.HexColor("#6B7280")
LINE = colors.HexColor("#C9D1DB")
SOFT = colors.HexColor("#F3F6F9")
FIELD = colors.HexColor("#FBFCFD")
WHITE = colors.white

ITEMS = []  # (xml id, page, type, role, name, key, x, y_top, w, h, extra)


def item(xid, page, type_, role, name, x, y_top, w, h, key=None, auto=False, required=True):
    """Register a sign item; x / y_top / w / h in points, y_top measured from the top of the page."""
    ITEMS.append(dict(xid=xid, page=page, type=type_, role=role, name=name, key=key, auto=auto,
                      required=required, x=x, y=y_top, w=w, h=h))


def box(c, x, y_top, w, h, label=None):
    """Field box (bottom-left reportlab coords from a top-based y) with a small caption above it."""
    c.setFillColor(FIELD)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.roundRect(x, H - y_top - h, w, h, 1.5 * mm, stroke=1, fill=1)
    if label:
        c.setFont("Helvetica", 7.5)
        c.setFillColor(MUTED)
        c.drawString(x, H - y_top + 1.8 * mm, label.upper())


def wrap(c, text, x, y, width, font="Helvetica", size=9, leading=None, color=INK):
    leading = leading or size * 1.42
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


def logo(c, x, y, height):
    img = ImageReader(LOGO)
    iw, ih = img.getSize()
    c.drawImage(img, x, y, height * iw / ih, height, mask="auto")


def band(c, title, kicker):
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.rect(0, H - 34 * mm, W, 34 * mm, stroke=0, fill=1)
    c.setFillColor(TEAL)
    c.rect(0, H - 35.5 * mm, W, 1.5 * mm, stroke=0, fill=1)
    c.setFillColor(colors.HexColor("#7FD3C9"))
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(18 * mm, H - 13 * mm, kicker.upper())
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(18 * mm, H - 24 * mm, title)
    c.setFillColor(WHITE)
    c.roundRect(W - 68 * mm, H - 27 * mm, 50 * mm, 16 * mm, 2 * mm, stroke=0, fill=1)
    logo(c, W - 65 * mm, H - 24.5 * mm, 11 * mm)


def heading(c, y_top, text):
    c.setFillColor(TEAL)
    c.rect(18 * mm, H - y_top - 1, 3, 11, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 11.5)
    c.drawString(18 * mm + 8, H - y_top, text)


def footer(c, page, total, initials=True):
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(18 * mm, 18 * mm, W - 18 * mm, 18 * mm)
    c.setFont("Helvetica", 7.5)
    c.setFillColor(MUTED)
    c.drawString(18 * mm, 12 * mm, "Northbrook Analytical Ltd  |  Service Agreement  |  Registered in England & Wales No. 08451276")
    c.drawString(18 * mm, 8 * mm, f"Page {page} of {total}")
    if initials:
        x, y_top, w, h = W - 48 * mm, H - 16 * mm, 30 * mm, 10 * mm
        c.setFont("Helvetica", 7)
        c.drawRightString(x - 2 * mm, H - y_top - 6 * mm, "CUSTOMER INITIALS")
        box(c, x, y_top, w, h)
        item(f"sign_item_sa_initials_p{page}", page, "initial", "customer", "Customer initials", x, y_top, w, h)


def page_details(c):
    band(c, "Service Agreement", "Preventive maintenance & calibration")
    full = W - 36 * mm
    x0 = 18 * mm

    # agreement number
    c.setFont("Helvetica", 9)
    c.setFillColor(INK)
    wrap(c, ("This agreement sets out the planned maintenance, calibration and breakdown support that Northbrook "
             "Analytical Ltd will provide for the laboratory equipment listed below."), x0, H - 47 * mm, full - 70 * mm)
    box(c, W - 78 * mm, 44 * mm, 60 * mm, 9 * mm, "Agreement no.")
    item("sign_item_sa_contract_no", 1, "text", "customer", "Agreement number", W - 76 * mm, 45.5 * mm, 56 * mm, 6 * mm,
         key="service_contract_no", auto=True)

    # 1. parties
    heading(c, 66 * mm, "1. The parties")
    col = (full - 8 * mm) / 2
    c.setFillColor(SOFT)
    c.roundRect(x0, H - 128 * mm, col, 56 * mm, 2 * mm, stroke=0, fill=1)
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 7.5)
    c.drawString(x0 + 5 * mm, H - 79 * mm, "SERVICE PROVIDER")
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x0 + 5 * mm, H - 86 * mm, "Northbrook Analytical Ltd")
    wrap(c, ("Unit 7, Kingston Business Park\nTanners Drive, Milton Keynes\nMK14 5BN, United Kingdom\n"
             "Company No. 08451276  |  VAT GB123456782\nsupport@northbrook-analytical.example\n+44 1908 555 120"),
         x0 + 5 * mm, H - 93 * mm, col - 10 * mm, size=8.5, leading=12)

    cx = x0 + col + 8 * mm
    box(c, cx, 76 * mm, col, 9 * mm, "Customer")
    item("sign_item_sa_customer", 1, "text", "customer", "Customer name", cx + 2 * mm, 77.5 * mm, col - 4 * mm, 6 * mm,
         key="customer_name", auto=True)
    box(c, cx, 94 * mm, col, 34 * mm, "Site / invoice address")
    item("sign_item_sa_address", 1, "textarea", "customer", "Customer address", cx + 2 * mm, 95.5 * mm, col - 4 * mm,
         31 * mm, key="address", auto=True, required=False)

    # 2. term
    heading(c, 142 * mm, "2. Term and service level")
    third = (full - 2 * 6 * mm) / 3
    for i, (label, xid, key, name) in enumerate([
        ("Start date", "sign_item_sa_start", "start_date", "Start date"),
        ("End date", "sign_item_sa_end", "end_date", "End date"),
        ("Planned visits per year", "sign_item_sa_visits", "no_of_services", "Planned visits per year"),
    ]):
        bx = x0 + i * (third + 6 * mm)
        box(c, bx, 152 * mm, third, 9 * mm, label)
        item(xid, 1, "text", "customer", name, bx + 2 * mm, 153.5 * mm, third - 4 * mm, 6 * mm, key=key, auto=True,
             required=key != "no_of_services")
    wrap(c, ("The agreement renews automatically for further 12-month periods unless either party gives 30 days' "
             "written notice before the end date. Response times and inclusions follow the service plan on your "
             "subscription (Silver or Gold) as described in clause 4."), x0, H - 169 * mm, full, size=8.5)

    # 3. equipment
    heading(c, 186 * mm, "3. Equipment covered")
    box(c, x0, 192 * mm, full, 62 * mm)
    item("sign_item_sa_equipment", 1, "textarea", "customer", "Equipment covered", x0 + 2 * mm, 194 * mm, full - 4 * mm,
         58 * mm, key="equipments", auto=True, required=False)
    c.setFont("Helvetica-Oblique", 7.5)
    c.setFillColor(MUTED)
    c.drawString(x0, H - 259 * mm, "Instruments and serial numbers as recorded in the Northbrook asset register on the start date.")
    footer(c, 1, 3)


CLAUSES = [
    ("4. Services included", "Planned preventive maintenance and calibration visits as stated in clause 2, carried out by "
     "Northbrook factory-trained engineers to the manufacturer's procedures, with a service report and calibration "
     "certificate traceable to national standards for each instrument. Gold plans include labour and travel for "
     "breakdowns, a loan instrument where a repair cannot be completed on site, and 20 % off parts; Silver plans include "
     "labour and travel and 10 % off parts."),
    ("5. Response times", "Breakdowns reported to Technical Support (website support form, e-mail or telephone) during "
     "working hours (Mon-Fri 08:00-17:30, excluding UK bank holidays) receive an engineer response within 48 working "
     "hours on Gold plans and 3 working days on Silver plans."),
    ("6. Exclusions", "Consumables, glassware and wear parts; damage caused by misuse, accident, unauthorised repair or "
     "relocation; work outside working hours unless agreed in advance; instruments not listed in clause 3."),
    ("7. Customer obligations", "Provide safe access to the equipment and services (power, water, gases, extraction), "
     "a responsible person on site, and operate the equipment in line with the operating manual. Notify us before "
     "moving, modifying or disposing of any covered instrument."),
    ("8. Charges and payment", "The annual charge is set out on the subscription order and is invoiced annually in "
     "advance. Invoices are payable within 30 days of the end of the month of invoice. Parts and chargeable work are "
     "invoiced on completion."),
    ("9. Changes to equipment", "Instruments may be added to or removed from the agreement at any time by written "
     "agreement; the annual charge is adjusted pro rata."),
    ("10. Liability", "Our total liability under this agreement is limited to the annual charge. We are not liable for "
     "loss of profit, loss of data or samples, or indirect loss. Nothing limits liability for death or personal injury "
     "caused by negligence."),
    ("11. Termination", "Either party may terminate on 30 days' written notice if the other commits a material breach "
     "that is not remedied within that period. Fees paid in advance are not refundable except on our breach."),
    ("12. Data protection and law", "Each party processes personal data in accordance with UK GDPR. This agreement is "
     "governed by the laws of England and Wales, whose courts have exclusive jurisdiction."),
]


def page_terms(c):
    band(c, "Terms of service", "Service Agreement")
    col_w = (W - 36 * mm - 10 * mm) / 2
    x, y = 18 * mm, H - 48 * mm
    for i, (head, body) in enumerate(CLAUSES):
        if i == 5:
            x, y = 18 * mm + col_w + 10 * mm, H - 48 * mm
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 9.5)
        c.drawString(x, y, head)
        y = wrap(c, body, x, y - 5 * mm, col_w, size=8.6, leading=12.4) - 5 * mm
    footer(c, 2, 3)


def panel(c, x, y_top, w, title):
    c.setFillColor(SOFT)
    c.roundRect(x, H - y_top - 92 * mm, w, 92 * mm, 2 * mm, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(x + 5 * mm, H - y_top - 8 * mm, title)
    return w - 10 * mm


def customer_panel(c, x, y_top, w):
    iw = panel(c, x, y_top, w, "Signed for the Customer")
    box(c, x + 5 * mm, y_top + 17 * mm, iw, 30 * mm, "Signature")
    item("sign_item_sa_customer_signature", 3, "signature", "customer", "Signature", x + 7 * mm, y_top + 19 * mm,
         iw - 4 * mm, 26 * mm)
    box(c, x + 5 * mm, y_top + 56 * mm, iw, 9 * mm, "Name and position")
    item("sign_item_sa_customer_name", 3, "text", "customer", "Name and position", x + 7 * mm, y_top + 57.5 * mm,
         iw - 4 * mm, 6 * mm, key="customer_name_job", auto=True)
    box(c, x + 5 * mm, y_top + 74 * mm, iw / 2, 9 * mm, "Date")
    item("sign_item_sa_customer_date", 3, "date", "customer", "Date", x + 7 * mm, y_top + 75.5 * mm, iw / 2 - 4 * mm,
         6 * mm)


def northbrook_panel(c, x, y_top, w):
    """Pre-signed by the authorised signatory: printed signature and name, issue date filled by the system."""
    iw = panel(c, x, y_top, w, "Signed for Northbrook Analytical Ltd")
    box(c, x + 5 * mm, y_top + 17 * mm, iw, 30 * mm, "Signature")
    c.setFillColor(colors.HexColor("#1B2A6B"))
    size = min(30, 30 * (iw - 16 * mm) / pdfmetrics.stringWidth(SIGNATORY[0], "Signature", 30))
    c.setFont("Signature", size)
    c.drawCentredString(x + 5 * mm + iw / 2, H - y_top - 37 * mm, SIGNATORY[0])
    box(c, x + 5 * mm, y_top + 56 * mm, iw, 9 * mm, "Name and position")
    c.setFillColor(INK)
    c.setFont("Helvetica", 10)
    c.drawString(x + 7 * mm, H - y_top - 61.8 * mm, f"{SIGNATORY[0]}, {SIGNATORY[1]}")
    box(c, x + 5 * mm, y_top + 74 * mm, iw / 2, 9 * mm, "Signed and issued")
    item("sign_item_sa_issue_date", 3, "text", "customer", "Issue date", x + 7 * mm, y_top + 75.5 * mm, iw / 2 - 4 * mm,
         6 * mm, key="issue_date", auto=True, required=False)
    c.setFont("Helvetica-Oblique", 7.5)
    c.setFillColor(MUTED)
    c.drawString(x + 5 * mm, H - y_top - 88 * mm, "Pre-signed by our authorised signatory.")


def page_signatures(c):
    band(c, "Signatures", "Service Agreement")
    full = W - 36 * mm
    x0 = 18 * mm
    heading(c, 50 * mm, "13. Agreement")
    wrap(c, ("By signing below, the parties agree to the services and terms set out in this Service Agreement, "
             "including the equipment listed in clause 3 and the terms of service in clauses 4 to 12. The agreement "
             "is pre-signed by Northbrook and takes effect once signed by the Customer; a copy of the completed "
             "document is sent to both parties."),
         x0, H - 58 * mm, full, size=9.5)

    box(c, x0, 80 * mm, 80 * mm, 9 * mm, "Customer purchase order no. (optional)")
    item("sign_item_sa_po", 3, "text", "customer", "Customer PO number", x0 + 2 * mm, 81.5 * mm, 76 * mm, 6 * mm,
         required=False)

    col = (full - 8 * mm) / 2
    customer_panel(c, x0, 100 * mm, col)
    northbrook_panel(c, x0 + col + 8 * mm, 100 * mm, col)
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(MUTED)
    c.drawString(x0, H - 202 * mm, "The completed agreement is stored against your service contract and asset records.")
    footer(c, 3, 3, initials=False)


def build_pdf():
    os.makedirs(os.path.dirname(PDF), exist_ok=True)
    c = canvas.Canvas(PDF, pagesize=A4)
    c.setTitle("Service Agreement - Northbrook Analytical")
    c.setAuthor("Northbrook Analytical Ltd")
    for draw in (page_details, page_terms, page_signatures):
        draw(c)
        c.showPage()
    c.save()


ROLE_REF = {"customer": "tl_field_service_customisation.sign_role_customer"}
TYPE_REF = {"text": "sign.sign_item_type_text", "textarea": "sign.sign_item_type_multiline_text",
            "signature": "sign.sign_item_type_signature", "initial": "sign.sign_item_type_initial",
            "date": "sign.sign_item_type_date"}


def build_xml():
    out = ['<?xml version="1.0" encoding="utf-8"?>',
           "<!-- Generated by tools/gen_sign_contract.py - edit the generator, not this file. -->",
           "<odoo>", '<data noupdate="1">',
           '    <record id="sign_tag_service_contracts" model="sign.template.tag">',
           "        <field name=\"name\">Service Contracts</field>",
           "        <field name=\"color\">10</field>",
           "    </record>",
           '    <record id="attachment_service_agreement" model="ir.attachment">',
           "        <field name=\"name\">Northbrook Service Agreement.pdf</field>",
           '        <field name="raw" type="bytes" file="tl_dfs_demo_data_custom/static/pdf/service_agreement.pdf"/>',
           "        <field name=\"mimetype\">application/pdf</field>",
           "    </record>",
           '    <record id="sign_template_service_agreement" model="sign.template">',
           "        <field name=\"name\">Service Agreement - Maintenance &amp; Calibration</field>",
           "        <field name=\"tag_ids\" eval=\"[Command.set([ref('sign_tag_service_contracts'), ref('sign.sign_template_tag_3')])]\"/>",
           "        <field name=\"redirect_url\">https://www.northbrook-analytical.example</field>",
           "        <field name=\"redirect_url_text\">Visit our website</field>",
           "        <field name=\"message\"><![CDATA[<p>Please review and sign your Northbrook Analytical service agreement. "
           "The equipment covered and the contract dates are filled in for you.</p>]]></field>",
           "    </record>",
           '    <record id="sign_document_service_agreement" model="sign.document">',
           "        <field name=\"attachment_id\" ref=\"attachment_service_agreement\"/>",
           "        <field name=\"template_id\" ref=\"sign_template_service_agreement\"/>",
           "    </record>"]
    for it in ITEMS:
        out += [
            f'    <record id="{it["xid"]}" model="sign.item">',
            '        <field name="document_id" ref="sign_document_service_agreement"/>',
            f'        <field name="type_id" ref="{TYPE_REF[it["type"]]}"/>',
            f'        <field name="responsible_id" ref="{ROLE_REF[it["role"]]}"/>',
            f'        <field name="name">{escape(it["name"])}</field>',
            f'        <field name="page" type="int">{it["page"]}</field>',
            f'        <field name="posX" type="float">{it["x"] / W:.3f}</field>',
            f'        <field name="posY" type="float">{it["y"] / H:.3f}</field>',
            f'        <field name="width" type="float">{it["w"] / W:.3f}</field>',
            f'        <field name="height" type="float">{it["h"] / H:.3f}</field>',
            f'        <field name="required" eval="{it["required"]}"/>',
        ]
        if it["key"]:
            out.append(f'        <field name="key">{it["key"]}</field>')
        if it["auto"]:
            out += ['        <field name="auto_fill" eval="True"/>', '        <field name="by_system" eval="True"/>']
        out.append("    </record>")
    out += ["</data>", "</odoo>", ""]
    os.makedirs(os.path.dirname(XML), exist_ok=True)
    with open(XML, "w") as f:
        f.write("\n".join(out))


if __name__ == "__main__":
    build_pdf()
    build_xml()
    print(f"{PDF}\n{XML}\n{len(ITEMS)} sign items")
