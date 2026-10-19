# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import models, fields, api
from datetime import date


class PickngBackdateWizard(models.TransientModel):
    _name = 'sh.picking.backdate.wizard'
    _description = "Picking Backdate Wizard"

    stock_picking_ids = fields.Many2many('stock.picking',)
    scheduled_date = fields.Datetime(
        string="Scheduled Date", required=True, default=fields.Datetime.now)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company)
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

    def open_picking_backdate_wizard(self):
        active_ids = self.env.context.get('active_ids')

        return {
            'name': self.env._('Assign Backdate'),
            'res_model': 'sh.picking.backdate.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('sh_all_in_one_backdate.stock_picking_backdate_wizard_view_form').id,
            'context': {
                'default_stock_picking_ids': [(6, 0, active_ids)],
            },
            'target': 'new',
            'type': 'ir.actions.act_window'
        }

    def assign_backdate(self):
        if self.company_id.backdate_for_picking:
            for stock_picking in self.stock_picking_ids:
                # Odoo 20: move lines date is related to the move date
                stock_picking.move_ids.with_context(sh_skip_backdate=True).write({
                    'date': self.scheduled_date,
                })
                stock_picking.write({
                    'scheduled_date': self.scheduled_date,
                    'remarks': self.remarks or '',
                })
                stock_picking.write({
                    'date_done': self.scheduled_date,
                })
