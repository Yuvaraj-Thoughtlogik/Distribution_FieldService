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


from collections import defaultdict
from datetime import date
from functools import reduce
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError
import logging

from dateutil.relativedelta import relativedelta
import re

# from odoo.addons.l10n_uk_hmrc.tools.field_verification import validate_national_insurance_number
# from odoo.addons.l10n_uk_hmrc.tools import field_verification

_log = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Tax Code
    l10n_uk_tax_code = fields.Char('Tax Code', default='1257L', groups="hr_payroll.group_hr_payroll_user", tracking=True)
    # Process the Tax code in to parts
    l10n_uk_taxcode_prefix = fields.Char('Tax Code Prefix', groups="hr_payroll.group_hr_payroll_user", readonly=True, store=True)
    l10n_uk_taxcode_suffix = fields.Char('Tax Code Suffix', groups="hr_payroll.group_hr_payroll_user", readonly=True, store=True)
    l10n_uk_taxcode_numeric = fields.Integer('Tax Code Numeric', groups="hr_payroll.group_hr_payroll_user", readonly=True,
                                             compute='_compute_l10n_uk_taxcode', default=1257, store=True)
    l10n_uk_taxcode_emergency = fields.Boolean('Emergency Tax', groups="hr_payroll.group_hr_payroll_user", readonly=False,
                                               default=False)
    l10n_uk_taxcode_w1m1 = fields.Boolean('W1/M1 Indicator', groups="hr_payroll.group_hr_payroll_user",
                                               readonly=False, default=False)
    l10n_uk_tax_regime = fields.Selection([
        ('_', 'England/N.I.'),
        ('C', 'Wales'),
        ('S', 'Scotland'),
        ], default="_",
        groups="hr_payroll.group_hr_payroll_user")

    #l10n_uk_taxcode_ytd_basis = fields.Boolean('YTD Basis', groups="hr_payroll.group_hr_payroll_user", readonly=True,
    #                                           default=True)
    l10n_uk_surname = fields.Char('Surname', groups="hr_payroll.group_hr_payroll_user", readonly=True, store=True,
                                  compute='_compute_l10n_uk_name_fields')
    l10n_uk_forename = fields.Char('Forename', groups="hr_payroll.group_hr_payroll_user", readonly=True, store=True,
                                  compute='_compute_l10n_uk_name_fields')
    l10n_uk_second_forename = fields.Char('Second Name', groups="hr_payroll.group_hr_payroll_user", readonly=True, store=True,
                                  compute='_compute_l10n_uk_name_fields')

    l10n_uk_age = fields.Char('Current Age', groups="hr_payroll.group_hr_payroll_user", readonly=True, store=False,
                                  compute='_compute_l10n_uk_age')
    # Current Year - Past employer
    past_employer_pay = fields.Monetary(default='0', store=True, groups="hr_payroll.group_hr_payroll_user")
    past_employer_tax = fields.Monetary(default='0', store=True, groups="hr_payroll.group_hr_payroll_user")
    past_employer_employee_ni = fields.Monetary(default='0', store=True, groups="hr_payroll.group_hr_payroll_user")
    past_employer_employer_ni = fields.Monetary(default='0', store=True, groups="hr_payroll.group_hr_payroll_user")

    # Student Loan
    has_student_loan = fields.Boolean(default=False, string='Student Loan', groups="hr_payroll.group_hr_payroll_user",
                                      help='Is this Contract subject to a Student Loan', store=True, tracking=True)
    student_loan_plan = fields.Selection([
        ('1', 'Plan 1'),
        ('2', 'Plan 2'),
        ('4', 'Plan 4'),
        ('5', 'Plan 5'),
    ],
        default="1", required=False, store=True, groups="hr_payroll.group_hr_payroll_user",
        readonly=False, string="Loan Plan")

    # Post Graduate loan
    has_post_graduate_loan = fields.Boolean(default=False, string='Post-Graduate Loan', store=True,
                                            groups = "hr_payroll.group_hr_payroll_user",
                                            help='Is this Contract subject to a Post-Graduate Loan')

    # National Insurance Number
    l10n_uk_ni_code = fields.Char('National Insurance No', default='QQ123456B',
                                  compute='_check_l10n_uk_hmrc_national_insurance_number',
                                  store=True, readonly=False, groups="hr_payroll.group_hr_payroll_user", tracking=True)

    # https://www.gov.uk/national-insurance-rates-letters/category-letters
    l10n_uk_ni_letter = fields.Selection(
        [
            ("A", "(A) All employees apart from those in groups B, C, H, J, M, V and Z"),
            ("B", "(B) Married women and widows entitled to pay reduced National Insurance"),
            ("C", "(C) Employees over the State Pension age"),
            ("H", "(H) Apprentices under 25"),
            ("J", "(J) Employees who can defer National Insurance because they’re already paying it in another job"),
            ("M", "(M) Employees under 21"),
            ("V", "(V) Employees who are working in their first job since leaving the armed forces (veterans)"),
            ("Z",
             "(Z) Employees under 21 who can defer National Insurance because they’re already paying it in another job"),

            # Category letters for employees who work in freeports
            # Employers use category letters F, I, L and S for employees who work in a freeport.
            ("F", "(F) All employees who work in freeports, apart from those in groups I, L, and S in this table"),
            ("I",
             "(I) Married women and widows who work in freeports and are entitled to pay reduced National Insurance"),
            ("L",
             "(L) Employees who work in freeports and can defer National Insurance because they’re already paying it in another job"),
            ("S", "(S) Employees who work in freeports and are over the State Pension age"),

            # Category letters for employees who work in investment zones
            # Employers use category letters N, E, D and K for employees who work in an investment zone.
            ("N",
             "(N) All employees who work in investment zones, apart from those in groups E, D and K in this table"),
            ("E",
             "(E) Married women and widows who work in investment zones and are entitled to pay reduced National Insurance"),
            ("D",
             "(D) Employees who work in investment zones and can defer National Insurance because they’re already paying it in another job"),
            ("K", "(K) Employees who work in investment zones and are over State Pension age"),

            # Category letter X
            # Employers use category letter X for employees who do not have to pay National Insurance, for example because they’re under 16.
            # X will retain tax = 0 as it will not be caught by any of the above rules
            ("X", "(X) Employees who do not have to pay National Insurance"),
        ],
        default="A", required=True, tracking=True,
        groups="hr_payroll.group_hr_payroll_user",
        readonly=False, string="National Insurance Letter")

    @api.constrains('name')
    def _compute_l10n_uk_name_fields(self):
        for employee in self:
            if employee.name and employee.company_country_code == 'GB':
                employee_split_name = employee.name.split(' ', 2) # Maximum 3 splits
                if len(employee_split_name) == 1:
                    employee.l10n_uk_surname = employee_split_name[0]
                    employee.l10n_uk_forename = ''          # clear this if there is only one name detected
                    employee.l10n_uk_second_forename = ''   # clear this if there is only one name detected
                elif len(employee_split_name) == 2:
                    employee.l10n_uk_forename = employee_split_name[0]
                    employee.l10n_uk_second_forename = ''   # clear this if there are only two names detected
                    employee.l10n_uk_surname = employee_split_name[1]
                elif len(employee_split_name) == 3:
                    employee.l10n_uk_forename = employee_split_name[0]
                    employee.l10n_uk_second_forename = employee_split_name[1]
                    employee.l10n_uk_surname = employee_split_name[2]

    @api.constrains('l10n_uk_ni_code')
    def _check_l10n_uk_hmrc_national_insurance_number(self):
        for record in self:
            if record.l10n_uk_ni_code and record.company_country_code == 'GB':
                if len(record.l10n_uk_ni_code) == 8:  # UK national insurance number can be 8 characters long in some cases, but the xml spec for the cis needs a length of 9 with an empty space if needed
                    record.l10n_uk_ni_code += ' '
                # todo need to relocate this inside the module to remove the dependency
                # field_verification.validate_national_insurance_number(record.l10n_uk_ni_code)

    @api.constrains('birthday')
    def _compute_l10n_uk_age(self):
        for employee in self:
            if employee.birthday and employee.company_country_code == 'GB':
                today = date.today()
                delta = relativedelta(today, employee.birthday)
                employee.l10n_uk_age = f"{delta.years} years, {delta.months} months, {delta.days} days"
            else:
                employee.l10n_uk_age = 0

    @api.depends('l10n_uk_tax_code')
    def _compute_l10n_uk_taxcode(self):
        _log.info("Processing Tax Code")
        for record in self:
            if record.company_country_code == 'GB':
                if record.l10n_uk_tax_code:
                    taxcode = str(record.l10n_uk_tax_code)


                    # 3 Character Tax Code Prefixes
                    if taxcode[0:3] in ('SD2', 'SD3', 'C0T', 'CBR', 'S0T', 'SBR', 'SD0', 'CD0', 'CD1', 'SD1'):
                        _log.debug("Processing taxcode: " + str(taxcode[0:3]))
                        record.l10n_uk_taxcode_prefix = taxcode[0:3]
                        record.l10n_uk_taxcode_suffix = ''
                        firstDigit = re.search(r'\d+', taxcode[3:len(taxcode)])
                        firstDigit = 3
                        if len(taxcode) == firstDigit:
                            record.l10n_uk_taxcode_numeric = 0
                        else:
                            record.l10n_uk_taxcode_numeric = int(taxcode[3:len(taxcode)].strip('AFHMNVBEIDJLZSCTX'))

                        if taxcode[0:1] in ('S','C'):
                            record.l10n_uk_tax_regime = taxcode[0:1]

                    # 2 Character Tax Code Prefixes
                    elif taxcode[0:2] in ('BR', '0T', 'D0', 'D1', 'NK', 'SK', 'CK', 'NT'):
                        _log.info("Processing taxcode: " + str(taxcode[0:2]))
                        record.l10n_uk_taxcode_prefix = taxcode[0:2]
                        record.l10n_uk_taxcode_suffix = ''
                        # firstDigit = re.search(r'\d+', TaxCode[2:length])
                        firstDigit = 2
                        if len(taxcode) == 2:
                            record.l10n_uk_taxcode_numeric = 0
                        else:
                            record.l10n_uk_taxcode_numeric = int(taxcode[2:len(taxcode)].strip('AFHMNVBEIDJLZSCTX'))

                        if taxcode[0:1] in ('S','C'):
                            record.l10n_uk_taxcode_suffix = ''
                            record.l10n_uk_tax_regime = taxcode[0:1]

                    # 1 Character Tax Code Prefixes
                    elif taxcode[0:1] in ('K', 'S', 'C'):
                        _log.info("Processing taxcode: " + str(taxcode[0:1]))
                        record.l10n_uk_taxcode_prefix = taxcode[0:1]
                        record.l10n_uk_taxcode_numeric = int(taxcode[1:len(taxcode)].strip('AFHMNVBEIDJLZSCTX'))
                        if taxcode[0:1] in ('K') or taxcode[-1].isnumeric():
                            record.l10n_uk_taxcode_suffix = ''
                            record.l10n_uk_tax_regime = "_" # England & N.I.
                        else:
                            # Must be in S or C
                            record.l10n_uk_taxcode_suffix = taxcode[-1]
                            record.l10n_uk_tax_regime = taxcode[0:1]
                    else:
                        firstDigit = re.search(r'\d+', taxcode)  # digits
                        lastChar = taxcode[-1]
                        if lastChar.isalpha():
                            record.l10n_uk_taxcode_suffix = lastChar

                        record.l10n_uk_tax_regime = "_"  # England & N.I.

                        if firstDigit and firstDigit.start() > 0:  # not first - otherwise no prefix (as 0T has been handled above)
                            record.l10n_uk_taxcode_prefix = taxcode[0:firstDigit.start()]
                            record.l10n_uk_taxcode_numeric = int(taxcode.strip('AFHMNVBEIDJLZSCTX'))
                        else:  # starts with a character
                            record.l10n_uk_taxcode_prefix = ''
                            firstChar = re.search(r'\D+', taxcode)
                            if firstChar:
                                record.l10n_uk_taxcode_numeric = int(taxcode[0:firstChar.start()])
                            else:  # Error - doesn't start with a character or a number
                                _log.info("Tax Code Processing Error: " + taxcode)

                    # _log.debug("Numeric: " + str(record.l10n_uk_taxcode_numeric) + " / Prefix: " + record.l10n_uk_taxcode_prefix)

                    if record.l10n_uk_taxcode_prefix:
                        if record.l10n_uk_taxcode_numeric == 0:
                            start = len(record.l10n_uk_taxcode_prefix)
                        else:
                            start = len(str(record.l10n_uk_taxcode_numeric)) + len(record.l10n_uk_taxcode_prefix)
                    else:
                        start = len(str(record.l10n_uk_taxcode_numeric))

                    _log.info("Start: " + str(start))

                    if record.l10n_uk_taxcode_numeric:
                        _log.info("Numeric: " + str(record.l10n_uk_taxcode_numeric))
                    if record.l10n_uk_taxcode_prefix:
                        _log.info("Prefix: " + record.l10n_uk_taxcode_prefix)
                    if record.l10n_uk_taxcode_suffix:
                        _log.info("Suffix: " + record.l10n_uk_taxcode_suffix)
                else:
                    _log.info("Tax Code is Empty")

    @api.depends('l10n_uk_tax_code')
    def _uk_compute_tax_code_letter(self):
        characters = dict.fromkeys([',', '.', '-', ' '], '')
        numbers = dict.fromkeys(['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'], '')
        for record in self:
            if record.company_country_code == 'GB':
                record.l10n_uk_tax_code_letter = "X"
                record.l10n_uk_tax_code_amount = 1234

    @api.depends('l10n_uk_ni_letter')
    def _uk_compute_ni_letter(self):
        # Length must be 1 and characters must be one of  A, B, C, H, J, M, V, Z, F, I, L, S, N, E, D, K or X
        for employee in self:
            if employee.l10n_uk_ni_letter and employee.company_country_code == 'GB' and len(
                    employee.l10n_uk_ni_letter) == 1:
                if employee.l10n_uk_ni_letter not in ("A", "B", "C", "H", "J", "M", "V", "Z", "F", "I", "L", "S", "N",
                                                      "E", "D", "K", "X"):
                    employee.l10n_uk_ni_letter = "0"  # Invalid

    @api.depends('l10n_uk_ni_code')
    def _uk_compute_ni_code(self):
        characters = dict.fromkeys([',', '.', '-', ' '], '')
        for employee in self:
            if employee.l10n_uk_ni_code and employee.company_country_code == 'GB':
                employee.l10n_uk_ni_code = reduce(lambda a, kv: a.replace(*kv), characters.items(),
                                                  employee.l10n_uk_ni_code)

    @api.model
    def _validate_ni(self, l10n_uk_ni_code):

        try:
            test = l10n_uk_ni_code[:-2]
            if test[0] in ['0', '1', '2', '3', '4', '5']:  # Should be good for several years
                test = '2%s' % test
            checksum = int(l10n_uk_ni_code[-2:])
            if checksum != (97 - int(test) % 97):
                raise Exception()
            return True
        except Exception:
            return False

    def _is_ni_valid(self):
        # https://en.wikipedia.org/wiki/National_Insurance_number
        # a sequence of  two prefix letters, six digits and one suffix letter.
        # An example is QQ123456C

        l10n_uk_ni_code = self.l10n_uk_ni_code
        if not l10n_uk_ni_code or len(l10n_uk_ni_code) != 9:
            return False
        return self._validate_ni(l10n_uk_ni_code)

    @api.depends('company_id')
    def claimEmploymentAllowance(self, localdict):
        self.ensure_one()
        company = self.env.company
        return company.l10n_uk_hmrc_employment_allowance

    @api.model
    def _get_invalid_ni_employee_ids(self):
        # as we do not store if the ni is valid or not it's not possible to fetch all the employees directly
        # use sql and manually filter the employees

        # return nothing if user has no right to either employee or bank partner
        try:
            self.check_access('read')
            # ni field is for this group only
            if not self.user_has_groups('hr.group_hr_user'):
                raise AccessError()

        except AccessError:
            return []

        self.env.cr.execute('''
            SELECT emp.id,
                   emp.l10n_uk_ni_code
              FROM hr_employee emp
              JOIN hr_contract con
              ON con.id = emp.contract_id
              AND con.state in ('open', 'close')
             WHERE emp.company_id IN %s
               AND emp.employee_type IN ('employee', 'student')
               AND emp.active=TRUE
        ''', (tuple(c.id for c in self.env.companies if c.country_id.code == 'GB'),))
        return [row['id'] for row in self.env.cr.dictfetchall() if
                not row['l10n_uk_ni_code'] or not self._validate_ni(row['l10n_uk_ni_code'])]

    @api.depends('birthday')
    def get_age(self, localdict):
        payslip = localdict['payslip']

        for employee in self:
            if employee.birthday:
                age = (payslip.end_date - employee.birthday) / 365

        return age

    def _uk_get_yearly_cumulative_values(self, year=None):
        self.ensure_one()
        if not year:
            year = fields.date.today().year

        year_start = date.today() + relativedelta(year=year, month=int(self.company_id.ytd_reset_month),
                                                  day=int(self.company_id.ytd_reset_day))
        year_end = date.today() + relativedelta(year=year + 1, month=int(self.company_id.ytd_reset_month),
                                                day=int(self.company_id.ytd_reset_day) - 1)
        _log.debug("Reporting: " + year_start.strftime('%m/%d/%Y') + " to " + year_end.strftime('%m/%d/%Y'))
        # Get all payslip of the year for this employee
        yearly_payslips = self.env['hr.payslip'].search([
            ('paid_date', '>=', year_start),
            ('paid_date', '<', year_end),
            ('employee_id', '=', self.id),
            ('state', 'in', ['done', 'paid']),
        ])
        line_values = yearly_payslips._get_line_values(['BASIC', 'PAYE', 'SLOAN', 'PLOAN'], compute_sum=True)
        res = {value: line_values[value]['sum']['total'] for value in ['BASIC', 'PAYE', 'SLOAN', 'PLOAN']}

        # NIC group by letter
        ps_per_letter = {l: yearly_payslips.filtered(lambda ps: ps.l10n_uk_ni_letter == l)
                         for l in set(yearly_payslips.mapped('l10n_uk_ni_letter'))}
        res['NI'] = []
        for letter, payslips in ps_per_letter.items():
            line_values = yearly_payslips._get_line_values(['NI', 'NIC.LEL', 'NIC.PT', 'NIC.UEL'], compute_sum=True)
            res['NI'] += [{
                'letter': self.l10n_uk_ni_letter,
                'contrib': line_values['NI']['sum']['total'],
                'lel': line_values['NIC.LEL']['sum']['total'],
                'pt': line_values['NIC.PT']['sum']['total'],
                'uel': line_values['NIC.UEL']['sum']['total'],
            }]
        # Statutory pay
        res['statutory'] = defaultdict(lambda: 0)
        for worked_days in yearly_payslips.worked_days_line_ids:
            res['statutory'][worked_days.code] += worked_days.amount
        return res

    def _uk_p60_data(self, year=None):
        self.ensure_one()
        if not year:
            year = self.env.context.get('year', fields.date.today().year)
        values = self._uk_get_yearly_cumulative_values(year)
        res = {
            'year': year + 1,
            'income_lines': [{
                'name': 'In previous employment',
                'pay': self.past_employer_pay,
                'tax': self.past_employer_tax,
            }, {
                'name': 'In this employment',
                'pay': values['BASIC'],
                'tax': values['PAYE'],
            }, {
                'name': 'Total for year',
                'pay': values['BASIC'] + self.past_employer_pay,
                'tax': values['PAYE'] + self.past_employer_tax,
            }],
            'nic_lines': [{
                'letter': v['letter'],
                'lel': v['lel'],
                'pt': v['pt'],
                'uel': v['uel'],
                'contrib': v['contrib'],
            } for v in values['NI']],
            'st_loan': values.get('SLOAN', 0),
            'pg_loan': values.get('PLOAN', 0),
            'employer_desc': f'{self.company_id.name},\n{self.company_id.partner_id.contact_address}',
            # 'employer_paye': self.company_id.l10n_uk_hmrc_paye_ref,
            'ssp': values['statutory'].get('LEAVE310', 0),
            'smp': values['statutory'].get('LEAVE320', 0),
            'spp': values['statutory'].get('LEAVE330', 0),
            'sap': values['statutory'].get('LEAVE340', 0),
            'spbp': values['statutory'].get('LEAVE350', 0),
            'sspp': values['statutory'].get('LEAVE360', 0),
            'snp': values['statutory'].get('LEAVE370', 0)
        }
        return res

    def _uk_generate_p60(self):
        self.ensure_one()

    def get_salutation(self):
        self.ensure_one()

        match self.gender:
            case ' male':
                return 'Mr'
            case 'female':
                return 'Ms'
            case 'other':
                return 'Mx'
