from email.policy import default

from odoo import models, fields, api
from odoo.api import ValuesType, Self


class CustomerAsset(models.Model):
    _name = 'customer.asset'
    _description = 'Customer Asset'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Equipment Serial Number", required=True,default="New")
    product_id = fields.Many2one('product.product', string='Product', required=True)
    sale_date = fields.Date(string='Sale Date')
    install_date = fields.Date(string='Install Date')
    under_warranty = fields.Boolean(string='Under Warranty?')
    warranty_expiry = fields.Date(string='Warranty Expiry Date')
    active_contract = fields.Boolean(string='Active?')
    contract_start_date = fields.Date(string='Start Date')
    contract_end_date = fields.Date(string='End Date')
    contract_renewal_date = fields.Date(string='Renewal Date')
    company_id = fields.Many2one('res.company', string='Company')
    contact_id = fields.Many2one('res.partner', string='Contact')
    address = fields.Char(string='Address', compute='_compute_address', store=True)
    helpdesk_ticket_id = fields.Many2one('helpdesk.ticket', string='Help Desk Ticket')
    subscription_id = fields.Many2one('sale.order', string='Subscription')
    fsm_task_id = fields.Many2one('project.task', string='FSM Task')

    @api.depends('company_id')
    def _compute_address(self):
        for rec in self:
            rec.address = rec.company_id.partner_id.contact_address if rec.company_id else ''
    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            if not val.get("name") or val['name'] == "New":
                val['name'] = self.env['ir.sequence'].next_by_code("customer.asset")
        return super().create(vals)