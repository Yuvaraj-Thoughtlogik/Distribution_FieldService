from odoo import models
from odoo.http import request


def _website_hides_prices(env):
    """Prices are hidden on the frontend of a quote-only website.

    Backend computations (sale orders, reports, pricelists...) never go through the
    methods overridden below with a frontend request, so internal users keep prices
    in the backend.
    """
    if not request or not getattr(request, "is_frontend", False):
        return False
    if env.context.get("dfs_show_prices"):
        return False
    website = env.website
    return bool(website and website.dfs_quote_mode)


def _strip_offers(vals):
    """Remove schema.org offers (price information) from JSON-LD markup data."""
    if isinstance(vals, dict):
        vals.pop("offers", None)
        for value in vals.values():
            _strip_offers(value)
    elif isinstance(vals, (list, tuple)):
        for value in vals:
            _strip_offers(value)
    return vals


PRICE_KEYS_TO_DROP = (
    "base_unit_price",
    "base_unit_name",
    "packaging_prices",
    "tax_disclaimer",
)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_additional_combination_info(
        self, product_or_template, quantity, uom, website, pricelist, fiscal_position, **kwargs
    ):
        info = super()._get_additional_combination_info(
            product_or_template, quantity, uom, website, pricelist, fiscal_position, **kwargs
        )
        if website and website.dfs_quote_mode and not self.env.context.get("dfs_show_prices"):
            info.update({
                "price": 0.0,
                "list_price": 0.0,
                "raw_pricelist_price": 0.0,
                "compare_list_price": 0.0,
                "has_discounted_price": False,
                "discount_start_date": False,
                "discount_end_date": False,
                "hide_price": True,
                # The product stays requestable (quote), even without price.
                "prevent_sale": False,
            })
            for key in PRICE_KEYS_TO_DROP:
                info.pop(key, None)
        return info

    def _get_sales_prices(self, pricelist_sudo, fiscal_position_sudo, website):
        res = super()._get_sales_prices(pricelist_sudo, fiscal_position_sudo, website)
        if website and website.dfs_quote_mode:
            for vals in res.values():
                vals["price_reduce"] = 0.0
                vals["raw_pricelist_price"] = 0.0
                for key in ("base_price", "base_unit_price"):
                    vals.pop(key, None)
        return res

    def _get_configurator_display_price(
        self, product_or_template, quantity, date, currency, pricelist, **kwargs
    ):
        price, rule_id = super()._get_configurator_display_price(
            product_or_template, quantity, date, currency, pricelist, **kwargs
        )
        if _website_hides_prices(self.env):
            price = 0.0
        return price, rule_id

    def _search_render_results_prices(self, mapping, combination_info):
        if _website_hides_prices(self.env):
            return None
        return super()._search_render_results_prices(mapping, combination_info)

    def _prepare_jsonld_vals(self):
        vals = super()._prepare_jsonld_vals()
        if _website_hides_prices(self.env):
            _strip_offers(vals)
        return vals

    def _get_google_analytics_data(self, product, combination_info):
        data = super()._get_google_analytics_data(product, combination_info)
        if _website_hides_prices(self.env):
            data.pop("price", None)
            data.pop("discount", None)
        return data


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _prepare_jsonld_vals(self, **kwargs):
        vals = super()._prepare_jsonld_vals(**kwargs)
        if _website_hides_prices(self.env):
            _strip_offers(vals)
        return vals
