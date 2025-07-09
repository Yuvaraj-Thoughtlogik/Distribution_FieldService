from odoo import models, fields, api
from odoo.tools.float_utils import float_round

class SaleOrderOption(models.Model):
    _inherit = 'sale.order.option'


    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='order_id.currency_id',
        store=True,
        readonly=True
    )

    total_price = fields.Monetary(
        string='Total Price',
        compute='_compute_total_price',
        store=True,
        currency_field='currency_id',
    )


    @api.depends('price_unit', 'quantity', 'discount')
    def _compute_total_price(self):
        for rec in self:
            discount_factor = (1 - (rec.discount or 0.0) / 100)
            total = rec.price_unit * rec.quantity * discount_factor
            rec.total_price = float_round(total, precision_rounding=rec.currency_id.rounding)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    order_line_total_price = fields.Monetary(
        string='Total Price',
        compute='_compute_order_line_total_price',
        store=True,
        currency_field='currency_id',
        readonly=True,
    )

    @api.depends('price_unit', 'product_uom_qty', 'discount')
    def _compute_order_line_total_price(self):
        for line in self:
            discount_factor = (1 - (line.discount or 0.0) / 100)
            total = line.price_unit * line.product_uom_qty * discount_factor
            line.order_line_total_price = float_round(total, precision_rounding=line.currency_id.rounding)
