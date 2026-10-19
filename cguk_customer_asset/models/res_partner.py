from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    customer_asset_count = fields.Integer(
        compute='_compute_customer_asset_count',
        string='Customer Asset Count',
    )

    def _get_customer_asset_domain(self):
        self.ensure_one()
        return ['|', '|',
                ('customer_company_id', '=', self.id),
                ('contact_id', '=', self.id),
                ('contact_id.parent_id', '=', self.id)]

    def action_view_customer_assets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Customer Assets'),
            'res_model': 'customer.asset',
            'view_mode': 'list,form',
            'domain': self._get_customer_asset_domain(),
            'target': 'current',
        }

    def _compute_customer_asset_count(self):
        Asset = self.env['customer.asset']
        for partner in self:
            partner.customer_asset_count = Asset.search_count(partner._get_customer_asset_domain()) if partner.id else 0
