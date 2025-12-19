# -*- coding:utf-8 -*-
# AUGUR Solutions Payroll Proprietary License v1.0
# Copyright © Augur Solutions Ltd, 2024-2025
#
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
import math

from odoo import fields, models, api
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import time

from odoo.exceptions import RedirectWarning, ValidationError
from odoo.fields import Command

import logging

from odoo.tools import float_repr

_log = logging.getLogger(__name__)


class employee_paye_fps_return(models.Model):
    _name = "employee_paye_fps_return"
    _description = "Holds employees PAYE data during a FPS return"

    currency_id = fields.Many2one(comodel_name='res.currency',
                                  default=lambda self: self.env['res.currency'].search([('name', '=', 'GBP')], limit=1))
    transaction_id = fields.Many2many(comodel_name='l10n_uk.hmrc.transaction', string='Transactions')

    inactivity_indicator = fields.Boolean()
    information_correct = fields.Boolean()
    hmrc_paye_password = fields.Char(string="PAYE password", store=True)
    use_wrong_period = fields.Boolean()
    already_submitted_period = fields.Boolean()
    late_reason = fields.Selection([
        ('A', 'Notional payment: Payment to Expat by third party or overseas employer'),
        ('B', 'Notional payment: Employment related security'),
        ('C', 'Notional payment: Other'),
        ('D', 'Payment subject to Class 1 NICs but P11D / P9D for tax'),
        ('E', 'Micro Employer using temporary "on or before" relaxation'),
        ('F', 'No requirement to maintain a Deductions Working Sheet or Impractical to report work done on the day'),
        ('G', 'Reasonable excuse'),
        ('H', 'Correction to earlier submission'),
    ],
        required=False, groups="hr_payroll.group_hr_payroll_user", readonly=False, string="Late Reason")

    #date_from = fields.Date(string='From date', default=fields.Date.today() + relativedelta(day=6))
    #date_to = fields.Date(string='To date', default=fields.Date.today() + relativedelta(months=+1, day=5))
    run_id = fields.Many2one(comodel_name='hr.payslip.run', string="Payslip Batch")

    # get employees with pay in the pay run
    employee_ids = fields.Many2many('hr.employee', string='Employees',
                                    default=lambda self: self._get_employees(), required=True, store=True)

    def generate_paye_fps(self):
        # TODO Re-allocate this to the correct fields
        if not self.env.company.l10n_uk_hmrc_tax_office_reference or not self.env.company.l10n_uk_hmrc_account_office_reference \
                or not self.env.company.l10n_uk_hmrc_tax_office_number or not self.env.company.l10n_uk_hmrc_sender_id:
            raise RedirectWarning(
                message="Please fill the PAYE fields on the company.",
                action={
                    'view_mode': 'form',
                    'res_model': 'res.company',
                    'type': 'ir.actions.act_window',
                    'res_id': self.env.company.id,
                    'views': [(False, 'form')],
                },
                button_text="Open the company form",
            )

        if not self.information_correct:
            raise ValidationError(
                "Please confirm the information is correct on the bottom of this form before proceeding")
        if not self.hmrc_paye_password:
            raise ValidationError(
                "Please enter your HMRC password for id: " + str(self.env.company.l10n_uk_hmrc_sender_id)
                + " on the bottom of this form")

        payruns = self.env['hr.payslip.run'].search([('id', '=', self.run_id.id),
                                                  # ('paid_date', '>=', self.date_from),
                                                  # ('paid_date', '<=', self.date_to),
                                                  ('state', 'in', ['paid']),
                                                  ('company_id', '=', self.env.company.id)])
        employee_lines = []

        transaction_create_vals = {
            'transaction_type': 'paye_fps_return',
            'period_start': payruns.date_start,
            'period_end': payruns.date_end,
            'company_id': self.env.company.id,
            # 'inactivity_indicator': self.inactivity_indicator,
            'user_id': self.env.user.id,
            'employee_ids': [],
            'employee_return_ids': [],
        }

        employer_credentials = {
            'sender_id': self.env.company.l10n_uk_hmrc_sender_id,
            'password': self.hmrc_paye_password,
            'tax_office_number': self.env.company.l10n_uk_hmrc_tax_office_number,
            'tax_office_reference': self.env.company.l10n_uk_hmrc_tax_office_reference,
            'accounts_office_reference': self.env.company.l10n_uk_hmrc_account_office_reference,
            'unique_taxpayer_reference': self.env.company.l10n_uk_hmrc_unique_taxpayer_reference,
        }

        # TODO - calculate this and the namespace
        related_tax_year = '24-25'

        document_data = {
            # 'inactivity_indicator': inactivity_indicator,
            'period_end': payruns.date_end,
            'related_tax_year': related_tax_year,
            'employee_return_ids': [],
            'employee_ids': [],
            'scheme_ceased_date': self.env.company.l10n_uk_hmrc_paye_ceased,
        }

        for employee in self.employee_ids:

            _log.info("Processing: " + str(employee.name) + " Pay Run: " + str(self.run_id.name)
                      + " Company: " + str(self.env.company.name))
            # Need to submit each FPS before the pay date
            payslips = self.env['hr.payslip'].search([('payslip_run_id', '=', self.run_id.id),
                                                      ('state', 'in', ['paid']),
                                                      ('employee_id', '=', employee.id),
                                                      ('company_id', '=', self.env.company.id),
                                                      ])
            _log.info("Found payslips: " + str(len(payslips)))

            # or filter payslips from above ?
            for payslip in payslips:

                # all slips *should* be in the same year but this is safest
                year_start = payslip.company_id.get_last_ytd_reset_date(payslip.date_to)
                _log.info("Year Start: " + str(year_start) + " Paid Date: " + str(payslip.paid_date) +
                          " NICT: " + str(payslip._sum('NICT', year_start, payslip.paid_date)) +
                          " GROSS: " + str(payslip._sum('GROSS', year_start, payslip.paid_date)))

                # If there is Gross Taxable for PAYE or NI
                if round(payslip._sum('NICT', year_start, payslip.paid_date) +
                         payslip._sum('GROSS', year_start, payslip.paid_date), 2) > 0.00:

                    period_no = 0

                    if employee.contract_id.schedule_pay == 'monthly':
                        pay_frequency = 'M1'
                        period_no = relativedelta(payslip.paid_date, year_start).months + 1
                    elif employee.contract_id.schedule_pay == 'weekly':
                        pay_frequency = 'W1'
                        #period_no = relativedelta(payslip.paid_date, year_start).weeks + 1
                        period_no = payslip._get_week_no(payslip.paid_date)
                    elif employee.contract_id.schedule_pay in (['bi-weekly', 'semi-monthly']):
                        pay_frequency = 'W2'
                        period_no = relativedelta(payslip.paid_date, year_start).weeks / 2 + 1
                    elif employee.contract_id.schedule_pay == 'annually':
                        pay_frequency = 'MA'
                    elif employee.contract_id.schedule_pay == 'semi-annually':
                        pay_frequency = 'M6'
                    elif employee.contract_id.schedule_pay == 'quarterly':
                        pay_frequency = 'M3'
                    else:
                        pay_frequency = 'IR' # Irregular (Could also be one-off = 'IO')


                    if employee.gender == 'male':
                        gender = 'M'
                    else:
                        gender = 'F'

                    zero = False


                    _log.info("Employee: " + str(payslip.employee_id.name) + " Start Date: "
                              + str(payslip.paid_date) + " period: " + str(period_no))

                    # Overrides
                    first_non_zero = lambda a, b: a if a > 0 else b if b > 0 else None

                    #if float_repr(payslip._sum('NICT', self.date_from, self.date_to), 2) == 0.00:
                    #    float_repr(payslip._sum('GROSS', self.date_from, self.date_to), 2)

                    appointed_week = 0
                    if employee.contract_id.is_director and employee.contract_id.director_date >= year_start:
                        # calc week of start
                        appointed_week = self.get_week_number(year_start, employee.contract_id.director_date)

                    if employee.l10n_uk_taxcode_prefix not in ('S', 'C', 'SK','CK', 'SD2', 'SD3', 'C0T', 'CBR', 'S0T', 'SBR', 'SD0', 'CD0', 'CD1', 'SD1'):
                        tax_code = str(employee.l10n_uk_tax_code)
                        tax_regime = ''
                    else:
                        # Add the Tax Regime for Scotland (S) or Wales (C)
                        tax_regime = str(
                            employee.l10n_uk_taxcode_prefix[0:1] if employee.l10n_uk_taxcode_prefix[0:1] else '')
                        employee.l10n_uk_tax_regime = tax_regime

                        tax_code = employee.l10n_uk_taxcode_prefix[1:len(employee.l10n_uk_taxcode_prefix)]
                        tax_code += str(employee.l10n_uk_taxcode_numeric)
                        if employee.l10n_uk_taxcode_suffix:
                            tax_code += employee.l10n_uk_taxcode_suffix
                    _log.info("Tax Regime: %r", employee.l10n_uk_taxcode_prefix)

                    if employee.l10n_uk_taxcode_w1m1:
                        non_cumulative = 'yes'
                    else:
                        non_cumulative = ''

                    leaving_date = ''
                    if employee.contract_id.date_end:
                        _log.info("Employee Left: " + str(employee.contract_id.date_end))
                        _log.info("Payslip Dates: " + str(payslip.date_from) + " / " + str(payslip.date_to))
                        if payslip.date_from <= employee.contract_id.date_end <= payslip.date_to:
                            _log.info("Setting Leaving Date: " + str(employee.contract_id.date_end))
                            leaving_date = employee.contract_id.date_end

                    # Set defaults for pension disclosures
                    employee_pension_contributions_not_paid_ytd = 0.00
                    employee_pension_contributions_not_paid = 0.00
                    employee_pension_contributions_paid_ytd = 0.00
                    employee_pension_contributions_paid = 0.00

                    # override pension disclosures with actual figures if applicable
                    if employee.contract_id.is_autoenrolment:
                        if employee.contract_id.is_pension_direct_pay():  # aka Net Pay or given by the Employer
                            employee_pension_contributions_paid_ytd = float_repr(
                                payslip._sum('PENE', year_start, payslip.paid_date), 2)
                            employee_pension_contributions_paid = float_repr(payslip._sum_run('PENE', self.run_id.id),
                                                                             2)
                            _log.info("Set Pension Contributions to Direct Pay for " + str(
                                employee.name + " amount: " + str(employee_pension_contributions_paid)))
                        else:  # relief at source or paid to the Pension Fund
                            employee_pension_contributions_not_paid_ytd = float_repr(
                                payslip._sum('PENE', year_start, payslip.paid_date), 2)
                            employee_pension_contributions_not_paid = float_repr(
                                payslip._sum_run('PENE', self.run_id.id), 2)
                            _log.info("Set Pension Contributions to Relief at Source for " + str(
                                employee.name + " amount: " + str(employee_pension_contributions_not_paid)))

                    # calculate Hours Worked
                    if employee.contract_id.schedule_pay == 'monthly':
                        hours = employee.contract_id.resource_calendar_id.full_time_required_hours # per week
                        hours_worked = self.get_hours_worked(hours)

                    else: # assumed weekly pay
                        hours = (payslip._get_regular_worked_hours() +
                                    self.worked_days_line_ids.filtered(lambda d: d.work_entry_type_id.code == 'OVERTIME'))
                        hours_worked = self.get_hours_worked(hours)

                    document_data['employee_return_ids'].append(
                        {'id': employee.id,
                         'nino': employee.l10n_uk_ni_code,
                         'forename': employee.l10n_uk_forename,
                         'surname': employee.l10n_uk_surname,
                         'address1': employee.private_street,
                         'address2': employee.private_street2,
                         'address3': ' '.join(filter(None, [employee.private_city, employee.private_state_id.name])),
                         'postcode': employee.private_zip,
                         'dob': employee.birthday,
                         'gender': gender,  # TODO Odoo allows 'Other' - HMRC only allows m/f ?
                         'is_director': employee.contract_id.is_director,
                         'ytd_basis': employee.contract_id.is_ytd_basis,
                         'appointed_week': appointed_week,
                         'works_id': employee.registration_number,
                         'leaving_date': leaving_date,
                         'taxable_pay_ytd': float_repr(payslip._sum('GROSS', year_start, payslip.paid_date), 2),
                         # YTD after this payrun
                         'total_tax_ytd': float_repr(payslip._sum('PAYE', year_start, payslip.paid_date), 2),
                         # YTD after this payrun
                         'pay_frequency': pay_frequency,
                         'payment_date': payslip.paid_date,
                         'late_reason': self.late_reason,
                         'period_no': period_no,  # accommodate monthly or weekly
                         'periods_covered': 1,
                         'hours_worked': hours_worked,
                         # a = up to 15.99 hrs, b=16-23.99 hrs, c=24-29.99 hrs, d = 30 or more, e=if employee does not have a regular work pattern
                         'tax_code': tax_code,
                         'tax_regime': tax_regime,
                         'non_cumulative': non_cumulative,
                         'taxable_pay': float_repr(payslip._sum_run('GROSS', self.run_id.id), 2),
                         # TODO MAY BE BETTER TO CREATE A RULE
                         'pay_after_stat_deductions': float_repr(payslip._sum_run('GROSS', self.run_id.id)
                                                                 - payslip._sum_run('PAYE', self.run_id.id)
                                                                 - payslip._sum_run('NI', self.run_id.id)
                                                                 - payslip._sum_run('SLOAN', self.run_id.id)
                                                                 - payslip._sum_run('PLOAN', self.run_id.id)
                                                                 , 2),
                         'employee_pension_contributions_not_paid_ytd': employee_pension_contributions_not_paid_ytd or 0.00,
                         'employee_pension_contributions_not_paid': employee_pension_contributions_not_paid or 0.00,
                         'employee_pension_contributions_paid_ytd': employee_pension_contributions_paid_ytd or 0.00,
                         'employee_pension_contributions_paid': employee_pension_contributions_paid or 0.00,
                         'tax_deducted_or_refunded': float_repr(payslip._sum_run('PAYE', self.run_id.id), 2),
                         'payroll_benefits_ytd': float_repr(payslip._sum_category('BIK', year_start, payslip.paid_date), 2),
                         'payroll_benefits': float_repr(payslip._sum_category_run('BIK', self.run_id.id), 2),
                         'total_sl_ytd': float_repr(round(payslip._sum('SLOAN', year_start, payslip.paid_date),0), 2),
                         'total_pl_ytd': float_repr(round(payslip._sum('PLOAN', year_start, payslip.paid_date),0), 2),

                         'has_student_loan': payslip.employee_id.has_student_loan,
                         'has_post_graduate_loan': payslip.employee_id.has_post_graduate_loan,
                         'sl_amt': float_repr(round(payslip._sum_run('SLOAN', self.run_id.id),0), 2),
                         'sl_plan': (str(employee.student_loan_plan).rjust(2, '0')),
                         'pl_amt': float_repr(round(payslip._sum_run('PLOAN', self.run_id.id),0), 2),

                         'ni_letter': employee.l10n_uk_ni_letter,

                         'gross_earnings_for_nic_in_period': float_repr(payslip._sum_category_run('BASIC', self.run_id.id)
                                                  + payslip._sum_category_run('ALW', self.run_id.id),2) or 0.00,
                         'gross_earnings_for_nic_ytd': float_repr(payslip._sum_category('BASIC', year_start, payslip.paid_date)
                                                          + payslip._sum_category('ALW', year_start, payslip.paid_date), 2) or 0.00,
                         'gross_earnings_at_lel_ytd': float_repr(round(payslip._sum('NIC.LEL', year_start, payslip.paid_date)
                                                         + payslip._sum('NIC.ST', year_start, payslip.paid_date),0), 2),
                         'gross_earnings_lel_to_pt_ytd': float_repr(payslip._sum('NIC.PT', year_start, payslip.paid_date), 2),
                         'gross_earnings_pt_to_uel_ytd': float_repr(payslip._sum('NIC.FUST', year_start, payslip.paid_date)
                                                                    + payslip._sum('NIC.UEL', year_start, payslip.paid_date), 2),
                         'total_employer_nic_in_period': float_repr(payslip._sum_run('NIC', self.run_id.id), 2),
                         'total_employer_nic_ytd': float_repr(payslip._sum('NIC', year_start, payslip.paid_date), 2),
                         'employee_ni_contributions_in_period': float_repr(payslip._sum_run('NI', self.run_id.id), 2),
                         'employee_ni_contributions_ytd': float_repr(payslip._sum('NI', year_start, payslip.paid_date), 2),

                         })
                    _log.info("Employee: " + str(payslip.employee_id.name) +
                              " NI PTD: " + float_repr(payslip._sum_run('NI', self.run_id.id), 2) +
                              " NI YTD: " + float_repr(payslip._sum('NI', year_start, payslip.paid_date), 2))
                    document_data['employee_ids'].append(employee.id)

        if len(document_data['employee_ids']) > 0 or document_data['scheme_ceased_date']:
            _log.debug("Attempting to Send FPS Return")

            transaction = self.env['l10n_uk.hmrc.transaction'].create({
                'transaction_type': 'paye_fps_return',
                'period_start': payruns.date_start,
                'period_end': payruns.date_end,
                'company_id': self.env.company.id,
                'sender_user_id': self.env.user.id,
            })

            transaction.sudo()._submit_fps_mr_transaction(
                credentials={
                    'sender_id': self.env.company.l10n_uk_hmrc_sender_id,
                    'password': self.hmrc_paye_password,
                    'accounts_office_reference': self.env.company.l10n_uk_hmrc_account_office_reference,
                    'tax_office_number': self.env.company.l10n_uk_hmrc_tax_office_number,
                    'tax_office_reference': self.env.company.l10n_uk_hmrc_tax_office_reference,
                    'unique_taxpayer_reference': self.env.company.l10n_uk_hmrc_unique_taxpayer_reference,
                    # 'paye_reference': self.env.company.l10n_uk_hmrc_paye_ref, # not used
                },  # or employer_credentials
                document_data=document_data,
            )

            # mark all payslips as submitted & record the transaction id
            #for payslip in payslips:
                # payslip.l10n_uk_hmrc_status = 'S'
                # payslip.l10n_uk_hmrc_transaction = transaction.id

            time.sleep(3)
            transaction.sudo()._cron_poll_pending_transactions()

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'hmrc.confirmation.wizard',
                'view_mode': 'form',
                'view_id': self.env.ref('l10n_uk_reports_paye.fps_confirmation_wizard_view').id,
                'target': 'new',  # Opens as modal dialog
                'context': {'default_message': 'Your FPS return has been sent'},
            }


        else:
            _log.info("No FPS Return Sent")

        return True

    def _get_employees(self):
        return self.env['hr.employee'].search([
                                            ('company_id', '=', self.env.company.id),
                                            ('slip_ids.payslip_run_id', '=', self.run_id.id),
                                            ('slip_ids.state', 'in', ['paid'])
                                            ])

    def get_payslips(self):
        return self.env['hr.payslip'].search([('slip_ids.payslip_run_id', '=', self.run_id.id),
                                              ('state', 'in', ['paid']),
                                              ('employee_id', 'in', self.employee_ids.ids),
                                              ('company_id', '=', self.env.company.id)])

    #@api.onchange('date_from', 'date_to')
    #def _onchange_dates(self):
    #    self.employee_ids = self.env['hr.employee'].search([('company_id', '=', self.env.company.id),
    #                                                        ('slip_ids.paid_date', '>=', self.date_from),
    #                                                        ('slip_ids.paid_date', '<=', self.date_to)])
    @api.onchange('run_id')
    def _onchange_batch(self):
        self.employee_ids = self._get_employees()

    def get_week_number(self, start_date, target_date):

        # Calculate the end date of the 12-month period
        end_date = start_date + timedelta(days=365)

        # Check if the target date is within the 12-month period
        if start_date <= target_date <= end_date:
            delta = target_date - start_date
            _log.debug("Start Date: " + str(start_date) + " Target Date: " + str(target_date) + " Weeks: " + str(
                math.floor(delta.days / 7)))
            return math.floor(delta.days / 7)
        else:
            return False

    def get_hours_worked(self, hours):
        """
            Categorize hours into letter codes:
            - A: up to 15.99 hrs
            - B: 16 - 23.99 hrs
            - C: 24 - 29.99 hrs
            - D: 30 hrs or more
            - E: irregular / no regular work pattern (if hours is None or invalid)
            """
        # Handle irregular work pattern
        if hours is None or not isinstance(hours, (int, float)) or hours < 0:
            return "E"

        if hours <= 15.99:
            return "A"
        elif 16 <= hours <= 23.99:
            return "B"
        elif 24 <= hours <= 29.99:
            return "C"
        elif hours >= 30:
            return "D"
        else:
            return "E"  # fallback