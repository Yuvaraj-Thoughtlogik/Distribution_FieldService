# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import fields, models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    remarks_for_sale = fields.Text(
        string="Remarks for Sale", related="sale_id.remarks")
    is_remarks_for_sale = fields.Boolean(
        related="company_id.remark_for_sale_order", string="Is Remarks for Sale")

    @api.depends('move_ids.state', 'move_ids.date', 'move_type')
    def _compute_scheduled_date(self):
        super()._compute_scheduled_date()
        for picking in self:
            if picking.id and picking.company_id.backdate_for_stock_move and picking.sale_id:
                picking.scheduled_date = picking.sale_id.date_order

    def write(self, vals):
        if vals.get('date_done'):
            sale_pickings = self.filtered(
                lambda p: p.sale_id and p.sale_id.date_order and p.company_id.backdate_for_stock_move)
            if sale_pickings:
                for date_order, pickings in sale_pickings.grouped(lambda p: p.sale_id.date_order).items():
                    super(StockPicking, pickings).write(dict(vals, date_done=date_order))
                others = self - sale_pickings
                if others:
                    super(StockPicking, others).write(vals)
                return True
        return super().write(vals)
