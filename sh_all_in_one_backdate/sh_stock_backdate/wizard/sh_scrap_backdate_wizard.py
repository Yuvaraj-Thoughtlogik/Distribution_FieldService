# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import models, fields, api
from datetime import date


class ScrapBackdateWizard(models.TransientModel):
    _name = 'sh.scrap.backdate.wizard'
    _description = "Scrap Backdate Wizard"

    # Odoo 20: stock.scrap was removed, scraps are stock.move records (is_scrap)
    scrap_ids = fields.Many2many('stock.move', domain=[('is_scrap', '=', True)])
    date_done = fields.Datetime(
        string="Date", required=True, default=fields.Datetime.now)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company)
    remarks = fields.Text(string="Remarks")
    is_remarks = fields.Boolean(
        related="company_id.remark_for_scrap", string="Is Remarks")
    is_remarks_mandatory = fields.Boolean(
        related="company_id.remark_mandatory_for_scrap", string="Is remarks mandatory")
    is_boolean = fields.Boolean()

    @api.onchange('date_done')
    def onchange_date_done(self):
        if self.date_done and str(self.date_done.date()) < str(date.today()):
            self.is_boolean = True
        else:
            self.is_boolean = False

    def open_scrap_backdate_wizard(self):
        active_ids = self.env['stock.move'].browse(
            self.env.context.get('active_ids') or []).filtered('is_scrap').ids

        return {
            'name': self.env._('Assign Backdate'),
            'res_model': 'sh.scrap.backdate.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('sh_all_in_one_backdate.stock_scrap_backdate_wizard_view_form').id,
            'context': {
                'default_scrap_ids': [(6, 0, active_ids)],
            },
            'target': 'new',
            'type': 'ir.actions.act_window'
        }

    def assign_backdate(self):
        if self.company_id.backdate_for_scrap:
            scraps = self.scrap_ids.filtered('is_scrap')
            scraps.with_context(sh_skip_backdate=True).write({
                'sh_scrap_date': self.date_done,
                'date': self.date_done,
                'remarks_for_scrap': self.remarks or '',
            })
