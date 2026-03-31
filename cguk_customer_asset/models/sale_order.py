from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _timesheet_create_project_prepare_values(self):

        res = super()._timesheet_create_project_prepare_values()
        res['name'] = '%s - %s' % (self.order_id.client_order_ref, self.order_id.name) if self.order_id.client_order_ref else self.order_id.name
        return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    parent_company = fields.Many2one(string='Parent Company', related='partner_id.parent_id')
    sale_customer_assets_ids = fields.One2many(
        comodel_name="customer.asset",
        string="Customer Assets",
        inverse_name="sale_order_id",
    )
    subscription_customer_assets_ids = fields.Many2many(
        comodel_name="customer.asset",
        string="Customer Assets",
        domain="['|',('partner_id', '=', partner_id),('contact_id', '=', partner_id),('delivery_address_id', '=', partner_shipping_id)]"
    )


    renewal_date = fields.Date(string="Renewal Date")

    sale_customer_assets_count = fields.Integer(string="Customer Assets", compute="_compute_sale_customer_assets_count")
    subscription_customer_assets_count = fields.Integer(string="Customer Assets", compute="_compute_subscription_customer_assets_count")

    @api.depends('sale_customer_assets_ids')
    def _compute_sale_customer_assets_count(self):
        for record in self:
            record.sale_customer_assets_count = len(record.sale_customer_assets_ids)

    @api.depends('subscription_customer_assets_ids')
    def _compute_subscription_customer_assets_count(self):
        for record in self:
            record.subscription_customer_assets_count = len(record.subscription_customer_assets_ids)

    def action_view_subscription_customer_assets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Related Customer Assets',
            'res_model': 'customer.asset',  # replace with actual model
            'view_mode': 'list,form',
            'domain': [('subscription_id', '=', self.id)],  # or use correct relation field
            'target': 'current',
        }
    def action_view_sale_customer_assets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Related Customer Assets',
            'res_model': 'customer.asset',  # replace with actual model
            'view_mode': 'list,form',
            'domain': [('sale_order_id', '=', self.id)],  # or use correct relation field
            'target': 'current',
        }


