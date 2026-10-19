# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from collections import defaultdict
from datetime import date

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    remarks_for_picking = fields.Text(
        string="Remarks for picking", related="picking_id.remarks")
    is_remarks_for_picking = fields.Boolean(
        related="company_id.remark_for_picking", string="Is Remarks for picking")

    # Odoo 20: stock.scrap does not exist anymore, a scrap is a stock.move (is_scrap)
    sh_scrap_date = fields.Datetime(
        string="Scrap Date", copy=False,
        help="Backdate applied to the scrap move when it is confirmed.")
    remarks_for_scrap = fields.Text(string="Remarks for scrap")
    is_remarks_for_scrap = fields.Boolean(
        related="company_id.remark_for_scrap", string="Is Remarks for scrap")
    is_remarks_mandatory_for_scrap = fields.Boolean(
        related="company_id.remark_mandatory_for_scrap", string="Is remarks mandatory for scrap")
    is_scrap_backdated = fields.Boolean(compute='_compute_is_scrap_backdated')

    @api.depends('sh_scrap_date')
    def _compute_is_scrap_backdated(self):
        for move in self:
            move.is_scrap_backdated = bool(
                move.sh_scrap_date and str(move.sh_scrap_date.date()) < str(date.today()))

    def _sh_get_forced_date(self):
        """Date imposed on the move by the backdate configuration (or False)."""
        self.ensure_one()
        company = self.company_id
        if self.is_scrap:
            if company.backdate_for_scrap and self.sh_scrap_date:
                return self.sh_scrap_date
            return False
        if self.picking_id.scheduled_date and (
                company.backdate_for_picking or company.backdate_for_stock_move):
            return self.picking_id.scheduled_date
        return False

    def write(self, vals):
        # Former behaviour (purchase / sale / stock backdate): the move date always
        # follows the picking scheduled date (or the scrap date). Restricted to the
        # writes on `date` (e.g. _action_done) because, in Odoo 20, changing the date
        # of a valued move replays the valuation.
        ctx = self.env.context
        if not vals.get('date') or ctx.get('sh_skip_backdate') or ctx.get('skip_backdate_validation'):
            return super().write(vals)
        forced = defaultdict(lambda: self.env['stock.move'])
        others = self.env['stock.move']
        for move in self:
            forced_date = move._sh_get_forced_date()
            if forced_date:
                forced[forced_date] |= move
            else:
                others |= move
        if not forced:
            return super().write(vals)
        if others:
            super(StockMove, others).write(vals)
        for forced_date, moves in forced.items():
            super(StockMove, moves).write(dict(vals, date=forced_date))
        return True
