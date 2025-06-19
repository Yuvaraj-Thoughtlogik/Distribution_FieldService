from odoo import models, fields, api

class RepairOrder(models.Model):
    _inherit = 'repair.order'

    customer_asset_id = fields.Many2one(
        comodel_name='customer.asset',
        string='Customer Assets',
        domain="['|', ('contact_id', '=', partner_id), '|', ('company_id', '=', partner_id), ('company_id', '=', parent_company)]"
    )
    parent_company = fields.Many2one(string='Parent Company', related='partner_id.parent_id')

    def action_open_customer_assets(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Customer Assets',
             'res_model': 'customer.asset',
            'view_mode': 'form',
            'res_id': self.customer_asset_id.id,
            'target': 'current',
        }

