"""Generate master-data XML files for tl_dfs_demo_data from dfs_data.py.

python -I gen_xml.py <module_dir>
"""
import os
import sys
from xml.sax.saxutils import escape, quoteattr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dfs_data as D  # noqa: E402

MOD = sys.argv[1]
M = "tl_dfs_demo_data"
HDR = '<?xml version="1.0" encoding="utf-8"?>\n<!-- Generated from master data definitions; edit with care. -->\n<odoo>\n<data noupdate="1">\n'
FTR = "</data>\n</odoo>\n"
COUNTRY = {"uk": "base.uk", "de": "base.de", "it": "base.it", "ch": "base.ch"}


def f(name, value):
    return '    <field name="%s">%s</field>\n' % (name, escape(str(value)))


def fe(name, expr):
    return '    <field name="%s" eval=%s/>\n' % (name, quoteattr(expr))


def fr(name, ref):
    return '    <field name="%s" ref="%s"/>\n' % (name, ref)


def fimg(name, path):
    return '    <field name="%s" type="bytes" file="%s/%s"/>\n' % (name, M, path)


def rec(xid, model, body, extra=""):
    return '<record id="%s" model="%s"%s>\n%s</record>\n' % (xid, model, extra, body)


def write(fname, content):
    path = os.path.join(MOD, "data", fname)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(HDR + content + FTR)


def valid_vat(cc, seed):
    """Deterministic fictional VAT number that passes the python-stdnum checksum."""
    from stdnum import get_cc_module
    mod = get_cc_module(cc, "vat")
    n = seed
    while True:
        n += 1
        cand = {"gb": "GB%09d", "de": "DE%09d", "it": "IT%011d", "ch": "CHE%09dMWST"}[cc] % n
        if mod.is_valid(cand):
            return cand


def gen_partners():
    out = []
    for key, name, color in D.TAGS:
        out.append(rec("partner_tag_" + key, "res.partner.category", f("name", name) + fe("color", str(color))))
    write("res_partner_category_data.xml", "".join(out))

    out = []
    vat_prefix = {"uk": "GB", "de": "DE", "it": "IT", "ch": "CHE"}
    for i, (key, name, street, city, zip_, ctry, email, phone, web) in enumerate(D.VENDORS):
        body = (f("name", name) + f("vat", valid_vat("gb" if ctry == "uk" else ctry, (12345678901 if ctry == "it" else 284516390) + i * 1093457)) + f("street", street) + f("city", city) + f("zip", zip_)
                + fr("country_id", COUNTRY[ctry]) + f("email", email) + f("phone", phone) + f("website", web)
                + fe("supplier_rank", "1") + fe("category_id", "[Command.set([ref('partner_tag_vendor')])]")
                + fimg("image_1920", "static/img/partners/%s.png" % key))
        out.append(rec("partner_vendor_" + key, "res.partner", body))
    write("res_partner_vendor_data.xml", "".join(out))

    out = []
    for i, (key, name, street, city, zip_, tags, phone, domain, pterm, _pl, contacts, deliveries) in enumerate(D.CUSTOMERS):
        body = (f("name", name) + f("vat", valid_vat("gb", 318204557 + i * 2718281)) + f("street", street) + f("city", city) + f("zip", zip_)
                + fr("country_id", "base.uk") + f("phone", phone) + f("email", "info@" + domain)
                + f("website", "https://www." + domain) + fe("customer_rank", "1")
                + fe("category_id", "[Command.set([%s])]" % ", ".join("ref('partner_tag_%s')" % t for t in tags))
                + fr("property_payment_term_id", "payment_term_30eom" if pterm == "30eom" else "account.account_payment_term_30days")
                + fimg("image_1920", "static/img/partners/%s.png" % key))
        out.append(rec("partner_" + key, "res.partner", body))
        for ckey, cname, func, avatar in contacts:
            first = cname.replace("Dr ", "").replace("Prof. ", "").split()
            email = "%s.%s@%s" % (first[0].lower(), first[-1].lower(), domain)
            cb = (f("name", cname) + fr("parent_id", "partner_" + key) + f("function", func) + f("email", email)
                  + f("phone", phone[:-3] + str(100 + len(out))[-3:]) + f("type", "contact"))
            if avatar:
                cb += fimg("image_1920", "static/img/people/%s.webp" % avatar)
            out.append(rec("partner_contact_" + ckey, "res.partner", cb))
        for dkey, dname, dstreet, dcity, dzip in deliveries:
            db = (f("name", dname) + fr("parent_id", "partner_" + key) + f("type", "delivery") + f("street", dstreet)
                  + f("city", dcity) + f("zip", dzip) + fr("country_id", "base.uk"))
            out.append(rec("partner_delivery_" + dkey, "res.partner", db))
    write("res_partner_customer_data.xml", "".join(out))


def gen_products():
    out = []
    parents = {}
    for key, name, parent in D.CATEGORIES:
        body = f("name", name)
        if parent:
            body += fr("parent_id", "product_category_" + parent)
        out.append(rec("product_category_" + key, "product.category", body))
    write("product_category_data.xml", "".join(out))

    first_img = {}
    for p in D.PRODUCTS:
        first_img.setdefault(p["pub"], p["key"])
    out = []
    for key, name, seq in D.PUBLIC_CATEGORIES:
        body = f("name", name) + fe("sequence", str(seq))
        if key in first_img:
            body += fimg("image_1920", "static/img/products/%s.jpg" % first_img[key])
            body += fimg("cover_image", "static/img/products/%s.jpg" % first_img[key])
        out.append(rec("public_category_" + key, "product.public.category", body))
    write("product_public_category_data.xml", "".join(out))

    out = []
    for p in D.PRODUCTS:
        kind = p["kind"]
        goods = kind not in ("service", "sub")
        body = f("name", p["name"]) + f("default_code", p["code"])
        body += f("type", "consu" if goods else "service")
        if goods:
            body += fe("is_storable", "True")
            tracking = {"equip": "serial", "spare_lot": "lot", "consu_exp": "lot"}.get(kind)
            if tracking:
                body += f("tracking", tracking)
            body += f("invoice_policy", "delivery")
            body += fe("weight", repr(p["weight"]))
        else:
            body += f("invoice_policy", "order")
        if kind == "consu_exp":
            days = 1095 if p["key"] == "cat_tabs" else 540
            body += fe("use_expiration_date", "True") + fe("expiration_time", str(days))
            body += fe("use_time", str(days - 60)) + fe("removal_time", str(days - 30)) + fe("alert_time", str(days - 90))
        body += fr("categ_id", "product_category_" + p["categ"])
        body += fe("public_categ_ids", "[Command.set([ref('public_category_%s')])]" % p["pub"])
        body += fe("list_price", repr(float(p["price"]))) + fe("standard_price", repr(float(p["cost"])))
        body += fe("sale_ok", "True") + fe("purchase_ok", "True" if goods else "False")
        body += fe("is_published", "True" if p["published"] else "False")
        body += fe("allow_out_of_stock_order", "True")
        desc = p["desc"] + ((" " + p["warranty"]) if p.get("warranty") else "")
        body += f("description_sale", desc)
        body += fe("description_ecommerce", repr("<p>%s</p>" % escape(desc)))
        if p["uom"]:
            body += fr("uom_id", "uom.product_uom_" + p["uom"])
        if p["role"]:
            body += fr("planning_role_id", "planning_role_" + p["role"])
        if kind == "sub":
            body += fe("recurring_invoice", "True")
        body += fimg("image_1920", "static/img/products/%s.jpg" % p["key"])
        out.append(rec("product_" + p["key"], "product.template", body))
        if p["vendor"]:
            sb = (fr("partner_id", "partner_vendor_" + p["vendor"]) + fr("product_tmpl_id", "product_" + p["key"])
                  + fe("price", repr(float(p["cost"]))) + fe("min_qty", "1.0")
                  + fe("delay", "21" if kind == "equip" else "7") + f("product_code", "V-" + p["code"]))
            out.append(rec("supplierinfo_" + p["key"], "product.supplierinfo", sb))
            if kind in ("consu", "consu_exp"):
                sb2 = (fr("partner_id", "partner_vendor_" + p["vendor"]) + fr("product_tmpl_id", "product_" + p["key"])
                       + fe("price", repr(round(p["cost"] * 0.9, 2))) + fe("min_qty", "10.0") + fe("delay", "7")
                       + f("product_code", "V-" + p["code"]))
                out.append(rec("supplierinfo_%s_10" % p["key"], "product.supplierinfo", sb2))
        if kind == "sub":
            ib = (fr("plan_id", "sale_subscription.subscription_plan_year") + fe("fixed_price", repr(float(p["price"])))
                  + fr("currency_id", "base.GBP") + fr("product_tmpl_id", "product_" + p["key"]))
            out.append(rec("subscription_pricing_" + p["key"], "product.pricelist.item", ib))
    # optional products (second pass, all templates exist now)
    for p in D.PRODUCTS:
        if p["optional"]:
            out.append(rec("product_" + p["key"], "product.template",
                           fe("optional_product_ids", "[Command.set([%s])]" % ", ".join("ref('product_%s')" % o for o in p["optional"]))))
    write("product_data.xml", "".join(out))


def gen_hr():
    out = []
    out.append(rec("resource_calendar_field", "resource.calendar",
                   f("name", "Field Engineers 40 Hours (08:00-17:00)") + fe("hours_per_day", "8.0")
))
    for key, name, parent in D.DEPARTMENTS:
        body = f("name", name)
        if parent:
            body += fr("parent_id", "hr_department_" + parent)
        out.append(rec("hr_department_" + key, "hr.department", body))
    for key, name, dept in D.JOBS:
        out.append(rec("hr_job_" + key, "hr.job", f("name", name) + fr("department_id", "hr_department_" + dept)))
    for (key, name, job, dept, mgr, img, login, roles, drole, cal) in D.EMPLOYEES:
        first, last = name.split()[0], name.split()[-1]
        body = (f("name", name) + fr("job_id", "hr_job_" + job) + f("job_title", dict((j[0], j[1]) for j in D.JOBS)[job])
                + fr("department_id", "hr_department_" + dept)
                + f("work_email", "%s.%s@northbrook-analytical.example" % (first.lower(), last.lower()))
                + f("work_phone", "+44 1908 555 %03d" % (100 + D.EMPLOYEES.index(next(e for e in D.EMPLOYEES if e[0] == key))))
                + fimg("image_1920", "static/img/people/%s.webp" % img))
        if mgr:
            body += fr("parent_id", "hr_employee_" + mgr)
        if cal == "field":
            body += fr("resource_calendar_id", "resource_calendar_field")
        if roles:
            body += fe("planning_role_ids", "[Command.set([%s])]" % ", ".join("ref('planning_role_%s')" % r for r in roles))
        if drole:
            body += fr("default_planning_role_id", "planning_role_" + drole)
        out.append(rec("hr_employee_" + key, "hr.employee", body))
    managers = {"management": "dwhitfield", "sales": "slockwood", "field_service": "gevans", "tech_support": "lchen",
                "warehouse": "kmurray", "finance": "fmacleod"}
    for dept, emp in managers.items():
        out.append(rec("hr_department_" + dept, "hr.department", fr("manager_id", "hr_employee_" + emp)))
    write("hr_data.xml", "".join(out))


if __name__ == "__main__":
    gen_partners()
    gen_products()
    gen_hr()
