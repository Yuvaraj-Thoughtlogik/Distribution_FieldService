from odoo import api, fields, models


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    product_sales_price = fields.Monetary(
        string="Sales Price",
        compute="_compute_rule_unit_prices",
        currency_field="currency_id",
        help="Sales price on the product, in the pricelist currency.",
    )
    pricelist_unit_price = fields.Monetary(
        string="Pricelist Price",
        compute="_compute_rule_unit_prices",
        currency_field="currency_id",
        help="Unit price this rule gives for the product (at its minimum quantity).",
    )

    @api.depends(
        "applied_on", "product_tmpl_id.list_price", "product_id.lst_price", "compute_price",
        "fixed_price", "price_discount", "price_markup", "price_surcharge", "price_round",
        "base", "base_pricelist_id", "min_quantity", "currency_id",
    )
    def _compute_rule_unit_prices(self):
        for item in self:
            product = (item.product_id if item.applied_on == "0_product_variant"
                       else item.product_tmpl_id if item.applied_on == "1_product"
                       else None)
            if not product:
                item.product_sales_price = item.pricelist_unit_price = False
                continue
            currency = item.currency_id or item.env.company.currency_id
            sales_price = product.lst_price if product._name == "product.product" else product.list_price
            item.product_sales_price = product.currency_id._convert(
                sales_price, currency, item.env.company, fields.Date.today())
            item.pricelist_unit_price = item._compute_price(
                product, max(item.min_quantity, 1.0), product.uom_id, currency=currency)
