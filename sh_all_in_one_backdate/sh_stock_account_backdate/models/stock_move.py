# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from collections import defaultdict

from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _create_account_move(self):
        """Odoo 20: stock valuation entries are created on stock.move (no more
        stock.valuation.layer). Date the journal entries with the (possibly
        backdated) date of the stock moves instead of today."""
        if not self or self.env.context.get('force_period_date'):
            return super()._create_account_move()
        today = fields.Date.context_today(self)
        moves_by_date = defaultdict(lambda: self.env['stock.move'])
        for move in self:
            move_date = fields.Date.context_today(self, move.date) if move.date else today
            moves_by_date[move_date] |= move
        if set(moves_by_date) == {today}:
            return super()._create_account_move()
        account_moves = self.env['account.move']
        for move_date, moves in moves_by_date.items():
            account_moves |= super(StockMove, moves.with_context(force_period_date=move_date))._create_account_move()
        return account_moves

    def _sh_backdate_account_moves(self, new_date):
        """Re-date the stock journal entries linked to the moves.

        Replaces the former stock.valuation.layer create_date SQL updates:
        the valuation itself is replayed by stock.move.write({'date': ...}).
        """
        if not new_date:
            return
        new_date = fields.Datetime.to_datetime(new_date)
        accounting_date = fields.Date.context_today(self, new_date)
        account_moves = self.sudo().account_move_id.filtered(
            lambda m: m.state != 'cancel' and m.date != accounting_date)
        for account_move in account_moves:
            was_posted = account_move.state == 'posted'
            if was_posted:
                account_move.button_draft()
            account_move._sh_write_dated_vals({'date': accounting_date})
            if was_posted:
                account_move.action_post()

    def _sh_set_backdate(self, new_date, extra_vals=None):
        """Backdate done/undone moves: the write on `date` lets stock_account
        replay the valuation; then the related journal entries are re-dated."""
        vals = dict(extra_vals or {})
        vals['date'] = new_date
        self.with_context(sh_skip_backdate=True).write(vals)
        self._sh_backdate_account_moves(new_date)
