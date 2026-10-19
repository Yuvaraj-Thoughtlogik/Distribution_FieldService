from odoo import api, fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    parent_company = fields.Many2one(string='Parent Company', related='partner_id.parent_id')
    customer_assets_ids = fields.Many2many(
        comodel_name="customer.asset",
        relation='customer_asset_helpdesk_ticket_rel',
        column1='helpdesk_ticket_id',
        column2='customer_asset_id',
        string="Customer Assets",
        domain="['|', ('contact_id', '=', partner_id), '|', ('customer_company_id', '=', partner_id), ('customer_company_id', '=', parent_company)]",
    )
    customer_assets_count = fields.Integer(string="Customer Assets Count", compute="_compute_customer_assets_count")

    @api.depends('customer_assets_ids')
    def _compute_customer_assets_count(self):
        for record in self:
            record.customer_assets_count = len(record.customer_assets_ids)

    def action_view_customer_assets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Related Customer Assets'),
            'res_model': 'customer.asset',
            'view_mode': 'list,form',
            'domain': [('helpdesk_ticket_ids', 'in', self.id)],
            'target': 'current',
        }

    def _get_intervention_action(self):
        action = super()._get_intervention_action()
        if self.customer_assets_ids:
            action['context'] = dict(action.get('context') or {}, default_customer_assets_ids=self.customer_assets_ids.ids)
        return action
