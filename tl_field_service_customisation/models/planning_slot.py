from odoo import fields, models
from odoo.fields import Domain


class PlanningSlot(models.Model):
    _inherit = 'planning.slot'

    warehouse_id = fields.Many2one(comodel_name='stock.warehouse', string='Warehouse')

    def _get_available_product_materials_domain(self):
        """Restrict the materials catalog of an intervention to the products of its warehouse
        (products without warehouse are visible for every intervention)."""
        domain = super()._get_available_product_materials_domain()
        if self.warehouse_id:
            domain &= Domain('warehouse_id', 'in', [self.warehouse_id.id, False])
        return domain


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    warehouse_id = fields.Many2one(comodel_name='stock.warehouse', string='Warehouse')
