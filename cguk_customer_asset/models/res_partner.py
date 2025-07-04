from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Required field
    customer_asset_count = fields.Integer(
        compute='_compute_customer_asset_ids',
        string='Customer Asset Count'
    )

    # Required action method
    def action_view_customer_assets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Customer Assets',
            'res_model': 'customer.asset',
            'view_mode': 'list,form',
            'domain': ['|', '|',
                       ('company_id', '=', self.id),
                       ('contact_id', '=', self.id),
                       ('contact_id.parent_id', '=', self.id)],
            'target': 'current',
        }

    @api.depends('child_ids')
    def _compute_customer_asset_ids(self):
        for partner in self:
            domain = ['|', '|',
                      ('company_id', '=', partner.id),
                      ('contact_id', '=', partner.id),
                      ('contact_id.parent_id', '=', partner.id)]
            assets = self.env['customer.asset'].search(domain)
            partner.customer_asset_count = len(assets)
