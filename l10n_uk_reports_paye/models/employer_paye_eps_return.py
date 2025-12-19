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

from odoo.exceptions import RedirectWarning
from odoo.fields import Command

import logging

from odoo.tools import float_repr

_log = logging.getLogger(__name__)


class employer_paye_eps_return(models.Model):
    _name = "employer_paye_eps_return"
    _description = "Holds employers PAYE data during a EPS return"

    currency_id = fields.Many2one(comodel_name='res.currency',
                                  default=lambda self: self.env['res.currency'].search([('name', '=', 'GBP')], limit=1))
    transaction_id = fields.Many2many(comodel_name='l10n_uk.hmrc.transaction', string='Transactions')

    inactivity_indicator = fields.Boolean()
    information_correct = fields.Boolean()
    hmrc_paye_password = fields.Char(string="PAYE password", store=True)
    use_wrong_period = fields.Boolean()
    already_submitted_period = fields.Boolean()

    if fields.Date.today().day > 5:
        increment = 0
    else:
        increment = -1
    _log.debug("Increment: " + str(increment))

    date_from = fields.Date(string='From date', default=fields.Date.today() + relativedelta(months=increment, day=6))
    date_to = fields.Date(string='To date', default=fields.Date.today() + relativedelta(months=increment + 1, day=5))

    def generate_paye_eps(self):
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
        year_start = self.env.company.get_last_ytd_reset_date(self.date_to)
        payslips = self.env['hr.payslip'].search([('state', 'in', ['paid']),
                                                  ('paid_date', '>=', year_start),
                                                  ('paid_date', '<=', self.date_to),
        #                                          ('l10n_uk_hmrc_status', 'in', ['S', 'V']),
                                                  ('company_id', '=', self.env.company.id)])

        transaction_create_vals = {
            'transaction_type': 'paye_eps_return',
            'period_start': self.date_from,
            'period_end': self.date_to,
            'company_id': self.env.company.id,
            # 'inactivity_indicator': self.inactivity_indicator,
            # 'user_id': self.env.user.id,
        }

        employer_credentials = {
            'sender_id': self.env.company.l10n_uk_hmrc_sender_id,
            'password': self.hmrc_paye_password,
            'tax_office_number': self.env.company.l10n_uk_hmrc_tax_office_number,
            'tax_office_reference': self.env.company.l10n_uk_hmrc_tax_office_reference,
            'accounts_office_reference': self.env.company.l10n_uk_hmrc_account_office_reference,
            'unique_taxpayer_reference': self.env.company.l10n_uk_hmrc_unique_taxpayer_reference,
        }

        related_tax_year = '24-25'

        smp_recovered = float(0.00)
        spp_recovered = float(0.00)
        sap_recovered = float(0.00)
        shpp_recovered = float(0.00)
        spbp_recovered = float(0.00)
        sncp_recovered = float(0.00)
        smp_nic_recovered = float(0.00)
        spp_nic_recovered = float(0.00)
        sap_nic_recovered = float(0.00)
        shpp_nic_recovered = float(0.00)
        spbp_nic_recovered = float(0.00)
        sncp_nic_recovered = float(0.00)
        employment_allowance = float(0.00)
        cis_suffered = float(0.00)  # TODO: Link CIS

        year_start = self.env.company.get_last_ytd_reset_date(self.date_to)
        period_no = relativedelta(self.date_to, year_start).months + 1
        _log.debug("Period: " + str(self.date_to) + " / " + str(period_no))
        _log.debug("Rate: " + str(self.env.ref('l10n_uk_hr_payroll.rule_parameter_UK_SPL_SE_Rate')))

        if self.env.company.l10n_uk_hmrc_small_employer:
            rate = float(self.env['hr.rule.parameter']._get_parameter_from_code('UK_SPL_SE_RATE', self.date_to)) / 100
        else:
            rate = float(self.env['hr.rule.parameter']._get_parameter_from_code('UK_SPL_RATE', self.date_to)) / 100

        _log.debug("rate: " + str(rate))
        for payslip in payslips:
            smp_recovered += float(float_repr(payslip._sum('SMP', year_start, self.date_to) * rate, 2))
            spp_recovered += float(float_repr(payslip._sum('SPP', year_start, self.date_to) * rate, 2))
            sap_recovered += float(float_repr(payslip._sum('SAP', year_start, self.date_to) * rate, 2))
            shpp_recovered += float(float_repr(payslip._sum('SPL', year_start, self.date_to) * rate, 2))
            spbp_recovered += float(float_repr(payslip._sum('SPB', year_start, self.date_to) * rate, 2))
            sncp_recovered += float(float_repr(payslip._sum('SNP', year_start, self.date_to) * rate, 2))
            # TODO NIC recovery calculation
            smp_nic_recovered += float(float_repr(payslip._sum('SMP', year_start, self.date_to) * rate, 2))
            spp_nic_recovered += float(float_repr(payslip._sum('SPP', year_start, self.date_to) * rate, 2))
            sap_nic_recovered += float(float_repr(payslip._sum('SAP', year_start, self.date_to) * rate, 2))
            shpp_nic_recovered += float(float_repr(payslip._sum('SPL', year_start, self.date_to) * rate, 2))
            spbp_nic_recovered += float(float_repr(payslip._sum('SPB', year_start, self.date_to) * rate, 2))
            sncp_nic_recovered += float(float_repr(payslip._sum('SNP', year_start, self.date_to) * rate, 2))
            employment_allowance += float(float_repr(payslip._sum('NIC', year_start, self.date_to) * rate, 2))

        # Do not claim more than the maximum for the year
        if (employment_allowance >= float(
                float_repr(self.env['hr.rule.parameter']._get_parameter_from_code('UK_EMP_ALL', self.date_to), 2))):
            employment_allowance = float(
                float_repr(self.env['hr.rule.parameter']._get_parameter_from_code('UK_EMP_ALL', self.date_to), 2))

        _log.info("Employment Allowance: " + str(employment_allowance))
        _log.info("Use Employment Allowance: " + str(self.env.company.l10n_uk_hmrc_employment_allowance))

        document_data = {
            # 'inactivity_indicator': inactivity_indicator,
            'period_end': self.date_to,
            'related_tax_year': related_tax_year,
            'smp_recovered': smp_recovered,
            'spp_recovered': spp_recovered,
            'sap_recovered': sap_recovered,
            'shpp_recovered': shpp_recovered,
            'spbp_recovered': spbp_recovered,
            'sncp_recovered': sncp_recovered,
            'smp_nic_recovered': smp_nic_recovered,
            'spp_nic_recovered': spp_nic_recovered,
            'sap_nic_recovered': sap_nic_recovered,
            'shpp_nic_recovered': shpp_nic_recovered,
            'spbp_nic_recovered': spbp_nic_recovered,
            'sncp_nic_recovered': sncp_nic_recovered,
            'cis_suffered': cis_suffered,
            'employment_allowance': employment_allowance,
            'use_employment_allowance': self.env.company.l10n_uk_hmrc_employment_allowance,
            'apprenticeship_level_due_ytd': False,  # TODO: Link Apprenticeship Levy
            'tax_month': period_no,
            'apprenticeship_annual_allowance': False,  # TODO: Link Apprenticeship Levy
        }

        _log.info("Attempting to Send EPS Return")

        transaction = self.env['l10n_uk.hmrc.transaction'].create({
            'transaction_type': 'paye_eps_return',
            'period_start': self.date_from,
            'period_end': self.date_to,
            'company_id': self.env.company.id,
            'sender_user_id': self.env.user.id,
        })

        transaction.sudo()._submit_eps_mr_transaction(
            credentials={
                'sender_id': self.env.company.l10n_uk_hmrc_sender_id,
                'password': self.hmrc_paye_password,
                'accounts_office_reference': self.env.company.l10n_uk_hmrc_account_office_reference,
                'tax_office_number': self.env.company.l10n_uk_hmrc_tax_office_number,
                'tax_office_reference': self.env.company.l10n_uk_hmrc_tax_office_reference,
                # 'paye_reference': self.env.company.l10n_uk_hmrc_paye_ref, # not used
                'unique_taxpayer_reference': self.env.company.l10n_uk_hmrc_unique_taxpayer_reference,

            },  # or employer_credentials
            document_data=document_data,
        )

        return True
