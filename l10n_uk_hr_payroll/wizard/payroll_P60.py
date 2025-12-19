# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from xml.etree.ElementTree import tostring

from odoo import models, fields


class ReportP60(models.TransientModel):
    _name = 'l10n_uk_hr_payroll_p60'
    _description = "Payroll P60 End of Year Report"

    def _get_employees(self):
        return self.env['hr.employee'].search([('contract_ids.state', 'in', ('open', 'close')),
                                               ('company_id', '=', self.env.company.id)])

    employee_ids = fields.Many2many('hr.employee', string='Employees',
                                    default=lambda self: self._get_employees(), required=True, store=True)

    year = fields.Integer('Year', default=lambda self: fields.date.today().year - 1)

    def generate_p60(self):
        employee_str = ','.join(str(i) for i in self.employee_ids.ids)
        return {
            'name': 'P60',
            'type': 'ir.actions.act_url',
            'url': f'/print/p60/{employee_str}/{self.year}',
        }