# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import fields, models, api
from datetime import date


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    remarks = fields.Text(string="Remarks")
    is_remarks = fields.Boolean(
        related="company_id.remark_for_picking", string="Is Remarks")
    is_remarks_mandatory = fields.Boolean(
        related="company_id.remark_mandatory_for_picking", string="Is remarks mandatory")
    is_boolean = fields.Boolean()

    @api.onchange('scheduled_date')
    def onchange_scheduled_date(self):
        if self.scheduled_date and str(self.scheduled_date.date()) < str(date.today()):
            self.is_boolean = True
        else:
            self.is_boolean = False

    def _set_scheduled_date(self):
        # Core skips done pickings; with backdate enabled the done moves also follow
        # the scheduled date (stock_account replays the valuation on date change).
        done_backdated = self.filtered(
            lambda p: p.state == 'done'
            and (p.company_id.backdate_for_picking or p.company_id.backdate_for_stock_move))
        super(StockPicking, self - done_backdated)._set_scheduled_date()
        for picking in done_backdated:
            picking.move_ids.with_context(sh_skip_backdate=True).write({'date': picking.scheduled_date})
