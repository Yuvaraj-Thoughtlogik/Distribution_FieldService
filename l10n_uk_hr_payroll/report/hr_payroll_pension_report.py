# -*- coding:utf-8 -*-
# AUGUR Solutions Payroll Proprietary License v1.0
# Copyright © Augur Solutions Ltd, 2024-2025

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

from odoo import fields, models


class HrPayrollReport(models.Model):
    _inherit = "hr.payroll.report"

    struct_id = fields.Many2one('hr.payroll.structure', 'Structure', readonly=True)

    def _select(self, additional_rules):
        return super()._select(additional_rules) + """,
                p.struct_id as struct_id,
                pl.date_from, pl_date_to, emp.name, emp.registration_number, emp.l10n_uk_ni_code, 
                pl.rate as EmployeeContributionPercentage, pl.total as EmployeeContributionAmount, 
                pl2.rate as EmployerContributionPercentage, pl2.total as EmployerContributionAmount, 
                pl.amount as PensionablePayForPayrollPeriod
                """

    def _from(self, additional_rules):
        return super()._from(additional_rules) + """
                hr_payslip_line pl
                INNER JOIN hr_employee emp on pl.employee_id = emp.id and pl.code in ('PENC')
                LEFT JOIN hr_payslip_line pl2 on pl.employee_id = pl2.employee_id and pl.slip_id = pl2.slip_id and pl2.code in ('PENE')
                """

    def _group_by(self, additional_rules):
        return super()._group_by(additional_rules) + """,
            """

    def _order_by(self, additional_rules):
        return super().order_by(additional_rules) + """,
            """
