# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from datetime import date
from odoo import models, fields, api


class BackdateWizard(models.TransientModel):
    _name = 'sh.sale.backdate.wizard'
    _description = "Sale Backdate Wizard"

    sale_order_ids = fields.Many2many('sale.order')
    date_order = fields.Datetime(
        string="Order Date", required=True, default=fields.Datetime.now)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company)
    remarks = fields.Text(string="Remarks")
    is_remarks = fields.Boolean(
        related="company_id.remark_for_sale_order", string="Is Remarks")
    is_remarks_mandatory = fields.Boolean(
        related="company_id.remark_mandatory_for_sale_order", string="Is remarks mandatory")
    is_boolean = fields.Boolean()

    @api.onchange('date_order')
    def onchange_date_order(self):
        if self.date_order and str(self.date_order.date()) < str(date.today()):
            self.is_boolean = True
        else:
            self.is_boolean = False

    def open_backdate_wizard(self):
        active_ids = self.env.context.get('active_ids')

        return {
            'name': self.env._('Assign Backdate'),
            'res_model': 'sh.sale.backdate.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('sh_all_in_one_backdate.sale_order_backdate_wizard_view_form').id,
            'context': {
                'default_sale_order_ids': [(6, 0, active_ids)],
            },
            'target': 'new',
            'type': 'ir.actions.act_window'
        }

    def assign_backdate(self):
        remarks = self.remarks or ''
        for sale_order in self.sale_order_ids:
            if self.company_id.backdate_for_sale_order:
                sale_order.write({
                    'date_order': self.date_order,
                    'remarks': remarks,
                })

            if self.company_id.backdate_for_invoice:
                sale_order.invoice_ids._sh_backdate(self.date_order, {'remarks_for_sale': remarks})

            if self.company_id.backdate_for_stock_move:
                for picking in sale_order.picking_ids:
                    picking.write({
                        'scheduled_date': self.date_order,
                        'date_deadline': self.date_order,
                    })
                    if picking.state == 'done':
                        picking.date_done = self.date_order
                    # Odoo 20: writing the move date replays the valuation
                    # (stock_account), then the stock journal entries are re-dated.
                    picking.move_ids._sh_set_backdate(self.date_order)
