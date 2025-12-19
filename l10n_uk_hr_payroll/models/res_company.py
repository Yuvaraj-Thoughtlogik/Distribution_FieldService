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


import logging

from odoo import api, fields, models, _
from odoo.tools import ormcache
from odoo.exceptions import ValidationError
# from odoo.addons.l10n_uk_hmrc.tools.field_verification import validate_crn

import calendar
from datetime import date
from dateutil.relativedelta import relativedelta



class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_uk_hmrc_is_employer = fields.Boolean(string='Is the company an employer',
                                              help='Allow edit of HMRC Employer references',
                                              groups='account.group_account_manager')

    l10n_uk_hmrc_paye_ref = fields.Char(string='Employer PAYE Reference',
                                        help='HMRC provided Employer Payment Reference when you registered as an employer',
                                        groups='account.group_account_manager')

    l10n_uk_hmrc_small_employer = fields.Boolean(string='Claim Small Employers Relief',
                                                 help='Usually applies to companies that have paid £45k or less in class 1 NICs in the last Tax Year',
                                                 groups='account.group_account_manager')

    l10n_uk_hmrc_employment_allowance = fields.Boolean(string='Claim Employment Allowance',
                                                       help='Usually applies to companies that have paid £100k or less in class 1 NICs in the last Tax Year',
                                                       tracking=True,
                                                       groups='account.group_account_manager')

    l10n_uk_hmrc_employment_allowance_ytd = fields.Float(string='YTD Employment Allowance Claimed',
                                                         help='This will display how much employment allowance has been claimed in each year',
                                                         groups='account.group_account_manager',
                                                         default=0.0, readonly=True)

    l10n_uk_hmrc_paye_ceased = fields.Date(string='Date Scheme Ceased',
                                                         help='This is the date the PAYE scheme ceased',
                                                         groups='account.group_account_manager',
                                                         tracking=True)

    l10n_uk_employees = fields.Integer(compute="_get_workers_count", string="Employees", store=False,
                                       groups='account.group_account_manager', default=0)
    l10n_uk_pensionable_earnings = fields.Selection([
        ('P', 'Basic Pay'),
        ('Q', 'Qualifying Earnings'),
        ('T', 'Total Earnings'),
        ('B', 'Banded Earnings')],
        default = 'Q', string = 'Pensionable Earnings Basis', tracking=True, groups='account.group_account_manager')
    #    ytd_reset_day = fields.Integer(
    #        default=6,
    #        string='YTD Reset Day of the month',
    #        help="""Day where the YTD will be reset every year. If zero or negative, then the first day of the month will be selected instead.
    #            If greater than the last day of a month, then the last day of the month will be selected instead.""")

    #    ytd_reset_month = fields.Selection([
    #        ('1', 'January'),
    #        ('2', 'February'),
    #        ('3', 'March'),
    #        ('4', 'April'),
    #        ('5', 'May'),
    #        ('6', 'June'),
    #        ('7', 'July'),
    #        ('8', 'August'),
    #        ('9', 'September'),
    #        ('10', 'October'),
    #        ('11', 'November'),
    #        ('12', 'December')],
    #        default='4', string='YTD Reset Month')

    #    @api.constrains('ytd_reset_day', 'ytd_reset_month')
    #    def _check_valid_reset_date(self):
    #        for company in self:
    #            # We try if the date exists in 2023, which is not a leap year.
    #            max_possible_day = calendar.monthrange(2023, int(company.ytd_reset_month))[1]
    #            if company.ytd_reset_day < 1 or company.ytd_reset_day > max_possible_day:
    #                raise ValidationError(self.env._(
    #                    "The YTD reset day must be a valid day of the month : since the current month is %(month)s, it should be between 1 and %(day)s.",
    #                    month=company._fields['ytd_reset_month'].selection[int(company.ytd_reset_month) - 1][1],
    #                    day=max_possible_day
    #                    ))
    # def _has_hmrc_fields_filled(self):
    #    self.ensure_one()
    #    #return self.l10n_uk_hmrc_utr or self.l10n_uk_hmrc_account_office_reference \
    #    #    or self.hmrc_cis_sender_id or self.l10n_uk_hmrc_tax_office_number \
    #    #    or self.l10n_uk_hmrc_tax_office_reference
    #    return self.hmrc_cis_sender_id or self.l10n_uk_hmrc_tax_office_number \
    #        or self.l10n_uk_hmrc_tax_office_reference

    def _get_workers_count(self):
        contract = self.env['hr.contract']
        today = fields.Date.today()

        for company in self:
            company.l10n_uk_employees = contract.search_count([
                ('company_id', '=', company.id),
                ('state', '=', 'open'),  # Odoo’s standard “active” state
                ('date_start', '<=', today),
                '|',
                ('date_end', '=', False),
                ('date_end', '>=', today),
            ])

#    def get_last_ytd_reset_date(self, target_date):
#        self.ensure_one()
#        last_ytd_reset_date = date(target_date.year, int(self.ytd_reset_month), self.ytd_reset_day)
#        if last_ytd_reset_date > target_date:
#            last_ytd_reset_date += relativedelta(years=-1)
#        return last_ytd_reset_date

    # override as we need to accommodate the use case where there are no payroll records, but we want to close a scheme
    # and therefore send through an FPS without ay payslips
    def get_last_ytd_reset_date(self, target_date):
            self.ensure_one()
            if not target_date:
                target_date = fields.Date.today()

            last_ytd_reset_date = date(target_date.year, int(self.ytd_reset_month), self.ytd_reset_day)
            if last_ytd_reset_date > target_date:
                last_ytd_reset_date += relativedelta(years=-1)
            return last_ytd_reset_date
