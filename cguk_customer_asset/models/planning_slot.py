from odoo import api, fields, models


class PlanningSlot(models.Model):
    """Field Service interventions (Odoo 20: planning.slot) linked to customer assets."""
    _inherit = 'planning.slot'

    parent_company = fields.Many2one(string='Parent Company', related='partner_id.parent_id')
    customer_assets_ids = fields.Many2many(
        comodel_name="customer.asset",
        relation='customer_asset_planning_slot_rel',
        column1='planning_slot_id',
        column2='customer_asset_id',
        string="Customer Assets",
        compute="_compute_customer_assets_ids",
        store=True,
        readonly=False,
        copy=True,
        domain="['|', ('contact_id', 'child_of', partner_id), '|', ('customer_company_id', '=', partner_id), '|', ('customer_company_id', '=', parent_company), ('delivery_address_id', '=', partner_id)]",
    )
    customer_assets_count = fields.Integer(string="Customer Assets Count", compute="_compute_customer_assets_count")

    @api.depends('helpdesk_ticket_id')
    def _compute_customer_assets_ids(self):
        """Interventions planned from a helpdesk ticket inherit the ticket's assets."""
        for slot in self:
            if slot.helpdesk_ticket_id.customer_assets_ids and not slot.customer_assets_ids:
                slot.customer_assets_ids = slot.helpdesk_ticket_id.customer_assets_ids

    @api.depends('customer_assets_ids')
    def _compute_customer_assets_count(self):
        for slot in self:
            slot.customer_assets_count = len(slot.customer_assets_ids)

    def action_view_customer_assets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Related Customer Assets'),
            'res_model': 'customer.asset',
            'view_mode': 'list,form',
            'domain': [('intervention_ids', 'in', self.id)],
            'target': 'current',
        }
