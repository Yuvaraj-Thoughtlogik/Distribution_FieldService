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

{
    'name': 'United Kingdom Payroll',
    'countries': ['gb'],
    'category': 'Human Resources/Payroll',
    'depends': ['hr_payroll', 'hr_contract_reports', 'hr_work_entry_holidays', 'hr_payroll_holidays', 'l10n_uk_hmrc',
                'l10n_uk_reports'],
    'author': 'Augur Solutions LTD',
    'website': 'https://www.auguraccountants.com/odoo-uk-payroll',
    'summary': 'UK Payroll with integrated HMRC RTI Gateway supported by UK Accountants',
    'currency': 'EUR',
    'price': '129.99',
    'support': 'payroll@auguraccountants.com',
    'version': '18.0.1.1',
    'images': ['/l10n_uk_hr_payroll/static/images/uk_company_setup.png.png',
               '/l10n_uk_hr_payroll/static/images/uk_employee_setup.png',
               '/l10n_uk_hr_payroll/static/images/uk_year_end_reports.png',
               '/l10n_uk_hr_payroll/static/images/uk_contract_setup.png,'
               '/l10n_uk_hr_payroll/static/images/uk_payslips.png',
               '/l10n_uk_hr_payroll/static/images/uk_pensions1.png',
               '/l10n_uk_hr_payroll/static/images/uk_pensions2.png',
               '/l10n_uk_hr_payroll/static/images/uk_electronic_lodgement1.png'],
    'description': """

United Kingdom Payroll (Released 10-02-2025)
=============================================
    * HMRC Returns Full payment Submission (FPS) & Employer Payment Summary (EPS) NOTE: Via gateway at additional cost
    * Weekly & Monthly Pay Runs
    * Accommodates differences for England & Northern Ireland, Wales and  Scotland
    * Tax Codes
    * PAYE - https://assets.publishing.service.gov.uk/media/659bf68dd7737c000df33528/PAYErout-v22-0.odt
    * National Insurance - https://www.gov.uk/government/publications/payroll-technical-specifications-national-insurance
    * National Insurance for Investment Zones, Freeports, Veterans, Apprentices, Mariners
    * Class 1A and Class 1B National Insurance rates for expenses and benefits
    * Student / Post Graduate Loans - https://www.gov.uk/government/publications/payroll-technical-specifications-student-loans
    * Payroll Giving - https://www.gov.uk/government/publications/payroll-giving-approved-agencies
    * Employee Payslips including common UK disclosures
    * Statutory Maternity, Paternity, Adoption & Sick Leave Pay
    * Bonus, Commission, Car Allowance
    * Allow pension contributions to be based on pay that is greater than the statutory limits (i.e. £50,270)
    * UK Bank Holidays for Time Off
    * Claim employment allowance

Augur Solutions Payroll Gateway (Separate micro-payment gateway)
================================================================

    * HMRC PAYE Submissions
    * NEST Pension Submissions
    * True Potential Pension Submissions
    * Pricing is available via the Augur Webstore https://www.augursolutions.co.uk/store
    """,
    'data': [
        'data/report_paperformat.xml',
        'views/payroll_reports.xml',
        'data/hr_payroll_structure_data.xml',
        'data/hr_payroll_dashboard_warnings.xml',
        'data/hr_payslip_input_type_data.xml',
        'data/hr_salary_rule_category_data.xml',
        'data/hr_rule_parameters_data.xml',
        'data/hr_employee_monthly_salary_data.xml',
        'data/hr_employee_hourly_wage_data.xml',
        'data/hr_work_entry_type_data.xml',
        'data/hr_salary_attachment_type_data.xml',
        #        'data/resource_calendar_leaves.xml', # add these back in for most customer
        'data/hr_pensionfunds.xml',
        'data/l10n_uk_hr_note_data.xml',
        #        'data/l10n_uk_hr_payroll_demo.xml',
        'views/hr_contract_views.xml',
        'views/hr_employee_views.xml',
        'views/res_company_views.xml',
        #        'views/hr_leave_views.xml',
        'views/res_users_views.xml',
        #        'views/res_partner_views.xml',
        #        'views/template_transaction_engine_request_base.xml',
        #        'views/hr_pensionaccount_views.xml',
        'views/hr_pensionfund_views.xml',
        #        'wizard/l10n_uk_pension_true_potential_wizard_views.xml',
        'wizard/payroll_P60.xml',
        'views/report_p60_template.xml',
        'views/ir_ui_menu.xml',
        'wizard/l10n_uk_pension_aviva_wizard_views.xml',
        'wizard/l10n_uk_pension_nest_wizard_views.xml',
        'wizard/l10n_uk_pension_smart_wizard_views.xml',
        'wizard/l10n_uk_pension_peoples_wizard_views.xml',
        'views/report_payslip.xml',
        #        'views/hr_payroll_reports.xml',
        'views/hr_payslip_views.xml',
        'security/l10n_uk_hr_payroll_security.xml',
        'security/ir.model.access.csv', ],
    'demo': [
        'data/l10n_uk_hr_payroll_demo.xml'
    ],
    'installable': True,
    'license': 'OPL-1',
}
