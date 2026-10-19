import logging

from werkzeug.exceptions import Forbidden, NotFound

from odoo.exceptions import UserError
from odoo.http import request, route
from odoo.tools import email_normalize

from odoo.addons.website_sale.controllers.cart import Cart
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale.controllers.payment import PaymentPortal
from odoo.addons.website_sale.controllers.product_configurator import (
    WebsiteSaleProductConfiguratorController,
)
from odoo.addons.website_sale.controllers.product_feed import ProductFeed

_logger = logging.getLogger(__name__)

QUOTE_FORM_FIELDS = (
    "name", "company", "email", "phone", "street", "city", "zip", "country_id", "notes",
    "reference",
)
QUOTE_REQUIRED_FIELDS = ("name", "company", "email", "phone", "street", "zip")
LAST_QUOTE_SESSION_KEY = "dfs_last_quote_request"


def _quote_mode():
    website = request.env.website
    return bool(website and website.dfs_quote_mode)


class DfsQuoteCart(Cart):
    """The cart becomes the "Quote request" list."""

    @route()
    def cart(self, id=None, access_token=None, **post):
        if not _quote_mode():
            return super().cart(id=id, access_token=access_token, **post)
        if not request.env.website.has_ecommerce_access():
            return request.redirect("/web/login")
        order_sudo = request.cart
        if order_sudo:
            order_sudo.order_line.filtered(
                lambda sol: sol.product_id and not sol.product_id.active
            ).unlink()
        return request.render("tl_dfs_website_quote.quote_cart", {
            "website_sale_order": order_sudo,
            "quote_lines": self._dfs_quote_lines(order_sudo),
            "warning": post.get("warning"),
        })

    @staticmethod
    def _dfs_quote_lines(order_sudo):
        if not order_sudo:
            return request.env["sale.order.line"].sudo()
        # Combo/optional children are listed under their parent line.
        return order_sudo.website_order_line.filtered(lambda line: not line.linked_line_id)

    @route(
        "/shop/quote/update", type="http", auth="public", methods=["POST"], website=True,
        sitemap=False,
    )
    def dfs_quote_update(self, **post):
        order_sudo = request.cart
        if not order_sudo:
            return request.redirect("/shop/cart")
        remove_id = post.get("remove")
        updates = {}
        if remove_id and str(remove_id).isdigit():
            updates[int(remove_id)] = 0
        else:
            for key, value in post.items():
                if not key.startswith("qty_"):
                    continue
                line_id = key[4:]
                if not line_id.isdigit():
                    continue
                try:
                    qty = int(float(value or 0))
                except ValueError:
                    continue
                updates[int(line_id)] = max(qty, 0)
        lines = order_sudo.order_line
        for line_id, qty in updates.items():
            line = lines.filtered(lambda l, lid=line_id: l.id == lid)
            if not line or line.product_uom_qty == qty:
                continue
            try:
                order_sudo._cart_update_line_quantity(line.id, qty)
            except UserError as e:
                return request.redirect("/shop/cart?warning=%s" % e.args[0])
        return request.redirect("/shop/cart")

    @route("/shop/quote/request", type="http", auth="public", website=True, sitemap=False)
    def dfs_quote_request(self, **kwargs):
        order_sudo = request.cart
        if not order_sudo or not order_sudo.website_order_line:
            return request.redirect("/shop/cart")
        return request.render(
            "tl_dfs_website_quote.quote_request_form",
            self._dfs_quote_form_values(order_sudo, self._dfs_prefill_values()),
        )

    def _dfs_prefill_values(self):
        values = {"country_id": request.env.ref("base.uk").id}
        user = request.env.user
        if not user._is_public():
            partner = user.partner_id
            commercial = partner.commercial_partner_id
            values.update({
                "name": partner.name if not partner.is_company else "",
                "company": (
                    commercial.name if commercial != partner or partner.is_company
                    else partner.company_name or ""
                ),
                "email": partner.email or "",
                "phone": partner.phone or "",
                "street": partner.street or "",
                "city": partner.city or "",
                "zip": partner.zip or "",
                "country_id": partner.country_id.id or values["country_id"],
            })
        return values

    def _dfs_quote_form_values(self, order_sudo, form, errors=None):
        return {
            "website_sale_order": order_sudo,
            "quote_lines": self._dfs_quote_lines(order_sudo),
            "form": form,
            "errors": errors or {},
            "countries": request.env["res.country"].sudo().search([]),
            "required_fields": QUOTE_REQUIRED_FIELDS,
        }

    def _dfs_validate_quote_form(self, post):
        form = {key: (post.get(key) or "").strip() for key in QUOTE_FORM_FIELDS}
        errors = {}
        for key in QUOTE_REQUIRED_FIELDS:
            if not form[key]:
                errors[key] = request.env._("This field is required.")
        if form["email"] and not email_normalize(form["email"]):
            errors["email"] = request.env._("Please enter a valid e-mail address.")
        country = False
        if form["country_id"].isdigit():
            country = request.env["res.country"].sudo().browse(int(form["country_id"])).exists()
        form["country_id"] = country.id if country else False
        for key, limit in (("notes", 5000), ("reference", 100)):
            form[key] = form[key][:limit]
        for key in ("name", "company", "email", "phone", "street", "city", "zip"):
            form[key] = form[key][:250]
        return form, errors

    @route(
        "/shop/quote/submit", type="http", auth="public", methods=["POST"], website=True,
        sitemap=False,
    )
    def dfs_quote_submit(self, **post):
        order_sudo = request.cart
        if not order_sudo or not order_sudo.website_order_line:
            return request.redirect("/shop/cart")
        if post.get("website_url"):  # honeypot field, hidden to humans
            return request.redirect("/shop/quote/thank-you")
        form, errors = self._dfs_validate_quote_form(post)
        if errors:
            return request.render(
                "tl_dfs_website_quote.quote_request_form",
                self._dfs_quote_form_values(order_sudo, form, errors),
            )
        visitor = request.env["ir.http"]._get_visitor_from_request().sudo()
        lead = order_sudo._dfs_submit_quote_request(form, visitor=visitor)
        request.session[LAST_QUOTE_SESSION_KEY] = {
            "order_id": order_sudo.id,
            "lead_id": lead.id,
        }
        request.env.website.sale_reset()
        request.session.pop("sale_order_id", None)
        return request.redirect("/shop/quote/thank-you")

    @route("/shop/quote/thank-you", type="http", auth="public", website=True, sitemap=False)
    def dfs_quote_thank_you(self, **kwargs):
        info = request.session.get(LAST_QUOTE_SESSION_KEY) or {}
        order_sudo = request.env["sale.order"].sudo().browse(info.get("order_id")).exists()
        lead_sudo = request.env["crm.lead"].sudo().browse(info.get("lead_id")).exists()
        return request.render("tl_dfs_website_quote.quote_thank_you", {
            "quote_order": order_sudo,
            "quote_lead": lead_sudo,
        })

    # ------------------------------------------------------------------
    # JSON payloads: never leak prices to the browser
    # ------------------------------------------------------------------
    def _get_cart_notification_information(self, order, added_qty_per_line):
        res = super()._get_cart_notification_information(order, added_qty_per_line)
        if _quote_mode():
            for line in res.get("lines", []):
                line["price_total"] = 0.0
        return res

    def _get_updated_cart_page_values(self, order_sudo):
        res = super()._get_updated_cart_page_values(order_sudo)
        if _quote_mode():
            res.update({"amount": 0.0, "minor_amount": 0})
            res.pop("website_sale.total", None)
        return res

    def _get_express_shop_payment_values(self, order, **kwargs):
        if _quote_mode():
            return {}
        return super()._get_express_shop_payment_values(order, **kwargs)


class DfsQuoteWebsiteSale(WebsiteSale):
    """Checkout, address, delivery and payment steps do not exist on a quote-only website."""

    def _dfs_redirect_to_quote(self):
        return request.redirect("/shop/cart")

    @route()
    def shop_checkout(self, try_skip_step=None, **query_params):
        if _quote_mode():
            return self._dfs_redirect_to_quote()
        return super().shop_checkout(try_skip_step=try_skip_step, **query_params)

    @route()
    def shop_address(self, *args, **kwargs):
        if _quote_mode():
            return self._dfs_redirect_to_quote()
        return super().shop_address(*args, **kwargs)

    @route()
    def shop_address_submit(self, *args, **kwargs):
        if _quote_mode():
            raise Forbidden()
        return super().shop_address_submit(*args, **kwargs)

    @route()
    def process_express_checkout(self, *args, **kwargs):
        if _quote_mode():
            raise Forbidden()
        return super().process_express_checkout(*args, **kwargs)

    @route()
    def shop_update_address(self, *args, **kwargs):
        if _quote_mode():
            raise Forbidden()
        return super().shop_update_address(*args, **kwargs)

    @route()
    def extra_info(self, **post):
        if _quote_mode():
            return self._dfs_redirect_to_quote()
        return super().extra_info(**post)

    @route()
    def shop_payment(self, **post):
        if _quote_mode():
            return self._dfs_redirect_to_quote()
        return super().shop_payment(**post)

    @route()
    def shop_payment_validate(self, *args, **kwargs):
        if _quote_mode():
            return self._dfs_redirect_to_quote()
        return super().shop_payment_validate(*args, **kwargs)

    @route()
    def shop_payment_confirmation(self, **post):
        if _quote_mode():
            return request.redirect("/shop/quote/thank-you")
        return super().shop_payment_confirmation(**post)

    @route()
    def print_saleorder(self, **kwargs):
        if _quote_mode():
            raise NotFound()
        return super().print_saleorder(**kwargs)

    @route()
    def pricelist_change(self, *args, **kwargs):
        if _quote_mode():
            return request.redirect("/shop")
        return super().pricelist_change(*args, **kwargs)

    @route()
    def pricelist(self, *args, **kwargs):
        if _quote_mode():
            return request.redirect("/shop/cart")
        return super().pricelist(*args, **kwargs)

    def _get_search_order(self, post):
        order = super()._get_search_order(post)
        if _quote_mode() and "list_price" in (order or ""):
            order = "is_published desc, website_sequence asc, id desc"
        return order


class DfsQuotePaymentPortal(PaymentPortal):
    @route()
    def shop_payment_transaction(self, *args, **kwargs):
        if _quote_mode():
            raise Forbidden()
        return super().shop_payment_transaction(*args, **kwargs)


class DfsQuoteProductConfigurator(WebsiteSaleProductConfiguratorController):
    def _get_basic_product_information(self, product_or_template, pricelist, combination,
                                       **kwargs):
        info = super()._get_basic_product_information(
            product_or_template, pricelist, combination, **kwargs
        )
        if request.is_frontend and _quote_mode():
            info["price"] = 0.0
            for key in ("strikethrough_price", "base_unit_price", "base_unit_name", "price_info"):
                info.pop(key, None)
        return info

    def _get_ptav_price_extra(self, ptav, currency, date, product_or_template):
        if request.is_frontend and _quote_mode():
            return 0.0
        return super()._get_ptav_price_extra(ptav, currency, date, product_or_template)


class DfsQuoteProductFeed(ProductFeed):
    @route()
    def gmc_feed(self, *args, **kwargs):
        if _quote_mode():
            raise NotFound()
        return super().gmc_feed(*args, **kwargs)
