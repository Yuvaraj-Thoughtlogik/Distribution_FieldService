
from odoo import models,fields,api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    description = fields.Text(string="Description")

    @api.onchange('product_template_id')
    def _onchange_get_description(self):
        for rec in self:
            if rec.product_template_id:
                rec.description = rec.product_template_id.description_sale
            else:
                rec.description = ""