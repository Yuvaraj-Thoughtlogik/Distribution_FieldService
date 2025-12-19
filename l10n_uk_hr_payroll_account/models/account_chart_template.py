# AUGUR Payroll Proprietary License v1.0
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

from odoo import models
from collections import defaultdict


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    def _configure_payroll_account_uk(self, companies):
        """
            |                                              | Debit | Credit |               Comment                |
            | -------------------------------------------- | ----- | ------ | ------------------------------------ |
            | PAYE & Employee NIC                          | 2220  | 2210   |                                     |
            | Employer's NIC                               | 7012  | 2210   |                                     |
            | Salaries & Wages                             | 7010  | 2220   |                                     |
            | Pension - Employee Contribution              | 2220  | 2230   |                                     |
            | Pension - Employer Contribution              | 7013  | 2230   |                                     |
            | Child Maintenance                            | 2220  | 2215   |                                     |
            | Medical Insurance                            | 2220  | 2240   |                                     |
            | Medical Insurance - Employer Contribution    | 7014  | 2240   |                                     |
            | Student Loans                                | 2220  | 2210   |                                     |
            | Post-Graduate Loans                          | 2220  | 2210   |                                     |
            | HMRC Recovery (Statutory Leaves)             | 1105  | 7010   |  Statutory Recovery                 |                                    |
        """
        account_codes = [
            #  Debit Balances (Expenses & Receivables)
            "1105",  # HMRC Statutory Leave Recoveries
            "7000",  # Wages & Salaries Expense
            "7012",  # Employer's NIC
            "7013",  # Employer's Pension Contributions
            "7014",  # Employer's Medical Insurance
            # Credit Balances (Payables)
            "2210",  # PAYE & NI Payable
            "2215",  # Child Maintenance Payable
            "2220",  # Wages & Salaries Payable (Clearing)
            "2230",  # Pension Contributions Payable
            "2240",  # Medical Insurance Payable

        ]
        default_account = "7000"
        rules_mapping = defaultdict(dict)

        # ================================================ #
        #          UK Employee Payroll Structure           #
        # ================================================ #

        # basic_rule = self.env['hr.salary.rule'].search([
        #    ('struct_id', '=', self.env.ref('l10n_uk_hr_payroll.uk_hr_payroll_employee_structure').id),
        #    ('code', '=', 'BASIC')
        # ])
        # rules_mapping[basic_rule]['credit'] = '700000'

        structure_uk = self.env.ref('l10n_uk_hr_payroll.uk_hr_payroll_employee_structure')

        schedule_uk_rule_employer_ni = self.env.ref("l10n_uk_hr_payroll.l10n_uk_hr_employer_ni_monthly")
        schedule_uk_rule_employee_ni = self.env.ref("l10n_uk_hr_payroll.l10n_uk_hr_employee_ni_monthly")
        schedule_uk_rule_paye = self.env.ref("l10n_uk_hr_payroll.l10n_uk_hr_PAYE_monthly")

        schedule_uk_rule_employee_pension = self.env.ref("l10n_uk_hr_payroll.l10n_uk_hr_pension_employee_monthly")
        schedule_uk_rule_employer_pension = self.env.ref("l10n_uk_hr_payroll.l10n_uk_hr_pension_employer_monthly")

        schedule_uk_rule_car = self.env.ref("l10n_uk_hr_payroll.l10n_uk_hr_allowance_car_monthly")
        schedule_uk_rule_postgrad = self.env.ref("l10n_uk_hr_payroll.l10n_uk_hr_postgraduate_loan_monthly")
        schedule_uk_rule_student = self.env.ref("l10n_uk_hr_payroll.l10n_uk_hr_student_loan_monthly")
        schedule_uk_rule_ssp = self.env.ref("l10n_uk_hr_payroll.l10n_uk_hr_ssp_monthly")
        schedule_uk_rule_smp = self.env.ref("l10n_uk_hr_payroll.l10n_uk_hr_smp_monthly")
        schedule_uk_rule_spp = self.env.ref("l10n_uk_hr_payroll.l10n_uk_hr_spp_monthly")
        schedule_uk_rule_adp = self.env.ref("l10n_uk_hr_payroll.l10n_uk_hr_sap_monthly")
        schedule_uk_rule_spb = self.env.ref("l10n_uk_hr_payroll.l10n_uk_hr_spb_monthly")
        schedule_uk_rule_spl = self.env.ref("l10n_uk_hr_payroll.l10n_uk_hr_spl_monthly")
        schedule_uk_rule_snn = self.env.ref("l10n_uk_hr_payroll.l10n_uk_hr_snn_monthly")

        schedule_uk_rule_ssp_recovery = self.env.ref("l10n_uk_hr_payroll.l10n_uk_hr_statutory_recovery_monthly")

        schedule_uk_rule_bonus = self.env.ref("l10n_uk_hr_payroll.l10n_uk_hr_bonus_monthly")
        schedule_uk_rule_commission = self.env.ref("l10n_uk_hr_payroll.l10n_uk_hr_commission_monthly")
        schedule_uk_rule_overtime = self.env.ref("l10n_uk_hr_payroll.l10n_uk_hr_overtime_monthly")

        schedule_1_rule_net = self.env['hr.salary.rule'].search([
            ('struct_id', '=', structure_uk.id),
            ('code', '=', 'NET')
        ])

        rules_mapping = {

            schedule_uk_rule_employer_ni: {
                "debit": "7012",
                "credit": "2210",
                # "debit_tags": "+NIC",
            },
            schedule_uk_rule_employee_ni: {
                "credit": "2210",
                "debit": "2220",
                # "debit_tags": "+NI",
            },
            schedule_uk_rule_paye: {
                "credit": "2210",
                "debit": "2220",
                # "debit_tags": "+PAYE",
            },
            schedule_uk_rule_employee_pension: {
                "credit": "2230",
                "debit": "2220",
            },
            schedule_uk_rule_employer_pension: {
                "credit": "2230",
                "debit": "7013",
            },
            schedule_uk_rule_car: {
                "credit": "2220",
                "debit": "7010",
            },
            schedule_uk_rule_postgrad: {
                "credit": "2220",
                "debit": "2210",
                # "debit_tags": "+POSTGRAD",
            },
            schedule_uk_rule_student: {
                "credit": "2220",
                "debit": "2210",
                # "debit_tags": "+STUDENT",
            },
            schedule_uk_rule_spb: {
                "credit": "2220",
                "debit": "7010",
            },
            schedule_uk_rule_spl: {
                "credit": "2220",
                "debit": "7010",
            },
            schedule_uk_rule_snn: {
                "credit": "2220",
                "debit": "7010",
            },

            schedule_uk_rule_adp: {
                "credit": "2220",
                "debit": "7010",
            },
            schedule_uk_rule_spp: {
                "credit": "2220",
                "debit": "7010",
            },
            schedule_uk_rule_smp: {
                "credit": "2220",
                "debit": "7010",
            },
            schedule_uk_rule_ssp: {
                "credit": "2220",
                "debit": "7010",
            },
            schedule_uk_rule_ssp_recovery: {
                "credit": "7010",
                "debit": "1105",
                # "debit_tags": "+SSPRECOVERY",
            },
            schedule_uk_rule_bonus: {
                "credit": "2220",
                "debit": "7010",
            },
            schedule_uk_rule_commission: {
                "credit": "2220",
                "debit": "7010",
            },
            schedule_uk_rule_overtime: {
                "credit": "2220",
                "debit": "7010",
            },
        }

        self._configure_payroll_account(
            companies,
            "UK",
            account_codes=account_codes,
            rules_mapping=rules_mapping,
            default_account=default_account)
