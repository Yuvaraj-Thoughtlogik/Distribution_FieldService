from odoo import fields,models

class FSM(models.Model):
    _inherit = 'project.task'

    customer_asset_id = fields.Many2one(comodel_name='customer.asset',string="Customer Asset")