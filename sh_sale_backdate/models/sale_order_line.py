# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_procurement_values(self, group_id=False):
        res = super()._prepare_procurement_values(group_id)
        if self.company_id.backdate_for_stock_move and self.order_id:
            res['date_deadline'] = self.order_id.date_order
            res['date_planned'] = self.order_id.date_order
        elif self.order_id:
            res['date_deadline'] = fields.Date.today()
            res['date_planned'] = fields.Date.today()
        return res
