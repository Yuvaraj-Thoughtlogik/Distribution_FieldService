# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import models, fields, api
from datetime import date


class InvoiceBackdateWizard(models.TransientModel):

    _name = 'sh.invoice.backdate.wizard'
    _description = "Invoice Backdate Wizard"

    account_move_ids = fields.Many2many('account.move')
    invoice_date = fields.Datetime(
        string="Invoice Date", required=True, default=lambda self: fields.Datetime.now())
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company)
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

    def open_invoice_backdate_wizard(self):
        active_ids = self.env.context.get('active_ids')

        return {
            'name': self.env._('Assign Backdate'),
            'res_model': 'sh.invoice.backdate.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('sh_all_in_one_backdate.invoice_backdate_wizard_view_form').id,
            'context': {
                    'default_account_move_ids': [(6, 0, active_ids)],
            },
            'target': 'new',
            'type': 'ir.actions.act_window'
        }

    def assign_backdate(self):
        if self.company_id.enable_backdate_for_move:
            self.account_move_ids._sh_backdate(self.invoice_date, {'remarks': self.remarks})
