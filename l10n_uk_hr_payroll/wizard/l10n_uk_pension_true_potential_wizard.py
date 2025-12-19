# -*- coding: utf-8 -*-
# Copyright Augur Ltd & Michael Judd 2024, All Rights Reserved
# AUGUR Payroll Proprietary License v1.0
# Copyright © Augur Solutions Ltd, 2024

# The author and owner of this software is Augur Solutions Ltd
# (a company registered in England with registered number 15886736)
# of 15 Roxford Close, Upper Halliford, SURREY TW17 8RS, England
#
# This software and associated files (the “Software”) may only be used (executed, modified, executed after
# modifications) if you have purchased a valid license from the authors, or if you have received a written
# agreement from the authors of the Software.
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software or modified copies of the
# Software.
#
# The above copyright notice and this permission notice must be included in all copies or substantial portions of
# the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
# TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

from collections import defaultdict
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_log = logging.getLogger(__name__)


class L10nUKPensionTruePotentialWizard(models.TransientModel):
    _name = 'l10n_uk_pension_true_potential_wizard'
    _description = 'True Potential Pension Report Wizard'
    id = 'pension_true_potential'

    @api.model
    def default_get(self, field_list=None):
        if self.env.company.country_id.code != "GB":
            raise UserError(_('You must be logged in a UK company to use this feature'))
        return super().default_get(field_list)

    date_from = fields.Date(default=lambda self: fields.Date.today() + relativedelta(day=1, month=1))
    date_to = fields.Date(default=lambda self: fields.Date.today() + relativedelta(day=31, month=12))
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    employee_amount = fields.Monetary(string="Employee Contribution")
    employer_amount = fields.Monetary(string="Employer Contribution")
    currency_id = fields.Many2one(related="company_id.currency_id")
    line_ids = fields.One2many(
        'l10n_uk_pension_true_potential_line_wizard', 'wizard_id',
        compute='_compute_line_ids', store=True, readonly=False)

    @api.depends('date_from', 'date_to')
    def _compute_line_ids(self):
        for wizard in self.filtered(lambda w: w.date_from and w.date_to):
            all_payslips = self.env['hr.payslip'].search([
                ('company_id', '=', wizard.company_id.id),
                ('date_from', '>=', wizard.date_from),
                ('date_to', '<=', wizard.date_to),
                ('state', 'in', ['done', 'paid'])
            ])

            all_employees = all_payslips.mapped('employee_id')
            _log.debug("Employees found: " + str(len(all_employees)))

            result = [(5, 0, 0)]
            line_codes = ['PENE', 'PENC', 'GROSS']

            line_values = all_payslips._get_line_values(line_codes, vals_list=['amount', 'total'])
            for employee in all_employees:

                employee_payslips = defaultdict(lambda: self.env['hr.payslip'])

                employee_amount = 0
                employer_amount = 0
                pensionable_amount = 0
                employee_earnings = 0

                for payslip in all_payslips.filtered(lambda e: e.employee_id.id == employee.id):
                    employee_amount += sum(line_values['PENE'][p.id]['total'] for p in payslip)
                    employer_amount += sum(line_values['PENC'][p.id]['total'] for p in payslip)
                    employee_earnings += sum(line_values['GROSS'][p.id]['total'] for p in payslip)
                    pensionable_amount += sum(line_values['PENC'][p.id]['amount'] for p in payslip)
                    _log.debug("Earnings: " + str(pensionable_amount) + " " + str(employee_earnings))

                    contract = self.env['hr.contract'].search([('employee_id', '=', employee.id)])
                    # .with_context(active_test=False)
                result.append((0, 0, {
                    'employee_id': employee.id,
                    'nino': employee.l10n_uk_ni_code,
                    'member_id': contract.member_no,
                    'pensionable_amount': pensionable_amount,
                    'employee_earnings': employee_earnings,
                    'employee_amount': employee_amount,
                    'employer_amount': employer_amount,
                    'wizard_id': wizard.id
                }))



            wizard.line_ids = result


    def action_export_xls(self):
        self.ensure_one()
        _log.debug("action_export_xlsx: " + str(self.id))
        return {
            'name': 'Export True Potential Pension Report Amount',
            'type': 'ir.actions.act_url',
            'url': '/export/uk/tp/%s' % (self.id),
        }
    def action_export_csv(self):
        self.ensure_one()
        _log.debug("action_export_csv: " + str(self.id))
        return {
            'name': 'Export True Potential Pension Report Amount',
            'type': 'ir.actions.act_url',
            'url': '/export/uk/tp/%s' % (self.id),
        }

class L10nUKPensionTruePotentialLineWizard(models.TransientModel):
    _name = 'l10n_uk_pension_true_potential_line_wizard'
    _description = 'True Potential Pension Report Wizard Line'

    wizard_id = fields.Many2one('l10n_uk_pension_true_potential_wizard')
    employee_id = fields.Many2one('hr.employee', required=True)
    nino = fields.Char(string="NI No", related='employee_id.l10n_uk_ni_code')

    member_id = fields.Char()
    pensionable_amount = fields.Monetary()
    employee_earnings = fields.Monetary()
    employee_amount = fields.Monetary()
    employer_amount = fields.Monetary()
    currency_id = fields.Many2one(related='wizard_id.currency_id')
