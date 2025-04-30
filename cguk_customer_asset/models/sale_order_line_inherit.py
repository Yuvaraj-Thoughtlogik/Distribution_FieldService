from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    track_cpe = fields.Boolean(string='Track CPE')

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            for line in order.order_line:
                if line.track_cpe:
                    self.env['customer.asset'].create({
                        'product_id': line.product_id.id,
                        'sale_date': order.date_order,
                        'company_id': order.company_id.id,
                        'contact_id': order.partner_id.id,
                        'subscription_id':order.id,
                        'address': order.partner_shipping_id.contact_address,
                    })
        return res
