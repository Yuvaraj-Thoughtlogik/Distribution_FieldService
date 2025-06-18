from odoo import models, fields, api

class RepairOrder(models.Model):
    _inherit = 'repair.order'

    customer_asset_ids = fields.Many2many(
        comodel_name='customer.asset',
        string='Customer Assets',
        compute='_compute_customer_asset_ids',
        store=True,
        readonly=False,
        domain="['|', ('contact_id', '=', partner_id), '|', ('company_id', '=', partner_id), ('company_id', '=', parent_company)]"
        # domain="['|', ('contact_id', '=', partner_id), ('company_id', '=', partner_id)]"
    )
    parent_company = fields.Many2one(string='Parent Company', related='partner_id.parent_id')
    customer_asset_count = fields.Integer(
        string='Customer Asset Count',
        compute='_compute_customer_asset_count',
        store=False
    )

    @api.depends('partner_id')
    def _compute_customer_asset_ids(self):
        for record in self:
            # Clear field if no customer selected
            if not record.partner_id:
                record.customer_asset_ids = [(5, 0, 0)]  # Clears Many2many field
                continue

            partner = record.partner_id
            assets = self.env['customer.asset'].search([
                '|',
                ('contact_id', '=', record.partner_id.id),
                '|',
                ('company_id', '=', record.partner_id.id),
                ('company_id', '=', record.partner_id.parent_id.id)
            ])
            record.customer_asset_ids = assets

    @api.onchange('partner_id')
    def _onchange_partner_id_clear_assets(self):
        self.customer_asset_ids = [(5, 0, 0)]

    @api.depends('customer_asset_ids')
    def _compute_customer_asset_count(self):
        for record in self:
            record.customer_asset_count = len(record.customer_asset_ids)

    def action_open_customer_assets(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Customer Assets',
            'res_model': 'customer.asset',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.customer_asset_ids.ids)],
            'context': {'default_partner_id': self.partner_id.id},
        }

