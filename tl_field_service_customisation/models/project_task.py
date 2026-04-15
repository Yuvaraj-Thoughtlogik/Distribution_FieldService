from odoo import fields,models
from odoo.osv import expression


class FSM(models.Model):
    _inherit = 'project.task'

    warehouse_id = fields.Many2one(comodel_name='stock.warehouse', string='Warehouse')

    def action_fsm_view_material(self):
        res = super().action_fsm_view_material()

        res['domain'] = expression.AND([res['domain'], ["|",('warehouse_id', '=', self.warehouse_id.id),('warehouse_id', '=', False)]])
        return res


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    warehouse_id = fields.Many2one(comodel_name='stock.warehouse', string='Warehouse',store=True)


