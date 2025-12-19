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


import decimal
import json
import logging
import math
from _decimal import Decimal
from datetime import date, datetime

import requests
from functools import reduce
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round, ormcache

_log = logging.getLogger(__name__)


class Payslip(models.Model):
    _inherit = 'hr.payslip'

    l10n_uk_ni_letter = fields.Selection(related='employee_id.l10n_uk_ni_letter', store=False, readonly=True)

    # used to calculate the Employment Allowance YTD before committing the value to the company
    # should be updated when the payslip is marked as paid - currently there is no reversal logic
    # TODO reversal logic for payslips that are paid and then the state is change to an earlier state
    l10n_uk_hmrc_employment_allowance = fields.Monetary(string="Employment Allowance Claimed", default=0.00)

    def _get_periods(self):
        schedule = self.contract_id.schedule_pay or self.contract_id.structure_type_id.default_schedule_pay
        periods = 12

        if schedule == 'quarterly':
            periods = 4
        elif schedule == 'semi-annually':
            periods = 2
        elif schedule == 'annually':
            periods = 1
        elif schedule == 'weekly':
            periods = 52
        elif schedule == '4-weekly':
            periods = 4 / 52
        elif schedule == 'bi-weekly':
            periods = 26
        elif schedule == 'bi-monthly':
            periods = 24
        elif schedule == 'monthly':
            period = 12
        else:  # if not handled, put the monthly behaviour
            periods = 12
        return periods

    def _get_dashboard_warnings(self):
        res = super()._get_dashboard_warnings()
        uk_companies = self.env.companies.filtered(lambda c: c.country_id.code == 'UK')
        if uk_companies:
            # HMRC PAYE Tax Office Details
            # HMRC UTN
            # Companies House Registration Number

            # NI VALIDATION
            invalid_ni_employee_ids = self.env['hr.employee']._get_invalid_ni_employee_ids()
            if invalid_ni_employee_ids:
                invalid_ni_str = _('Employees With Invalid NI Numbers')
                res.append({
                    'string': invalid_ni_str,
                    'count': len(invalid_ni_employee_ids),
                    'action': self._dashboard_default_action(invalid_ni_str, 'hr.employee', invalid_ni_employee_ids),
                })

            # GENDER VALIDATION
            invalid_gender_employees = self.env['hr.employee'].search([
                ('gender', 'not in', ['male', 'female']),
                ('company_id', 'in', uk_companies.ids)
            ])
            if invalid_gender_employees:
                invalid_gender_str = _('Employees With Invalid Configured Gender')
                res.append({
                    'string': invalid_gender_str,
                    'count': len(invalid_gender_employees),
                    'action': self._dashboard_default_action(invalid_gender_str, 'hr.employee',
                                                             invalid_gender_employees.ids),
                })

        return res

    def _compute_l18n_taxcode_prefix(self, localdict):
        employee = self.contract_id.employee_id
        return employee.l10n_uk_taxcode_prefix

    def _compute_l18n_taxcode_suffix(self, localdict):
        employee = self.contract_id.employee_id
        return employee.l10n_uk_taxcode_suffix

    def _compute_l18n_taxcode_numeric(self, localdict):
        employee = self.contract_id.employee_id
        return employee.l10n_uk_taxcode_numeric

    def find_rates(self, x, rates, isEmployee):
        self.ensure_one()

        def round_down(value, decimals):
            with decimal.localcontext() as ctx:
                d = decimal.Decimal(value)
                ctx.rounding = decimal.ROUND_HALF_DOWN
                return round(d, decimals)

        tax = decimal.Decimal(0)
        amount = decimal.Decimal(x)
        employee = self.contract_id.employee_id

        NILetter = employee.l10n_uk_ni_letter
        _log.debug("NI Letter: " + NILetter)

        # https://www.gov.uk/national-insurance-rates-letters/category-letters
        if NILetter != "0":  # Invalid
            periods = self._get_periods()
            _log.info("Periods in a year: " + str(periods))

            for low, high, c1, c2, c3, c4 in rates:
                if self.contract_id.is_director and self.contract_id.is_ytd_basis:
                    low = decimal.Decimal(low)
                    high = decimal.Decimal(high)
                else:
                    # for non-directors it's OK to use the monthly amounts
                    low = decimal.Decimal(round(low / periods, 0))
                    high = decimal.Decimal(round(high / periods, 0))

                c1 = decimal.Decimal(c1)
                c2 = decimal.Decimal(c2)
                c3 = decimal.Decimal(c3)
                c4 = decimal.Decimal(c4)

                _log.info("NI: " + str(low) + " / " + str(high) + " / " + str(c1) + " / " + str(c2) + " / " + str(
                    c3) + " / " + str(c4))

                # Employees with NI Letter = X pay no National Insurance
                if NILetter in 'X':
                    return 0.00

                if isEmployee:  # Employee NIC
                    _log.debug("Employee NIC")
                    context = decimal.getcontext()
                    context.rounding = decimal.ROUND_HALF_DOWN
                    if amount <= high and amount >= low:

                        if NILetter in 'AMHFVN':
                            tax += round((amount - low) * decimal.Decimal(c1 / 100), 3)
                            _log.debug("1: " + str(round(amount - low, 3)) + " rate: " + str(c1) + " tax: " + str(tax))
                        elif NILetter in 'BIE':
                            tax += round((amount - low) * decimal.Decimal(c2 / 100), 3)
                            _log.debug("1: " + str(round(amount - low, 3)) + " rate: " + str(c2) + " tax: " + str(tax))
                        elif NILetter in 'CSK':
                            tax += round((amount - low) * decimal.Decimal(c3 / 100), 3)
                            _log.debug("1: " + str(round(amount - low, 3)) + " rate: " + str(c3) + " tax: " + str(tax))
                        elif NILetter in 'JLZD':
                            tax += round((amount - low) * decimal.Decimal(c4 / 100), 3)
                            _log.debug("1: " + str(round(amount - low, 3)) + " rate: " + str(c4) + " tax: " + str(
                                (amount - low) * (c4 / 1)))
                    elif x > high:
                        if NILetter in 'AMHFVN':
                            tax += round((high - low) * decimal.Decimal(c1 / 100), 3)
                            _log.debug("2: " + str(round(high - low, 3)) + " rate: " + str(c1) + " tax: " + str(tax))
                        elif NILetter in 'BIE':
                            tax += round((high - low) * decimal.Decimal(c2 / 100), 3)
                            _log.debug("2: " + str(round(high - low, 3)) + " rate: " + str(c2) + " tax: " + str(tax))
                        elif NILetter in 'CSK':
                            tax += round((high - low) * decimal.Decimal(c3 / 100), 3)
                            _log.debug("2: " + str(round(high - low, 3)) + " rate: " + str(c3) + " tax: " + str(tax))
                        elif NILetter in 'JLZD':
                            tax += round((high - low) * decimal.Decimal(c4 / 100), 3)
                            _log.debug("2: " + str(round(high - low, 3)) + " rate: " + str(c4) + " tax: " + str(tax))

                else:  ## Employer NIC
                    _log.info("Employer NIC")
                    context = decimal.getcontext()
                    context.rounding = decimal.ROUND_HALF_DOWN
                    if amount <= high and amount >= low:
                        if NILetter in 'ABCJ':
                            tax += round((amount - low) * decimal.Decimal(c1 / 100), 3)
                            _log.info("1: " + str(round(amount - low, 3)) + " rate: " + str(c1) + " tax: " + str(tax))
                        elif NILetter in 'HMVZ':
                            tax += round((amount - low) * decimal.Decimal(c2 / 100), 3)
                            _log.info("1: " + str(round(amount - low, 3)) + " rate: " + str(c2) + " tax: " + str(tax))
                        elif NILetter in 'FISL':
                            tax += round((amount - low) * decimal.Decimal(c3 / 100), 3)
                            _log.info("1: " + str(round(amount - low, 3)) + " rate: " + str(c3) + " tax: " + str(tax))
                        elif NILetter in 'JLZD':
                            tax += round((amount - low) * decimal.Decimal(c4 / 100), 3)
                            _log.info("1: " + str(round(amount - low, 3)) + " rate: " + str(c4) + " tax: " + str(tax))
                    elif amount > high:
                        if NILetter in 'ABCJ':
                            tax += round((high - low) * decimal.Decimal(c1 / 100), 3)
                            _log.info("2: " + str(round(high - low, 3)) + " rate: " + str(c1) + " tax: " + str(tax))
                        elif NILetter in 'HMVZ':
                            tax += round((high - low) * decimal.Decimal(c2 / 100), 3)
                            _log.info("2: " + str(round(high - low, 3)) + " rate: " + str(c2) + " tax: " + str(tax))
                        elif NILetter in 'FISL':
                            tax += round((high - low) * decimal.Decimal(c3 / 100), 3)
                            _log.info("2: " + str(round(high - low, 3)) + " rate: " + str(c3) + " tax: " + str(tax))
                        elif NILetter in 'DEKN':
                            tax += round((high - low) * decimal.Decimal(c4 / 100), 3)
                            _log.info("2: " + str(round(high - low, 3)) + " rate: " + str(c4) + " tax: " + str(tax))

        return tax

    def _get_employer_ni(self, localdict):
        self.ensure_one()

        categories = localdict['categories']
        payslip = localdict['payslip']
        contract = localdict['contract']
        rules = localdict['result_rules']

        yearStart = payslip.company_id.get_last_ytd_reset_date(payslip.paid_date)
        yearEnd = payslip.company_id.get_last_ytd_reset_date(payslip.paid_date) + relativedelta(years=+1, days=-1)
        _log.debug("Year Start: " + str(yearStart) + " Year End: " + str(yearEnd))

        employers_ni_table = payslip._rule_parameter('UK_PAYE_NIC', payslip.paid_date)
        if contract.is_director and contract.is_ytd_basis:

            # Add back Pension Contributions Deducted from Pay if the Pension Fund is Direct Pay
            ytd = payslip._sum_category('BASIC', str(yearStart), str(yearEnd)) + categories['BASIC'] \
                  + payslip._sum_category('ALW', str(yearStart), str(yearEnd)) + categories['ALW'] \
                  + payslip._sum_category('NIO', str(yearStart), str(yearEnd)) + categories['NIO'] \
                  + payslip._sum_category('SP', str(yearStart), str(yearEnd)) + categories['SP'] \
                  - payslip._sum_category('NTD', str(yearStart), str(yearEnd)) - categories['NTD'] \
                  + payslip.employee_id.past_employer_pay


            amount = self.find_rates(ytd, employers_ni_table, False)
            _log.info("YTD Employer NICs due: " + str(amount))
            amount -= Decimal(str(payslip._sum('NIC', str(yearStart), str(yearEnd))))
            amount -= Decimal(payslip.employee_id.past_employer_employer_ni)
            _log.info("YTD Employer NICs paid: " + str(amount))
        else:

            amount = self.find_rates(categories['BASIC'] + categories['ALW'] + categories['SP'] + categories['NIO'] - categories['NTD'], employers_ni_table, False)

        if amount < 0:
            amount = 0

        return amount

    def _get_employee_ni(self, localdict):
        self.ensure_one()

        categories = localdict['categories']
        rules = localdict['result_rules']
        payslip = localdict['payslip']
        contract = localdict['contract']

        employees_ni_table = localdict['payslip']._rule_parameter('UK_PAYE_NI')

        if contract.is_director and contract.is_ytd_basis:

            yearStart = payslip.company_id.get_last_ytd_reset_date(payslip.paid_date)
            yearEnd = payslip.company_id.get_last_ytd_reset_date(payslip.paid_date) + relativedelta(years=+1, days=-1)

            # Add back Pension Contributions Deducted from Pay if the Pension Fund is Direct Pay
            ytd = payslip._sum_category('BASIC', str(yearStart), str(yearEnd)) + categories['BASIC'] \
                  + payslip._sum_category('ALW', str(yearStart), str(yearEnd)) + categories['ALW'] \
                  + payslip._sum_category('SP', str(yearStart), str(yearEnd)) + categories['SP'] \
                  - payslip._sum_category('NTD', str(yearStart), str(yearEnd)) - categories['NTD'] \
                  + payslip._sum_category('NIO', str(yearStart), str(yearEnd)) + categories['NIO'] \
                  + payslip.employee_id.past_employer_pay

            ni = self.find_rates(ytd, employees_ni_table, True)
            _log.info("YTD Employee NI due: " + str(ni))
            ni -= Decimal(str(payslip._sum('NI', str(yearStart), str(yearEnd))))
            ni -= Decimal(payslip.employee_id.past_employer_employee_ni)
            _log.info("YTD Employee NIs paid: " + str(ni))
        else:
            ni = self.find_rates(categories['BASIC'] + categories['ALW'] + categories['SP'] + categories['NIO'] - categories['NTD'],
                 employees_ni_table, True)

        if ni < 0:
            ni = 0

        return ni

    def _employee_qualifying_earnings(self, localdict):
        self.ensure_one()

        categories = localdict['categories']
        payslip = localdict['payslip']
        contract = localdict['contract']
        qualifying_earnings = categories['BASIC'] + categories['SP']

        # could include cash allowances such as car or mobile phone - update this to have a flag on the allowance
        pension_company = self.env['l10n_uk_pension_fund_company'].search([('company_id', '=', payslip.company_id.id),
                                                                           ('pension_fund_id', '=', contract.pension_fund.id)], limit=1)
        if pension_company.include_allowances:
            qualifying_earnings += categories['ALW']

        if pension_company.banded_earnings:
            schedule = self.contract_id.schedule_pay or self.contract_id.structure_type_id.default_schedule_pay

            # don't deduct pension below the minimum
            if schedule == 'monthly':
                minimum = payslip._rule_parameter('UK_PEN_SMINM')
            elif schedule == 'weekly':
                minimum = payslip._rule_parameter('UK_PEN_SMINW')
            else:
                minimum = 0

            if qualifying_earnings < minimum:
                pension_contribution = 0

            # cap the maximum pensionable pay
            if schedule == 'monthly':
                maximum = payslip._rule_parameter('UK_PEN_SMAXM')
            elif schedule == 'weekly':
                maximum = payslip._rule_parameter('UK_PEN_SMAXW')
            else:
                maximum = 0

            if qualifying_earnings > maximum and not contract.pension_exceed_max:
                qualifying_earnings = maximum

            if contract.is_autoenrolment:
                # should include bonus, commission, overtime, statutory sick pay, maternity, paternity or adoption pay
                qualifying_earnings -= minimum

        if qualifying_earnings < 0:
            qualifying_earnings = 0

        return round(qualifying_earnings, 2)

    def _get_taxable_pay(self, localdict, ytd=True):
        self.ensure_one()

        employee = self.contract_id.employee_id
        categories = localdict['categories']
        payslip = localdict['payslip']
        contract = localdict['contract']
        result_rules = localdict['result_rules']

        year_start = payslip.company_id.get_last_ytd_reset_date(payslip.paid_date)
        year_end = payslip.company_id.get_last_ytd_reset_date(payslip.paid_date) + relativedelta(years=+1, days=-1)
        _log.info("Year Start: " + str(year_start) + " Year End: " + str(year_end))

        schedule = employee.contract_id.schedule_pay or employee.contract_id.structure_type_id.default_schedule_pay

        if schedule == 'monthly':
            denominator = 12
            period_no = self._get_period_monthly_basis(localdict)
        elif schedule == 'weekly':
            denominator = 52
            period_no = self._get_period_weekly_basis(localdict)
        else:
            denominator = 0
            period_no = -1

        _log.info(
            "_get_taxable_pay: Year: " + str(self.getTaxYear(localdict)) + " Period: " + str(period_no) + " " + str(
                schedule))

        # ends with W1 or M1 - Emergency Tax Codes - usually will have a space before it
        if employee.l10n_uk_taxcode_emergency or not ytd:
            ytd = False  # we should already know this as it is passed in
            period_no = 1
        else:
            ytd = True  # we should already know this as it is passed in

        tax_code_prefix = payslip._compute_l18n_taxcode_prefix(localdict) or ''  # is often empty
        tax_code_suffix = payslip._compute_l18n_taxcode_suffix(localdict) or ''
        tax_code_numeric = payslip._compute_l18n_taxcode_numeric(localdict) or 0

        _log.info("Prefix: " + tax_code_prefix + " Numeric: " + str(tax_code_numeric) + " Suffix: " + tax_code_suffix)

        # https://assets.publishing.service.gov.uk/media/65afa3a2334849000dc7391e/Tax-test-data-examples-from-April-2024-v1-1.zip
        # Stage 1 Calculation of Cumulative Pay to date.
        if ytd:
            # Use later of paid date or date to as some pay runs will be in arrears and others in advance
            # However, if you use the latter of the two, you will get the current YTD based on paid date
            if payslip.paid_date > payslip.date_to:
                filter_date = payslip.paid_date
            else:
                filter_date = payslip.date_to

            taxable_pay = payslip._sum_category('BASIC', str(year_start), str(filter_date)) + categories['BASIC'] \
                          + payslip._sum_category('ALW', str(year_start), str(filter_date)) + categories['ALW'] \
                          + payslip._sum_category('BIK', str(year_start), str(filter_date)) + categories['BIK'] \
                          + payslip._sum_category('SP', str(year_start), str(filter_date)) + categories['SP'] \
                          - payslip._sum_category('NTD', str(year_start), str(filter_date)) - categories['NTD'] \
                          + payslip._sum('TPENE', str(year_start), str(filter_date)) + result_rules['TPENE']['total']

            if employee.past_employer_pay > 0:
                taxable_pay += employee.past_employer_pay
                _log.info("Adding Past Employer Pay: " + str(employee.past_employer_pay))

            _log.info("YTD TaxablePay: " + str(taxable_pay) + " NTD: " + str(
                payslip._sum_category('NTD', str(year_start), str(payslip.date_to)) + categories['NTD']))

        else:
            taxable_pay = (categories['BASIC'] + categories['ALW'] + categories['BIK'] + categories['SP']
                           - categories['NTD'] + result_rules['TPENE']['total'])
            _log.info("TaxablePay: " + str(taxable_pay))

            period_no = 1

        _log.info("YTDTaxablePay1: " + str(taxable_pay) + " Previous: " + str(
            payslip._sum_category('BASIC', str(year_start), str(payslip.date_to))) + " Current: " + str(
            categories['BASIC']))

        # Tax codes that exclude the Personal Tax free allowance
        if tax_code_prefix in ('BR', '0T', 'D0', 'D1', 'SD2', 'SD3', 'C0T', 'CBR', 'S0T', 'SBR', 'SD0', 'CD0', 'CD1',
                               'SD1'):
            pay_adjustment = 0
        else:
            # reduce taxable pay be tax-free threshold
            # Stage 2 Calculation of Taxable Pay to date - as per the instructions for programmers
            quotient = int((tax_code_numeric - 1) / 500)  # (1257 -1) /500 = 2
            remainder = (tax_code_numeric - 1 - (quotient * 500)) + 1  # (1257 - (2 * 500)) + 1 = 258

            part_1 = (math.floor((((remainder * 10) + 9) / denominator) * 100 ) / 100) + 0.01
            part_2 = quotient * ((math.floor(((500 * 10) / denominator) * 100 ) / 100) + 0.01) # must be rounded up to the next 1/100's

            pay_adjustment = round((part_1 + part_2), 4)
            _log.info('Period Pay Adjustment: ' + str(part_1) + ' ' + str(part_2) + ' ' + str(pay_adjustment))
            pay_adjustment = round(pay_adjustment * period_no, 4)  # FreePay: (215.75 + 833.33) = 1049.08

            _log.info("Quotient: " + str(quotient) + " Remainder: " + str(remainder) \
                      + " Part1: " + str(part_1) + " Part2: " + str(part_2) + " PayAdjustment: " + str(pay_adjustment))

        # If your tax code has a K prefix, this means you owe tax to the HMRC. Rather than receiving personal allowance to reduce your taxable pay, your taxable pay is increased instead.
        if tax_code_prefix in ('K', 'SK', 'CK'):
            _log.info("Tax Code is K so adding pay adjustment of " + str(pay_adjustment))
            taxable_pay += pay_adjustment
        else:
            taxable_pay -= pay_adjustment

        _log.info("TaxablePay with Pay Adjustment: " + str(taxable_pay))

        if contract.is_autoenrolment and not contract.is_pension_direct_pay:
            if ytd:
                pension = payslip._sum('PENE', str(year_start), str(year_end)) \
                          + round(payslip._employee_qualifying_earnings(localdict) * (
                            payslip._employee_pension_rate(localdict) / 100), 2)
            else:
                pension = round(payslip._employee_qualifying_earnings(localdict) * (
                            payslip._employee_pension_rate(localdict) / 100), 2)
            _log.info("Pension: " + str(pension))
            taxable_pay -= pension

        _log.info("TaxablePay Adjusted for Pension: " + str(taxable_pay))
        return round(taxable_pay, 2)

    def _get_period_monthly_basis(self, localdict):

        payslip = localdict['payslip']

        year_end = payslip.company_id.get_last_ytd_reset_date(payslip.paid_date) + relativedelta(years=+1, days=-1)
        year_start = payslip.company_id.get_last_ytd_reset_date(payslip.paid_date)
        end_date = payslip.paid_date

        period_no = relativedelta(end_date, year_start).months + 1
        _log.info(
            "Period No: " + str(period_no) + " Tax Year: " + str(year_end) + " / " + str(year_start) + " / " + str(
                end_date))

        return period_no

    def _get_period_weekly_basis(self, localdict):

        payslip = localdict['payslip']

        #lang = self.employee_id.lang or self.env.user.lang
        #week_start = self.env["res.lang"]._lang_get(lang).week_start

        #year_start = payslip.company_id.get_last_ytd_reset_date(payslip.date_to)
        #year_end = payslip.company_id.get_last_ytd_reset_date(payslip.date_to) + relativedelta(years=+1, days=-1)
        #end_date = payslip.paid_date

        return payslip._get_week_no(payslip.date_to)

        #_log.info("Dates: " + year_start.strftime('%d/%m/%Y') + " / " + end_date.strftime('%d/%m/%Y'))

        #wk_num = end_date.strftime('%U') if week_start == '7' else end_date.strftime('%W')  # calendar year

        #calendar_year_end = date(int(year_start.strftime('%Y')), 12, 31)

        #if date(end_date.year, end_date.month, end_date.day) > calendar_year_end:
        #    # calculate how many weeks there were in the financial year up to Dec 31
        #    wks_last_year = int(
        #        calendar_year_end.strftime('%U') if week_start == '7' else calendar_year_end.strftime('%W')) - \
        #                    int(year_start.strftime('%U') if week_start == '7' else year_start.strftime('%W'))

            # calculate the number of weeks in the current calendar year and add to the weeks from last year
        #    period_no = int(wk_num) - int(calendar_year_end + relativedelta(days=+1).strftime(
        #        '%U') if week_start == '7' else calendar_year_end + relativedelta(days=+1).strftime('%W')) + wks_last_year

        #else:  # on or before December 31st
        #    period_no = int(wk_num) - int(year_start.strftime('%U') if week_start == '7' else int(year_start.strftime('%W')))

        #denominator = 52
        #_log.info("Period no: " + str(period_no))
        #return period_no

    def _get_week_no(self, date_to):
        lang = self.employee_id.lang or self.env.user.lang
        week_start = self.env["res.lang"]._lang_get(lang).week_start

        year_start = self.company_id.get_last_ytd_reset_date(date_to)
        year_end = self.company_id.get_last_ytd_reset_date(date_to) + relativedelta(years=+1, days=-1)
        end_date = date_to

        _log.info("Dates: " + year_start.strftime('%d/%m/%Y') + " / " + end_date.strftime('%d/%m/%Y'))

        wk_num = end_date.strftime('%U') if week_start == '7' else end_date.strftime('%W')  # calendar year

        calendar_year_end = date(int(year_start.strftime('%Y')), 12, 31)

        if date(end_date.year, end_date.month, end_date.day) > calendar_year_end:
            # calculate how many weeks there were in the financial year up to Dec 31
            wks_last_year = int(
                calendar_year_end.strftime('%U') if week_start == '7' else calendar_year_end.strftime('%W')) - \
                            int(year_start.strftime('%U') if week_start == '7' else year_start.strftime('%W'))

            # calculate the number of weeks in the current calendar year and add to the weeks from last year
            period_no = int(wk_num) - int((calendar_year_end + relativedelta(days=+1)).strftime(
                '%U') if week_start == '7' else (calendar_year_end + relativedelta(days=+1)).strftime('%W')) + wks_last_year + 1

        else:  # on or before December 31st
            period_no = int(wk_num) - int(
                year_start.strftime('%U') if week_start == '7' else int(year_start.strftime('%W'))) + 1

        return period_no

    def _calc_tax_amount(self, localdict):
        self.ensure_one()

        employee = self.contract_id.employee_id
        payslip = localdict['payslip']
        categories = localdict['categories']

        # TODO we need to make sure this can be set when generating payslips
        if not payslip.paid_date:
            payslip.paid_date = payslip.date_to

        schedule = employee.contract_id.schedule_pay or employee.contract_id.structure_type_id.default_schedule_pay

        end_date = payslip.date_to
        if schedule == 'monthly':
            denominator = 12
            period_no = self._get_period_monthly_basis(localdict)

        elif schedule == 'weekly':
            denominator = 52
            period_no = self._get_period_weekly_basis(localdict)
            _log.info("Period no: " + str(period_no))

        else: # catchall: may need to implement other schedules later
            denominator = 1
            period_no = 1

        # Emergency Tax is calculated on the Month or Week only - not YTD
        if employee.l10n_uk_taxcode_w1m1 or employee.l10n_uk_taxcode_emergency:
            ytd = False  # use Month or Week
            period_no = 1
        else:
            ytd = True  # use YTD

        ytd_taxable_pay = math.floor(payslip._get_taxable_pay(localdict, ytd))  # round down to a whole pound
        _log.info("YTDTaxablePay4: " + str(ytd_taxable_pay))

        tax_code_prefix = payslip._compute_l18n_taxcode_prefix(localdict)
        tax_code_suffix = payslip._compute_l18n_taxcode_suffix(localdict)
        tax_code_numeric = payslip._compute_l18n_taxcode_numeric(localdict)

        if tax_code_prefix and 'K' in tax_code_prefix:
            # strip these codes out as they do not affect this calculation
            tax_code_prefix = tax_code_prefix.replace('K', '')

        # _log.info("Prefix: " + tax_code_prefix + " Numeric: " + str(tax_code_numeric) + " Suffix: " + tax_code_suffix)

        # Stage 3 Calculation of tax due to date.
        ytd_tax_due = 0
        if ytd_taxable_pay > 0:
            if tax_code_prefix in ('NT', 'C', 'S', 'CBR', 'CD0', 'CD1', 'SBR', 'SD0', 'SD1', 'SD2', 'SD3'):
                if tax_code_prefix in 'NT':
                    # Tax Code: Not Taxed (Skip)
                    ytd_tax_due = 0
                    _log.info("Employee has NT tax code and pays no tax: " + tax_code_prefix)
                else:
                    # Determine England/NI, Scotland (S) or Wales (C)

                    # if containsAny(TaxCodeSuffix, {'W1','M1','X'}):  # Emergency Tax Rates
                    # Monthly v Weekly Calcs
                    # BR tax code (Basic Rate for second job - no tax free allowance)

                    if ('C') in tax_code_prefix:  # Wales
                        _log.info("Wales:")
                        R1 = payslip._rule_parameter('UK_PAYE_C_R1') / 100
                        R2 = payslip._rule_parameter('UK_PAYE_C_R2') / 100
                        R3 = payslip._rule_parameter('UK_PAYE_C_R3') / 100
                        R4 = payslip._rule_parameter('UK_PAYE_C_R4') / 100
                        G = payslip._rule_parameter('UK_PAYE_C_G')
                        MaxRate = payslip._rule_parameter('UK_PAYE_C_MaxRate') / 100

                        B1 = payslip._rule_parameter('UK_PAYE_C_B1')
                        B2 = payslip._rule_parameter('UK_PAYE_C_B2')
                        B3 = payslip._rule_parameter('UK_PAYE_C_B3')

                        if 'CBR' in tax_code_prefix:
                            ytd_tax_due = ytd_taxable_pay * R2
                            _log.info("CBR: " + str(ytd_tax_due))
                        elif 'CD0' in tax_code_prefix:
                            ytd_tax_due = ytd_taxable_pay * R3
                            _log.info("CD0: " + str(ytd_tax_due))
                        elif 'CD1' in tax_code_prefix:
                            ytd_tax_due = ytd_taxable_pay * R4
                            _log.info("CD1: " + str(ytd_tax_due))
                        elif employee.l10n_uk_taxcode_emergency:
                            ytd_tax_due = ytd_taxable_pay * MaxRate
                            _log.info("Emergency Tax: " + str(ytd_tax_due))
                        else:
                            if ytd_taxable_pay <= ((B1 / denominator) * period_no):
                                ytd_tax_due = ytd_taxable_pay * R1
                                _log.info("R1: " + str(ytd_tax_due))
                            elif ytd_taxable_pay <= (((B1 + B2) / denominator) * period_no):
                                ytd_tax_due = (((B1 / denominator) * period_no) * R1) + \
                                              ((ytd_taxable_pay - ((B1 / denominator) * period_no)) * R2)
                                _log.info("R2: " + str(ytd_tax_due))
                            elif ytd_taxable_pay <= (((B1 + B2 + B3) / denominator) * period_no):
                                ytd_tax_due = (((B1 / denominator) * period_no) * R1) \
                                              + (((B2 / denominator) * period_no) * R2) \
                                              + ((ytd_taxable_pay - ((B2 / denominator) * period_no)) * R3)
                                _log.info("R3: Parameters" + str(ytd_tax_due) + " PeriodNo: " + str(period_no) +
                                          " Denominator: " + str(denominator))
                                _log.info("R3 Tax Due: " + str(ytd_tax_due))
                                _log.info("R1 Breakdown: " + str(((B1 / denominator) * period_no) * R1))
                                _log.info("R2 Breakdown: " + str(((B2 / denominator) * period_no) * R2))
                                _log.info("R3 Breakdown: " + str((ytd_taxable_pay - ((B2 / denominator) * period_no)) * R3))
                                _log.info("YTDTaxPayable: " + str(ytd_taxable_pay))
                                _log.info("Band: " + str((B3 / denominator) * period_no))
                            else:
                                ytd_tax_due = (((B1 / denominator) * period_no) * R1) \
                                              + (((B2 / denominator) * period_no) * R2) \
                                              + (((B3 / denominator) * period_no) * R3) \
                                              + (ytd_taxable_pay - (((B3 + B2 + B1) / denominator) * period_no)) * R4
                                _log.info("R4: " + str(ytd_tax_due))


                    elif ('S') in tax_code_prefix:  # Scotland

                        _log.info("Scotland:")

                        R1 = payslip._rule_parameter('UK_PAYE_S_R1') / 100
                        R2 = payslip._rule_parameter('UK_PAYE_S_R2') / 100
                        R3 = payslip._rule_parameter('UK_PAYE_S_R3') / 100
                        R4 = payslip._rule_parameter('UK_PAYE_S_R4') / 100
                        R5 = payslip._rule_parameter('UK_PAYE_S_R5') / 100
                        R6 = payslip._rule_parameter('UK_PAYE_S_R6') / 100
                        G = payslip._rule_parameter('UK_PAYE_S_G')
                        MaxRate = payslip._rule_parameter('UK_PAYE_S_MaxRate') / 100

                        B1 = payslip._rule_parameter('UK_PAYE_S_B1')
                        B2 = payslip._rule_parameter('UK_PAYE_S_B2')
                        B3 = payslip._rule_parameter('UK_PAYE_S_B3')
                        B4 = payslip._rule_parameter('UK_PAYE_S_B4')
                        B5 = payslip._rule_parameter('UK_PAYE_S_B5')

                        # For a second job or pension - SBR, SD0, SD1, SD2, SD3
                        if 'SBR' in tax_code_prefix:
                            ytd_tax_due = ytd_taxable_pay * R2
                            _log.info("SBR: " + str(ytd_tax_due))
                        elif 'SD0' in tax_code_prefix:
                            ytd_tax_due = ytd_taxable_pay * R3
                            _log.info("SD0: " + str(ytd_tax_due))
                        elif 'SD1' in tax_code_prefix:
                            ytd_tax_due = ytd_taxable_pay * R4
                            _log.info("SD1: " + str(ytd_tax_due))
                        elif 'SD2' in tax_code_prefix:
                            ytd_tax_due = ytd_taxable_pay * R5
                            _log.info("SD2: " + str(ytd_tax_due))
                        elif 'SD3' in tax_code_prefix:
                            ytd_tax_due = ytd_taxable_pay * R6
                            _log.info("SD3: " + str(ytd_tax_due))
                        elif employee.l10n_uk_taxcode_emergency:
                            ytd_tax_due = ytd_taxable_pay * MaxRate
                            _log.info("Emergency Tax: " + str(ytd_tax_due))
                        else:
                            if ytd_taxable_pay <= ((B1 / denominator) * period_no):
                                ytd_tax_due = ytd_taxable_pay * R1
                                _log.info("R1: " + str(ytd_tax_due))
                            elif ytd_taxable_pay <= (((B1 + B2) / denominator) * period_no):
                                ytd_tax_due = (((B1 / denominator) * period_no) * R1) \
                                              + ((ytd_taxable_pay - ((B1 / denominator) * period_no)) * R2)
                                _log.info("R2: " + str(((B1 / denominator) * period_no) * R1))
                                _log.info("R2: " + str(ytd_tax_due) + "/" + str(B1) + "/" + str(B2) + "/" + str(
                                    R1) + "/" + str(R2) + "/" + str(((B1 / denominator) * period_no) * R1))
                            elif ytd_taxable_pay <= (((B1 + B2 + B3) / denominator) * period_no):
                                ytd_tax_due = (((B1 / denominator) * period_no) * R1) \
                                              + ((((B2) / denominator) * period_no) * R2) \
                                              + ((ytd_taxable_pay - (((B1 + B2) / denominator) * period_no)) * R3)

                                _log.info("R3: " + str(((B1 / denominator) * period_no) * R1))
                                _log.info("R3: " + str(((B2 / denominator) * period_no) * R2))
                                _log.info("R3: " + str(ytd_taxable_pay - (((B1 + B2) / denominator) * period_no) * R2))
                                _log.info("R3: " + str(ytd_tax_due) + "/" + str(B1) + "/" + str(B2) + "/" + str(
                                    B3) + "/" + str(R1) + "/" + str(R2) + "/" + str(R3))

                            elif ytd_taxable_pay <= (((B1 + B2 + B3 + B4) / denominator) * period_no):
                                ytd_tax_due = (((B1 / denominator) * period_no) * R1) \
                                              + (((B2 / denominator) * period_no) * R2) \
                                              + (((B3 / denominator) * period_no) * R3) \
                                              + ((ytd_taxable_pay - (
                                            ((B1 + B2 + B3) / denominator) * period_no)) * R4)  # PROBLEM

                                _log.info("R4: " + str(ytd_tax_due))
                                _log.info("R4 Band1: " + str(((B1 / denominator) * period_no) * R1))
                                _log.info("R4 Band2: " + str(((B2 / denominator) * period_no) * R2))
                                _log.info("R4 Band3: " + str(((B3 / denominator) * period_no) * R3))
                                _log.info("R4 Band4: " + str(ytd_taxable_pay - ((B3 / denominator) * period_no) * R4))

                                _log.info("R4: " + str(ytd_tax_due) + "/ Band1 " + str(B1) + "/ Band2 " + str(
                                    B2) + "/ Band3 " + str(B3) + "/ Band4 " + str(B4) + \
                                           "/ Rate1 " + str(R1) + "/ Rate2 " + str(R2) + "/ Rate3 " + str(
                                    R3) + "/ Rate4 " + str(R4))
                            elif ytd_taxable_pay <= (((B1 + B2 + B3 + B4 + B5) / denominator) * period_no):
                                ytd_tax_due = (((B1 / denominator) * period_no) * R1) \
                                              + ((((B2) / denominator) * period_no) * R2) \
                                              + ((((B3) / denominator) * period_no) * R3) \
                                              + ((((B4) / denominator) * period_no) * R4) \
                                              + ((ytd_taxable_pay - (
                                            ((B1 + B2 + B3 + B4) / denominator) * period_no)) * R5)
                                _log.info("R5: " + str(ytd_tax_due))
                            else:
                                ytd_tax_due = (((B1 / denominator) * period_no) * R1) \
                                              + ((((B2) / denominator) * period_no) * R2) \
                                              + ((((B3) / denominator) * period_no) * R3) \
                                              + ((((B4) / denominator) * period_no) * R4) \
                                              + ((((B5) / denominator) * period_no) * R5) \
                                              + ((ytd_taxable_pay - (
                                            ((B1 + B2 + B3 + B4 + B5) / denominator) * period_no))) * R6
                                _log.info("R6: " + str(ytd_tax_due))


            else:  # England or Northern Ireland

                _log.info("England & NI:")

                R1 = payslip._rule_parameter('UK_PAYE_E_R1') / 100
                R2 = payslip._rule_parameter('UK_PAYE_E_R2') / 100
                R3 = payslip._rule_parameter('UK_PAYE_E_R3') / 100
                R4 = payslip._rule_parameter('UK_PAYE_E_R4') / 100
                G = payslip._rule_parameter('UK_PAYE_E_G')
                MaxRate = payslip._rule_parameter('UK_PAYE_E_MaxRate') / 100
                _log.info(" R1: " + str(R1) + " R2: " + str(R2) + " R3: " + str(R3) + " R4: " + str(R4))

                B1 = payslip._rule_parameter('UK_PAYE_E_B1')
                B2 = payslip._rule_parameter('UK_PAYE_E_B2')
                B3 = payslip._rule_parameter('UK_PAYE_E_B3')
                _log.info(" B1: " + str(B1) + "  B2: " + str(B2) + " B3: " + str(B3))

                if tax_code_prefix and tax_code_prefix != '0T':
                    if tax_code_prefix in 'BR':
                        ytd_tax_due = ytd_taxable_pay * R2
                        _log.debug("BR: " + str(ytd_tax_due))
                    elif tax_code_prefix in 'D0':
                        ytd_tax_due = ytd_taxable_pay * R3
                        _log.debug("D0: " + str(ytd_tax_due))
                    elif tax_code_prefix in 'D1':
                        ytd_tax_due = ytd_taxable_pay * R4
                        _log.debug("D1: " + str(ytd_tax_due))
                elif employee.l10n_uk_taxcode_emergency:
                    ytd_tax_due = ytd_taxable_pay * MaxRate
                    _log.info("Emergency Tax: " + str(ytd_tax_due))
                else:
                    if ytd_taxable_pay <= ((B1 / denominator) * period_no):
                        ytd_tax_due = ytd_taxable_pay * R1
                        _log.info("R1: " + str(ytd_tax_due))
                    elif ytd_taxable_pay <= (((B1 + B2) / denominator) * period_no):
                        ytd_tax_due = (((B1 / denominator) * period_no) * R1) + \
                                      ((ytd_taxable_pay - ((B1 / denominator) * period_no)) * R2)
                    elif ytd_taxable_pay <= (((B1 + B2 + B3) / denominator) * period_no):
                        ytd_tax_due = (((B1 / denominator) * period_no) * R1) \
                                      + (((B2 / denominator) * period_no) * R2) \
                                      + ((ytd_taxable_pay - ((B2 / denominator) * period_no)) * R3)

                        _log.info("R3: " + str(ytd_tax_due) + " PeriodNo: " + str(period_no) + " Denominator: " + str(
                            denominator))
                        _log.info("R1: " + str(((B1 / denominator) * period_no) * R1))
                        _log.info("R2: " + str(((B2 / denominator) * period_no) * R2))
                        _log.info("R3: " + str((ytd_taxable_pay - ((B2 / denominator) * period_no)) * R3))
                        _log.info("YTDTaxPayable: " + str(ytd_taxable_pay))
                        _log.info("Band: " + str((B3 / denominator) * period_no))
                    else:
                        ytd_tax_due = (((B1 / denominator) * period_no) * R1) \
                                      + (((B2 / denominator) * period_no) * R2) \
                                      + (((B3 / denominator) * period_no) * R3) \
                                      + ((ytd_taxable_pay - (((B3 + B2 + B1) / denominator) * period_no)) * R4)

                        _log.info("R4: " + str(ytd_tax_due) + " PeriodNo: " + str(period_no) + " Denominator: " + str(
                            denominator))
                        _log.info("R1: " + str(((B1 / denominator) * period_no) * R1))
                        _log.info("R2: " + str(((B2 / denominator) * period_no) * R2))
                        _log.info("R3: " + str(((B3 / denominator) * period_no) * R3))
                        _log.info("R4: " + str((ytd_taxable_pay - (((B3 + B2) / denominator) * period_no)) * R4))
                        _log.info("YTDTaxPayable: " + str(ytd_taxable_pay))
                        _log.info("Band: " + str((B3 / denominator) * period_no))

                    # HMRC says to use the YTD tax payable to 2 decimal points to determine the Rate to apply, and then round to zero decimal places
                    # GPointer = 2 so start at R2

        _log.info("YTDTaxDue: " + str(ytd_tax_due))

        year_start = payslip.company_id.get_last_ytd_reset_date(payslip.paid_date if payslip.paid_date else payslip.date_to)
        year_end = payslip.company_id.get_last_ytd_reset_date(payslip.date_to) + relativedelta(years=+1, days=-1)

        # Stage 4 Calculation of tax deduction or refund for the week.
        if ytd:
            tax_amount = round(ytd_tax_due - payslip._sum_category('PAYE', str(year_start), str(payslip.date_to)), 2)
            if employee.past_employer_tax > 0:
                tax_amount -= employee.past_employer_tax
                _log.info("Adding Past Employer Tax: " + str(employee.past_employer_tax))
        else:
            tax_amount = round(ytd_tax_due, 2)

        _log.info("Tax Amount: " + str(tax_amount))

        # Apply Regulatory Limit - should not include Benefits in Kind
        if tax_amount > 0:  # note: Regulatory limit should never be applied to negative pay
            # Apply Regulatory Limit - should not include Benefits in Kind
            regulatory_limit = round((categories['GROSS'] - categories['BIK']) / 2, 4) # 50% of pay
            #regulatory_limit = round((payslip._sum_run('GROSS', self.payslip_run_id.id)
            #                          - payslip._sum_run('BIK', self.payslip_run_id.id)) / 2,
            #                         2)  # 50% of pay
            _log.info("Regulatory Limit: " + str(regulatory_limit))
            if tax_amount > regulatory_limit > 0:
                tax_amount = regulatory_limit

        return round(tax_amount, 2)

    def _calc_student_loan_amount(self, localdict):
        self.ensure_one()

        _log.debug("Starting Calc for Student Loan")

        employee = localdict['employee']
        categories = localdict['categories']
        payslip = localdict['payslip']
        applicable_threshold = 0

        rate = payslip._rule_parameter('UK_SL_Rate')
        monthly_thresholds = payslip._rule_parameter('UK_SL_Threshold')
        schedule = employee.contract_id.schedule_pay or employee.contract_id.structure_type_id.default_schedule_pay

        for scheme, threshold in monthly_thresholds:
            _log.debug(
                "Scheme: " + str(scheme) + " " + str(threshold) + " Looking for: " + str(employee.student_loan_plan))
            if str(scheme) == str(employee.student_loan_plan):
                applicable_threshold = float_round(threshold, 0)
                if schedule == 'weekly':
                    applicable_threshold = math.floor(applicable_threshold * 12 / 52)
                _log.debug("Found Threshold: " + str(applicable_threshold))
                break

        _log.debug("Using Threshold: " + str(applicable_threshold))

        # If no threshold found - something has gone wrong
        if employee.has_student_loan and applicable_threshold > 0:
            repayment = (categories['BASIC'] + categories['ALW'] + categories['SP'] + categories['NIO']) - applicable_threshold

            if repayment > 0:
                _log.debug("Repayment: " + str(repayment))
                return math.floor(repayment * (rate / 100))

        return 0.00

    def _calc_postgrad_loan_amount(self, localdict):
        self.ensure_one()

        _log.debug("Starting Calc for Post Graduate Loan")

        employee = localdict['employee']
        categories = localdict['categories']
        payslip = localdict['payslip']

        rate = payslip._rule_parameter('UK_PL_Rate')
        monthly_threshold = payslip._rule_parameter('UK_PL_Threshold')
        schedule = employee.contract_id.schedule_pay or employee.contract_id.structure_type_id.default_schedule_pay

        if schedule == 'weekly':
            threshold = math.floor(monthly_threshold * 12 / 52)
        else:
            threshold = monthly_threshold

        if employee.has_post_graduate_loan and threshold > 0:
            repayment = (categories['BASIC'] + categories['ALW'] + categories['SP'] + categories['NIO'] - threshold)

            if repayment > 0:
                _log.debug("Repayment: " + str(repayment))
                return math.floor(repayment * (rate / 100))

        return 0.00

    # Statutory Recoveries
    # https://www.gov.uk/recover-statutory-payments
    # Applies to:
    # Maternity, Paternity, Adoption, Parental Bereavement Leaves and Shared Parental Pay

    def _calc_statutory_leave(self, localdict):

        payslip = localdict['payslip']
        worked_days = localdict['worked_days']

        # 90% of average weekly earnings for first 6 weeks
        # £184.03 or 90% of average weekly earnings (whichever is lower) for 33 weeks

        # Shared Parental Leave (ShPP) is £184.03 per week or 90% of average weekly earnings, whichever is lower
        weekly_rate = payslip._rule_parameter('UK_Parental_Leave_Rate')  # 184.03

        if 'LEAVE310' in worked_days:  # Sick Leave
            # weekly_qualifying rate = 123
            # track maximum up to 28 weeks
            # Your employee is no longer eligible for SSP if they have a continuous series of linked periods that lasts more than 3 years.
            days = worked_days['LEAVE310'].number_of_days

        elif 'LEAVE320' in worked_days:  # Maternity Leave
            days = worked_days['LEAVE320'].number_of_days
            payslip._rule_parameter('UK_SSP_Rate') #weekly_rate = 118.75

        elif 'LEAVE330' in worked_days:  # Paternity
            days = 0
        elif 'LEAVE340' in worked_days:  # Adoption
            days = 0
        elif 'LEAVE350' in worked_days:  # Parental Bereavement
            days = 0
        elif 'LEAVE360' in worked_days:  # Shared Parental
            days = 0
        elif 'LEAVE370' in worked_days:  # Neonatal
            days = 0
        else:  # no matches
            days = 0

        monthly_rate = ((weekly_rate / 5) * days)

        return monthly_rate

    def _calc_statutory_recovery_rate(self, localdict):
        # https://www.gov.uk/employers-maternity-pay-leave
        payslip = localdict['payslip']

        if payslip.company_id.l10n_uk_hmrc_small_employer:
            rate = payslip._rule_parameter('UK_SPL_SE_RATE')  # 103
        else:
            rate = payslip._rule_parameter('UK_SPL_RATE')  # 92

        return rate

    def set_Commentary(self, payslip_id, code, commentary):
        self.ensure_one()

        payslip_line = self.env['hr.payslip_line'].search([('payslip_id', '=', payslip_id), ('code', '=', code)],
                                                          limit=1)
        payslip_line.commentary = commentary

        return True

    def getTaxYear(self, localdict):

        payslip = localdict['payslip']
        tax_year = payslip.company_id.get_last_ytd_reset_date(payslip.paid_date) + relativedelta(years=+1)
        payslip.company_id.get_last_ytd_reset_date(payslip.paid_date)
        _log.debug(" Tax Year: " + str(tax_year))

        return tax_year

    def action_payslip_draft(self):
        super().action_payslip_draft()
        if self.payslip_run_id:
            paid_date = self.payslip_run_id.payment_date
        else:
            paid_date = fields.Date.today()

        self.write({'paid_date': paid_date})
        self.write({'date': paid_date})
        return super().action_payslip_draft()

    #def action_payslip_done(self):
    #    invalid_payslips = self._filter_out_of_contracts_payslips()
    #    if invalid_payslips:
    #        raise ValidationError(_('The following employees have a contract outside of the payslip period:\n%s',
    #                                '\n'.join(invalid_payslips.mapped('employee_id.name'))))
    #    if any(slip.contract_id.state == 'cancel' for slip in self):
    #        raise ValidationError(_('You cannot validate a payslip on which the contract is cancelled'))
    #    if any(slip.state == 'cancel' for slip in self):
    #        raise ValidationError(_("You can't validate a cancelled payslip."))
    #    if mismatched_slips := self.filtered(
    #            lambda slip: slip.payslip_run_id and slip.company_id != slip.payslip_run_id.company_id):
    #        raise ValidationError(_(
    #            "The following payslips company differs from the batch's company:\n%s",
    #            "\n".join(mismatched_slips.mapped('number')))
    #        )
    #    self.write({'state': 'done'})

    #    line_values = self._get_line_values(['NET'])

    #    self.filtered(lambda p: not p.credit_note and line_values['NET'][p.id]['total'] < 0).write(
    #        {'has_negative_net_to_report': True})
    #    self.mapped('payslip_run_id').action_close()
        # Validate work entries for regular payslips (exclude end of year bonus, ...)
    #    regular_payslips = self.filtered(lambda p: p.struct_id.type_id.default_struct_id == p.struct_id)
    #    work_entries = self.env['hr.work.entry']
    #    for regular_payslip in regular_payslips:
    #        work_entries |= self.env['hr.work.entry'].search([
    #            ('date_start', '<=', regular_payslip.date_to),
    #            ('date_stop', '>=', regular_payslip.date_from),
    #            ('employee_id', '=', regular_payslip.employee_id.id),
    #        ])
    #    if work_entries:
    #        work_entries.action_validate()

    #    self.write({'queued_for_pdf': True})
    #    payslip_cron = self.env.ref('hr_payroll.ir_cron_generate_payslip_pdfs', raise_if_not_found=False)
    #    if payslip_cron:
    #        payslip_cron._trigger()

    #    return

    def action_payslip_paid(self, paid_date=False):
        super().action_payslip_paid()

        if not paid_date:
            if any(slip.payslip_run_id for slip in self):
                self.write({'paid_date': self.payslip_run_id.payment_date,
                            'date': self.payslip_run_id.payment_date})
            else:
                self.write({'paid_date': fields.Date.today(),
                            'date': fields.Date.today()})

        self.filtered(lambda p: p.state != 'paid').write({
            'state': 'paid',
            'paid_date': paid_date,
            'date': paid_date,
            })

        return

    def send_hmrc_payslip(self):
        self.ensure_one()

        # payslip = self.env['hr.payslip'].search([
        #    ('id', '=', payslip_id),
        #    ("company_id", "=", self.company_id.id),
        #    ('state', 'in', ['done', 'paid']),
        # ])
        # line_values = payslip._get_line_values(['BASIC', 'PAYE', 'SLOAN', 'PLOAN'], compute_sum=True)
        _log.debug("Payslip=" + str(self.id))
        # record = self.env['hr_payslip'].search([('id', '=', self.id)])[0]
        # json_data = json.dumps(self.read)

        payslip_data = self.read(fields=['name', 'employee_id', 'contract_id', 'state', 'date_from', 'date_to'])
        payslip_lines_data = self._get_payslip_lines()

        payslip_data[0]['lines'] = payslip_lines_data

        payslip_json = json.dumps(payslip_data, default=str)

        # API endpoint URL
        # api_url = 'https://api.augursolutions.co.uk/payslip'
        api_url = 'http://192.168.0.15:1803/test'

        # Prepare headers for the request (if needed, e.g., for authentication)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer <YOUR_API_KEY>',  # Replace with your API key or authentication token
        }
        try:
            # Make the POST request to the external API
            response = requests.post(api_url, data=payslip_json, headers=headers, timeout=2)

            # Check the response status
            if response.status_code == 200:
                return self.with_context({
                    'status': 'success',
                    'message': 'Payslip data sent successfully.',
                    'response': response.json()  # The response from the external API, if any
                })
            else:
                return self.with_context({
                    'status': 'error',
                    'message': f'Failed to send data. Status code: {response.status_code}',
                    'error_details': response.text  # The error message from the API, if any
                })
        except requests.exceptions.Timeout as e:
            _log.error(f'Request timeout error while sending payslip data: {str(e)}')
            return self.with_context({
                'status': 'error',
                'message': 'Request timeout error while sending payslip data.',
                'error_details': str(e)
            })
        except requests.exceptions.RequestException as e:
            _log.error(f'Request error while sending payslip data: {str(e)}')
            return self.with_context({
                'status': 'error',
                'message': 'An error occurred while sending payslip data.',
                'error_details': str(e)
            })
        except Exception as e:
            _log.error(f'Unexpected error: {str(e)}')
            return self.with_context({
                'status': 'error',
                'message': 'An unexpected error occurred.',
                'error_details': str(e)
            })

    def _calcYTDEmploymentAllowance(self, localdict, amount):

        # payslip = localdict['payslip']

        # yearStart = payslip.company_id.get_last_ytd_reset_date(payslip.date_to)
        # yearEnd = payslip.company_id.get_last_ytd_reset_date(payslip.date_to) + relativedelta(years=+1, days=-1)

        # _log.info("Employment Allowance calculated = " + str(amount))
        # get YTD from paid / done slips
        # ytd = payslip._sum('NIC',str(yearStart),str(yearEnd))
        # if self.getPeriodNo(localdict) > 1:
        #    ytd += Payslip.l10n_uk_hmrc_employment_allowance

        # if ytd + amount > payslip._rule_parameter('UK_EMP_ALL'):
        #    amount = payslip._rule_parameter('UK_EMP_ALL') - ytd
        # else:
        #    ytd += amount

        # Payslip.l10n_uk_hmrc_employment_allowance += amount
        # _log.info("Employment Allowance Claimed = " + str(Payslip.l10n_uk_hmrc_employment_allowance))

        return amount

    def _get_regular_worked_hours(self):
        """
        Get the worked hours for the payslip except for the overtime hours.
        """
        self.ensure_one()
        overtime_days = self.worked_days_line_ids.filtered(lambda d: d.work_entry_type_id.code == 'OVERTIME')
    #    out_of_contract_days = self.worked_days_line_ids.filtered(lambda d: d.work_entry_type_id.code == 'OUT')
        return self.sum_worked_hours - sum(overtime_days.mapped("number_of_hours"))

    def _sum(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()

        self.env.cr.execute("""
                SELECT sum(pl.total)
                FROM hr_payslip as hp, hr_payslip_line as pl
                WHERE hp.employee_id = %s
                AND hp.state in ('done', 'paid')
                AND hp.paid_date >= %s
                AND hp.paid_date <= %s
                AND hp.id = pl.slip_id
                AND pl.code = %s""", (self.employee_id.id, from_date, to_date, code))
        res = self.env.cr.fetchone()
        return res and res[0] or 0.0

    def _sum_run(self, code, payrun_id):
        if payrun_id is None:
            return 0

        self.env.cr.execute("""
                SELECT sum(pl.total)
                FROM hr_payslip as hp, hr_payslip_line as pl
                WHERE hp.employee_id = %s
                AND hp.state in ('done', 'paid')
                AND hp.payslip_run_id = %s
                AND hp.id = pl.slip_id
                AND pl.code = %s""", (self.employee_id.id, payrun_id, code))
        res = self.env.cr.fetchone()
        return res and res[0] or 0.0

    def _sum_category(self, code, from_date, to_date=None):
        self.ensure_one()
        if to_date is None:
            to_date = fields.Date.today()

        self.env['hr.payslip'].flush_model(['employee_id', 'state', 'paid_date'])
        self.env['hr.payslip.line'].flush_model(['total', 'slip_id', 'salary_rule_id'])
        self.env['hr.salary.rule.category'].flush_model(['code'])

        self.env.cr.execute("""
                SELECT sum(pl.total)
                FROM
                    hr_payslip as hp,
                    hr_payslip_line as pl,
                    hr_salary_rule_category as rc,
                    hr_salary_rule as sr
                WHERE hp.employee_id = %s
                AND hp.state in ('done', 'paid')
                AND hp.paid_date >= %s
                AND hp.paid_date <= %s
                AND hp.id = pl.slip_id
                AND sr.id = pl.salary_rule_id
                AND rc.id = sr.category_id
                AND rc.code = %s""", (self.employee_id.id, from_date, to_date, code))
        res = self.env.cr.fetchone()
        return res and res[0] or 0.0

    def _sum_category_run(self, code, payrun_id):
        self.ensure_one()
        if payrun_id is None:
            return 0

        self.env['hr.payslip'].flush_model(['employee_id', 'state', 'paid_date'])
        self.env['hr.payslip.line'].flush_model(['total', 'slip_id', 'salary_rule_id'])
        self.env['hr.salary.rule.category'].flush_model(['code'])

        self.env.cr.execute("""
                SELECT sum(pl.total)
                FROM
                    hr_payslip as hp,
                    hr_payslip_line as pl,
                    hr_salary_rule_category as rc,
                    hr_salary_rule as sr
                WHERE hp.employee_id = %s
                AND hp.state in ('done', 'paid')
                AND hp.payslip_run_id = %s
                AND hp.id = pl.slip_id
                AND sr.id = pl.salary_rule_id
                AND rc.id = sr.category_id
                AND rc.code = %s""", (self.employee_id.id, payrun_id, code))
        res = self.env.cr.fetchone()
        return res and res[0] or 0.0


    def _sum_worked_days(self, code, from_date, to_date):
        self.ensure_one()

        query = """
             SELECT sum(hwd.amount)
             FROM hr_payslip hp, hr_payslip_worked_days hwd, hr_work_entry_type hwet
             WHERE hp.state in ('done', 'paid')
             AND hp.id = hwd.payslip_id
             AND hwet.id = hwd.work_entry_type_id
             AND hp.employee_id = %(employee)s
             AND hp.paid_date <= %(stop)s
             AND hwet.code = %(code)s
             AND hp.paid_date >= %(start)s"""

        self.env.cr.execute(query, {
            'employee': self.employee_id.id,
            'code': code,
            'start': from_date,
            'stop': to_date})
        res = self.env.cr.fetchone()
        return res[0] if res else 0.0

    def _get_period_name(self, cache):
        self.ensure_one()
        period_name = super()._get_period_name(cache)

        schedule = self.contract_id.schedule_pay or self.contract_id.structure_type_id.default_schedule_pay

        if schedule == 'weekly':
            # first date is not used, but retained for compatibility
            week_date = self.paid_date if self.paid_date else self.date_to
            wk_num = self._get_week_no(week_date)
            wk_num += 0 if self.paid_date else 1
            return _('Week %(week_number)s of %(year)s', week_number=wk_num, year=week_date.year)
        if schedule == 'monthly':
            return self._format_date_cached(cache, self.date_to, "MMMM Y")
        elif period_name:
            return period_name

        period_name = '%s - %s' % (
            self._format_date_cached(cache, self.date_from),
            self._format_date_cached(cache, self.date_to))

        return period_name

    def _get_payslip_lines(self):
        line_vals = []

        if any(self.mapped('ytd_computation')):
            last_ytd_payslips = self._get_last_ytd_payslips()
            code_set = set(self.struct_id.rule_ids.mapped('code'))
        else:
            last_ytd_payslips = defaultdict(lambda: self.env['hr.payslip'])
            code_set = set()
        ytd_payslips = reduce(
            lambda ytd_payslips, payslip: ytd_payslips | payslip, last_ytd_payslips.values(),
            self.env['hr.payslip']
        )

        line_values = ytd_payslips._get_line_values(code_set, ['ytd'])

        for payslip in self:
            if not payslip.contract_id:
                raise UserError(
                    _("There's no contract set on payslip %(payslip)s for %(employee)s. Check that there is at least a contract set on the employee form.",
                      payslip=payslip.name, employee=payslip.employee_id.name))

            localdict = self.env.context.get('force_payslip_localdict', None)
            if localdict is None:
                localdict = payslip._get_localdict()

            rules_dict = localdict['rules']
            result_rules_dict = localdict['result_rules']

            blacklisted_rule_ids = self.env.context.get('prevent_payslip_computation_line_ids', [])

            result = {}
            for rule in sorted(payslip.struct_id.rule_ids, key=lambda x: x.sequence):
                if rule.id in blacklisted_rule_ids:
                    continue
                localdict.update({
                    'result': None,
                    'result_qty': 1.0,
                    'result_rate': 100,
                    'result_name': False
                })
                if rule._satisfy_condition(localdict):
                    # Retrieve the line name in the employee's lang
                    employee_lang = payslip.employee_id.lang or self.env.lang
                    # This actually has an impact, don't remove this line
                    if rule.code in localdict['same_type_input_lines']:
                        for multi_line_rule in localdict['same_type_input_lines'][rule.code]:
                            localdict['inputs'][rule.code] = multi_line_rule
                            amount, qty, rate = rule._compute_rule(localdict)
                            tot_rule = payslip._get_payslip_line_total(amount, qty, rate, rule)

                            result_rules_dict[rule.code]['total'] += tot_rule
                            result_rules_dict[rule.code]['amount'] += tot_rule
                            result_rules_dict[rule.code]['quantity'] = 1
                            result_rules_dict[rule.code]['rate'] = 100
                            rules_dict[rule.code] = rule

                            localdict = rule.category_id._sum_salary_rule_category(localdict,
                                                                                   tot_rule)
                            rule_name = payslip._get_rule_name(localdict, rule, employee_lang)
                            line_vals.append({
                                'sequence': rule.sequence,
                                'code': rule.code,
                                'name': rule_name,
                                'salary_rule_id': rule.id,
                                'contract_id': localdict['contract'].id,
                                'employee_id': localdict['employee'].id,
                                'amount': amount,
                                'quantity': qty,
                                'rate': rate,
                                'total': tot_rule,
                                'slip_id': payslip.id,
                                'ytd': line_values[rule.code][last_ytd_payslips[payslip].id]
                                       ['ytd'] + tot_rule,
                            })

                        input_line_ids = localdict['same_type_input_lines'][rule.code].ids
                        localdict['inputs'][rule.code] = self.__get_aggregator_hr_payslip_input_model()(
                            env=self.env, ids=input_line_ids, prefetch_ids=input_line_ids,
                        )
                    else:
                        amount, qty, rate = rule._compute_rule(localdict)
                        # check if there is already a rule computed with that code
                        previous_amount = localdict.get(rule.code, 0.0)
                        # set/overwrite the amount computed for this rule in the localdict
                        tot_rule = payslip._get_payslip_line_total(amount, qty, rate, rule)
                        localdict[rule.code] = tot_rule
                        result_rules_dict[rule.code] = {'total': tot_rule, 'amount': amount, 'quantity': qty,
                                                        'rate': rate}
                        rules_dict[rule.code] = rule
                        # sum the amount for its salary category
                        localdict = rule.category_id._sum_salary_rule_category(localdict, tot_rule - previous_amount)
                        rule_name = payslip._get_rule_name(localdict, rule, employee_lang)
                        # create/overwrite the rule in the temporary results
                        result[rule.code] = {
                            'sequence': rule.sequence,
                            'code': rule.code,
                            'name': rule_name,
                            'salary_rule_id': rule.id,
                            'contract_id': localdict['contract'].id,
                            'employee_id': localdict['employee'].id,
                            'amount': amount,
                            'quantity': qty,
                            'rate': rate,
                            'total': tot_rule,
                            'slip_id': payslip.id,
                            'ytd': line_values[rule.code][last_ytd_payslips[payslip].id]
                                   ['ytd'] + tot_rule,
                        }

            line_vals += list(result.values())
        return line_vals

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    payment_date = fields.Date(string='Paid Date', required=True,
        default=lambda self: fields.Date.to_string((datetime.now().date())))
    # temporarily to avoid errors
    paid_date = fields.Date(string='Paid Date', required=True,
                               default=lambda self: fields.Date.to_string((datetime.now().date())))

    def action_paid(self):
        # self.mapped('slip_ids').action_payslip_paid(self.paid_date)
        #self.write({'state': 'paid'})
        super().action_paid()
        self.slip_ids.write({'paid_date': self.paid_date,
                             'date': self.paid_date})

    def action_open(self):
        super().action_open()
        self.slip_ids.write({'payment_date': self.paid_date,
                             'date': self.paid_date,
                             'state': 'verify'})

    def action_draft(self):
        super().action_draft()
        self.slip_ids.write({'payment_date': self.paid_date,
                             'date': self.paid_date})

class PayslipPaymentWizard(models.TransientModel):
    _name = 'payslip.payment.wizard'
    _description = 'Enter Payment Date for Payslip'

    payment_date = fields.Date(string="Payment Date", required=True)
    payslip_id = fields.Many2one('hr.payslip', required=True)

    def confirm_payment(self):
        self.payslip_id.write({
            'payment_date': self.payment_date,
            'state': 'paid'
        })
        return {'type': 'ir.actions.act_window_close'}
