# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class AccountMove(models.Model):

    _inherit = 'account.move'

    remarks = fields.Text(string="Remarks")
    is_remarks = fields.Boolean(related="company_id.remark_for_move")
    is_remarks_mandatory = fields.Boolean(
        related="company_id.remark_mandatory_move")
    is_boolean = fields.Boolean()

    @api.onchange('invoice_date')
    def onchange_invoice_date(self):
        if self.invoice_date and str(self.invoice_date) < str(date.today()):
            self.is_boolean = True
        else:
            self.is_boolean = False

    def _sh_backdate(self, new_date, extra_vals=None):
        """Reset to draft, set the (invoice) date and re-post the entries."""
        new_date = fields.Date.to_date(new_date)
        for move in self.filtered(lambda m: m.state != 'cancel'):
            was_posted = move.state == 'posted'
            if was_posted:
                move.button_draft()
            vals = dict(extra_vals or {}, date=new_date)
            if move.is_invoice(include_receipts=True):
                vals['invoice_date'] = new_date
            move._sh_write_dated_vals(vals)
            if was_posted:
                move.action_post()

    def _sh_write_dated_vals(self, vals):
        """Write a new date on a draft entry; if the existing sequence number
        does not match the new period anymore, clear it so that a new number
        is assigned when the entry is posted again."""
        self.ensure_one()
        try:
            with self.env.cr.savepoint():
                self.with_context(skip_readonly_check=True).write(vals)
        except ValidationError:
            self.env.invalidate_all()
            self.with_context(skip_readonly_check=True).write(dict(vals, name=False))
