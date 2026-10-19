# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from datetime import date
from odoo import models, fields, api


class BackdateWizard(models.TransientModel):
    _name = 'sh.purchase.backdate.wizard'
    _description = "Purchase Backdate Wizard"

    purchase_order_ids = fields.Many2many('purchase.order')
    date_planned = fields.Datetime(
        string="Receipt Date", required=True, default=fields.Datetime.now)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company)
    remarks = fields.Text(string="Remarks")
    is_remarks = fields.Boolean(
        related="company_id.remark_for_purchase_order", string="Is Remarks")
    is_remarks_mandatory = fields.Boolean(
        related="company_id.remark_mandatory_for_purchase_order", string="Is remarks mandatory")
    is_boolean = fields.Boolean()

    @api.onchange('date_planned')
    def onchange_date_planned(self):
        if self.date_planned:
            if str(self.date_planned.date()) < str(date.today()):
                self.is_boolean = True
            else:
                self.is_boolean = False

    def open_backdate_wizard(self):
        active_ids = self.env.context.get('active_ids')

        return {
            'name': self.env._('Assign Backdate'),
            'res_model': 'sh.purchase.backdate.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('sh_all_in_one_backdate.purchase_order_backdate_wizard_view_form').id,
            'context': {
                    'default_purchase_order_ids': [(6, 0, active_ids)],
            },
            'target': 'new',
            'type': 'ir.actions.act_window'
        }

    def assign_backdate(self):
        remarks = self.remarks or ''
        for purchase_order in self.purchase_order_ids:

            if self.company_id.backdate_for_purchase_order:
                purchase_order.write({
                    'date_planned': self.date_planned,
                    'date_approve': self.date_planned,
                    'remarks': remarks,
                })

            if self.company_id.backdate_for_bill:
                purchase_order.invoice_ids._sh_backdate(self.date_planned, {'remarks_for_purchase': remarks})

            if self.company_id.backdate_for_stock_move:
                for picking in purchase_order.picking_ids:
                    picking.scheduled_date = self.date_planned
                    if picking.state == 'done':
                        picking.date_done = self.date_planned
                    # Odoo 20: writing the move date replays the valuation
                    # (stock_account), then the stock journal entries are re-dated.
                    picking.move_ids._sh_set_backdate(self.date_planned)
