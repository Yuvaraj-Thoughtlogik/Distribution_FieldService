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


from odoo import fields, models, api, _
from odoo.exceptions import UserError
import logging

_log = logging.getLogger(__name__)


class l10n_uk_hr_payroll_pension_fund(models.Model):
    _name = "l10n_uk_pension_fund"
    _description = "Pension Fund"

    name = fields.Char(string='Pension Fund Name',groups='account.group_account_manager',)
    pension_street = fields.Char(string='Pension Address',groups='account.group_account_manager',)
    pension_street2 = fields.Char(string='Pension Address Line 2',groups='account.group_account_manager',)
    pension_city = fields.Char(string='Pension City',groups='account.group_account_manager',)
    pension_state_id = fields.Many2one('res.country.state', default='C5', string='Pension State',
                                       groups='account.group_account_manager',)
    pension_zip = fields.Char(string='Pension Post Code', groups='account.group_account_manager',)
    pension_country_id = fields.Many2one('res.country', default=231, string='Pension Country',
                                         groups='account.group_account_manager',)
    pension_email = fields.Char(string='Pension Email', groups='account.group_account_manager',)
    pension_phone = fields.Char(string='Pension Phone', groups='account.group_account_manager',)
    fund_type = fields.Selection([
        ("D", "Direct Pay - the Employer claims tax relief"),
        ("R", "Relief at Source - the Pension Provider claims the tax relief"),
    ],
        default="R", required=True,groups='account.group_account_manager',
        readonly=False, string="Pension Fund Type")
    company_ids = fields.One2many('l10n_uk_pension_fund_company', 'pension_fund_id',
                                  string='Company',
                                  groups='account.group_account_manager',)
    #@api.model
    #def default_get(self, field_list=None):
    #    if self.env.company.country_id.code != "GB":
    #        raise UserError(_('You must be logged in a UK company to use this feature'))
    #    return super().default_get(field_list)

class l10n_uk_hr_payroll_pension_fund_company(models.Model):
    _name = "l10n_uk_pension_fund_company"
    _description = "Pension Fund for a Company"

    company_id = fields.Many2one('res.company', string='Company',
                                 groups='account.group_account_manager',)
    pension_fund_id = fields.Many2one('l10n_uk_pension_fund', string='Pension',
                                      groups='account.group_account_manager',)
    employer_ref = fields.Char(string='Employer Reference',
                               groups='account.group_account_manager',)
    payment_source = fields.Char(string='Payment Source',
                                 groups='account.group_account_manager',)
    banded_earnings = fields.Boolean(string='Use Banded Earnings',
                                    help='Applies the statutory upper and lower limits to calculate qualifying earnings',
                                    default=True,
                                    groups='account.group_account_manager',)
    include_allowances = fields.Boolean(string='Include Allowances',
                                    help='Include Allowances in the qualifying earnings calculations',
                                    default=True,
                                    groups = 'account.group_account_manager',)


    @api.model
    def default_get(self, field_list=None):
        if self.env.company.country_id.code != "GB":
            raise UserError(_('You must be logged in a UK company to use this feature'))
        return super().default_get(field_list)
