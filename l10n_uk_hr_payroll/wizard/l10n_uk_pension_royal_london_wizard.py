# -*- coding: utf-8 -*-
# Copyright Augur Solutions Ltd & Michael Judd 2024, All Rights Reserved
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
from odoo.exceptions import UserError, ValidationError
import logging

_log = logging.getLogger(__name__)


class L10nUKPensionRoyalLondonWizard(models.TransientModel):
    _name = 'l10n_uk_pension_royal_london_wizard'
    _description = 'Royal London Pension Report Wizard'
    id = 'pension_royal_london'

    run_id = fields.Many2one(comodel_name='hr.payslip.run', string="Payslip Batch")
    employee_ids = fields.Many2many('hr.employee', string='Employees',
                                    default=lambda self: self._get_employees(), required=True, store=True)

    def _get_employees(self):
        return self.env['hr.employee'].search([('company_id', '=', self.env.company.id),
                                               ('slip_ids.payslip_run_id', '=', self.run_id.id),
                                               ('slip_ids.state', 'in', ['paid'])
                                               ])

    def get_payslips(self):
        return self.env['hr.payslip'].search([('slip_ids.payslip_run_id', '=', self.run_id.id),
                                              ('state', 'in', [('paid')]),
                                              ('employee_id', 'in', self.employee_ids.ids),
                                              ('company_id', '=', self.env.company.id)])

    @api.onchange('run_id')
    def _onchange_batch(self):
        _log.info("Company ID: " + str(self.env.company.id) + " Payroll Batch ID: " + str(self.run_id.id))
        self.employee_ids = self._get_employees()
        _log.info("Employees Found: " + str(len(self.employee_ids)))

    #@api.model
    #def default_get(self, field_list=None):
    #    if self.env.company.country_id.code != "GB":
    #        raise UserError(_('You must be logged in a UK company to use this feature'))
    #    return super().default_get(field_list)

    def action_export_xls(self):
        employee_str = ','.join(str(i) for i in self.employee_ids.ids)

#        for slip in self:
#            domain = [
#                ('employee_id', '=', slip.employee_ids.id),
#                ('date_from', '=', slip.date_from),
#                ('date_to', '=', slip.date_to),
#                ('id', '!=', slip.id)
#            ]
#            duplicates = self.env['hr.payslip'].search_count(domain)
#            if duplicates > 0:
#                raise ValidationError(_('You cannot generate this report to include multiple payments for the same Employee - please adjust your date filters'))

        return {
            'name': 'Export Royal London Pension Report Amount',
            'type': 'ir.actions.act_url',
            'url': f'/export/uk/royal_london/{employee_str}/{self.run_id.id}',
        }

    def action_export_csv(self):
        employee_str = ','.join(str(i) for i in self.employee_ids.ids)

#        for slip in self:
#            domain = [
#                ('employee_id', '=', slip.employee_ids.id),
#                ('date_from', '=', slip.date_from),
#                ('date_to', '=', slip.date_to),
#                ('id', '!=', slip.id)
#            ]
#            duplicates = self.env['hr.payslip'].search_count(domain)
#            if duplicates > 0:
#                raise ValidationError(_('You cannot generate this report to include multiple payments for the same Employee - please adjust your date filters'))

        return {
            'name': 'Export Royal London Pension Report Amount',
            'type': 'ir.actions.act_url',
            'url': f'/export/uk/royal_london/{employee_str}/{self.run_id.id}',
        }

