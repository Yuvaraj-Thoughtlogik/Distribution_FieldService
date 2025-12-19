# -*- coding:utf-8 -*-
# AUGUR Solutions Payroll Proprietary License v1.0
# Copyright © Augur Solutions Ltd, 2024-2025
from dateutil.utils import today

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


from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class HrContract(models.Model):
    _inherit = 'hr.contract'

    # Is this Contact a Director 
    is_director = fields.Boolean(default=False, string='Company Director', help='Is this Contract a Company Director',
                                 groups='hr_payroll.group_hr_payroll_user')
    is_ytd_basis = fields.Boolean(default=False, string='YTD Basis',
                                  groups='hr_payroll.group_hr_payroll_user',
                                  help='For Company Directors who are paid infrequently')
    director_date = fields.Date(default=today(), string='Date Appointed',
                                groups='hr_payroll.group_hr_payroll_user',
                                help='The date the employee was appointed as a Director')
    # Is the contract subject to pension auto-enrolment
    is_autoenrolment = fields.Boolean(default=True, string='Auto-enrolment',
                                      groups='hr_payroll.group_hr_payroll_user',
                                       help='Is this Contract subject to Pension Auto-enrolment',
                                       tracking=True)
    next_autoenrolment_date = fields.Date(string='Next Auto-enrolment Date',
                                          groups='hr_payroll.group_hr_payroll_user',
                                           help='The date this employee must make a new auto-enrolment election')

    ae_date = fields.Date(string='Date Auto-Enrolled',
                          groups='hr_payroll.group_hr_payroll_user',
                          help='The date this employee auto-enrolled')

    # https://thepeoplespension.co.uk/help/knowledgebase/what-is-a-status/
    # SP = State Pension Age
    # Earns below Lower Limit £10000/year. £520/month, £192/week - Entitled
    # - employee can opt-in if aged between 16 & 74 but employer is not required to pay in
    # Earns between £520/month & £833/month - Non-Eligible (Type 2 Employees)
    # - employee can opt-in if aged between 16 & 74 and employer is required to pay in
    # Earns > £833/month
    #   Aged: 16-21 - Non-Eligible
    #   Aged: 22-SP - Eligible (Type 1 Employees)
    #   Aged: SP-74 - Non-Eligible
    # Not Known: pension provider to assess the eligibility criteria of an employee (new starter or in postponement period)
    # on your behalf and the employee’s status hasn’t been confirmed yet, or
    # if an employee doesn’t have a pension but does have life cover/employee accident cover
    # Not Applicable: Use when an employee is aged under 16 or over 75.
    # This is because auto-enrolment doesn’t apply to them due to their age.

    ae_status = fields.Selection(
        [
            ('0', 'Excluded'),
            ('1', 'Eligible Jobholder'),
            ('2', 'Non-Eligible Jobholder'),
            ('3', 'Entitled Worker'),
            ('4', 'Contractual Enrolment'),
            ('5', 'Already in another qualifying scheme'),
            ('6', 'Not Known'),
            ('7', 'Not Applicable'),
        ],
        required=False, tracking=True,
        groups='hr_payroll.group_hr_payroll_user',
        string='AE Status',
        help='The employee\'s auto-enrolment status',
        readonly=False)


    ae_group = fields.Char(string='Pension Group', tracking=True,
                           groups='hr_payroll.group_hr_payroll_user',
                           required=False, readonly=False,
                           help='Optional code or string that is mapped to a pension group defined by the pension fund')






    pension_fund = fields.Many2one('l10n_uk_pension_fund', string='Pension Fund',
                                   groups='hr_payroll.group_hr_payroll_user', tracking=True)  # , required=True)
    member_no = fields.Char(string='Member Number', groups='hr_payroll.group_hr_payroll_user')

    employee_pension_contribution = fields.Float(string="Employee Pension Contribution",
                                                 groups='hr_payroll.group_hr_payroll_user',
                                                 tracking=True, default="5", readonly=False,
                                                 # compute="_check_total_contribution",
                                                 help="The percentage of the Monthly Gross Pay the Employee will pay in to their pension.")
    employer_pension_contribution = fields.Float(
        string="Employer Pension Contribution",
        tracking=True, default="3", readonly=False,  # compute="_check_valid_pension_employer",
        groups='hr_payroll.group_hr_payroll_user',
        help="The percentage of the Monthly Gross Pay the Employer will pay in to the Employee's pension.")

    employer_pension_contribution_amount = fields.Monetary(
        string="Employer Pension Contribution Amount",
        tracking=True, default="0", readonly=False,  # compute="_check_valid_pension_employer",
        groups='hr_payroll.group_hr_payroll_user',
        help="The amount the Employer will pay in to the Employee's pension. This is usually agreed as part of a salary sacrifice arrangement")

    pension_exceed_max = fields.Boolean(default=False, string='Allow Pension Contributions above Statutory Max',
                                        groups='hr_payroll.group_hr_payroll_user',
                                        help='Do you want pension contributions to be calculated on gross pay above the statutory maximum')

    @api.constrains('employer_pension_contribution', 'ae_status', 'employer_pension_contribution_amount')
    def _check_valid_pension_employer(self):
        for c in self:
            if c.is_autoenrolment and c.employer_pension_contribution_amount == 0 and c.ae_status == '1':
                threshold = float(self.env['hr.rule.parameter'].sudo()._get_parameter_from_code('UK_PEN_CO_Rate',
                        fields.Date.today(), raise_if_not_found=False))

                if (0 < c.employer_pension_contribution < threshold):
                    raise ValidationError(_('The employer contribution toward pension cannot be lower than '
                                + str(threshold) + '%.'))
                if c.employer_pension_contribution > 100:
                    raise ValidationError(_('The employer contribution toward pension cannot be higher than 100%.'))

    @api.constrains('employee_pension_contribution', 'employer_pension_contribution',
                    'ae_status', 'employer_pension_contribution_amount')
    def _check_total_contribution(self):
        for c in self:
            threshold = float(self.env['hr.rule.parameter'].sudo()._get_parameter_from_code('UK_PEN_MinRate',
                        fields.Date.today(), raise_if_not_found=False) \
                if c.company_id.l10n_uk_pensionable_earnings == 'Q' \
                        else self.env['hr.rule.parameter'].sudo()._get_parameter_from_code('UK_PEN_MinRate_Full',
                             fields.Date.today(), raise_if_not_found=False))

            # don't apply a threshold calculation to the percentages
            #  - if the contract is not auto-enrolled
            #  - if there is a fixed employer contribution amount
            #  - if the contract is not an eligible Jobholder
            if (c.is_autoenrolment and c.employer_pension_contribution_amount == 0 and c.ae_status == '1'
                    and (0 < c.employer_pension_contribution + c.employee_pension_contribution < threshold)):
                raise ValidationError(_('The total contribution toward pension cannot be lower than '
                                        + str(threshold) + '%.'))


    def is_pension_direct_pay(self):
        self.ensure_one()
        # lookup pension fund type and return true if relief at source - tax is paid in the pension fund

        pension_fund = self.env['l10n_uk_pension_fund'].search([
            ('id', '=', self.pension_fund.id)])
        return pension_fund.fund_type == 'D'

    def is_pension_relief_at_source(self):
        self.ensure_one()
        # lookup pension fund type and return true if relief at source - tax is paid in the pension fund

        pension_fund = self.env['l10n_uk_pension_fund'].search([('id', '=', self.pension_fund.id)])
        return pension_fund.fund_type == 'R'

    def pension_type(self):
        self.ensure_one()

        pension_fund = self.env['l10n_uk_pension_fund'].search([('id', '=', self.pension_fund.id)])
        return pension_fund.fund_type
