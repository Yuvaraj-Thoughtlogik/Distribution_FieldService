from odoo import models,fields,api


class CustomerAssets(models.Model):
    _inherit = 'customer.asset'

    contract_id = fields.Many2one(comodel_name='service.contract',string="Service Contract",related='subscription_id.contract_id')

    def action_view_contract(self):
        self.ensure_one()
        return {
            'name':self.contract_id.name,
            'type':'ir.actions.act_window',
            'view_mode':'form',
            'res_model':'service.contract',
            'res_id':self.contract_id.id,
            'target':'current'
        }