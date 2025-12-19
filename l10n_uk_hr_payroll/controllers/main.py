# -*- coding:utf-8 -*-
# AUGUR Solutions Payroll Proprietary License v1.0
# Copyright © Augur Solutions Ltd, 2024-2025
import base64
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


import io
import re
import logging
from datetime import datetime

from odoo import http, fields
# from odoo.http import request, route, Controller, content_disposition
from odoo.tools import pycompat,  float_repr
from odoo.tools.misc import xlsxwriter, csv
from dateutil.relativedelta import relativedelta
from PyPDF2 import PdfFileReader, PdfFileWriter

_log = logging.getLogger(__name__)


class L10nUKHrPayrollPensionNestController(http.Controller):

    @http.route(["/export/uk/nest/<string:employee_ids>/<string:start>/<string:end>"], type='http', auth='user')
    def export_pension_nest(self, employee_ids='', start=fields.Date.today(), end=fields.Date.today(), **kw):
        if not http.request.env.user.has_group('hr_payroll.group_hr_payroll_user') or not employee_ids or re.search(
                "[^0-9|,]", employee_ids):
            return http.request.not_found()

        ids = [int(s) for s in employee_ids.split(',')]
        employees = http.request.env['hr.employee'].browse(ids)
        _log.debug("Generate NEST Report")

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Worksheet')
        style_highlight = workbook.add_format({'bold': True, 'pattern': 1, 'bg_color': '#E0E0E0', 'align': 'center'})
        style_normal = workbook.add_format({'align': 'center', 'num_format': '0.00'})
        row = 0

        headers = [
            "NINO",
            "Name",
            "Pensionable Amount",
            "Employee Amount",
            "Employer Amount",
        ]

        all_payslips = http.request.env['hr.payslip'].search([
            ('employee_id', 'in', ids),
            ('paid_date', '>=', start),  # fields.Date.today() + relativedelta(day=1, month=1)),
            ('paid_date', '<=', end),  # fields.Date.today() + relativedelta(day=31, month=12)),
            ('state', 'in', ['done', 'paid'])
        ])

        line_values = all_payslips._get_line_values(
            ['PENE', 'PENC'],
            vals_list=['amount', 'total']
        )

        rows = []

        for employee in employees:
            employee_amounts = 0.00
            employer_amounts = 0.00
            pensionable_amounts = 0.00

            # employee_id = employee
            # for payslip in all_payslips.filtered('employee_id').employee_id:
            for payslip in all_payslips:
                if payslip.employee_id == employee:
                    pensionable_amounts += line_values['PENE'][payslip.id]['amount']
                    employee_amounts += line_values['PENE'][payslip.id]['total']
                    employer_amounts += line_values['PENC'][payslip.id]['total']

            pensionable_amount = round(pensionable_amounts, 2)
            employee_amount = round(employee_amounts, 2)
            employer_amount = round(employer_amounts, 2)

            if employee_amount > 0:
                rows.append((
                    employee.l10n_uk_ni_code.replace('.', '').replace('-', '') if employee.l10n_uk_ni_code else '',
                    employee.name,
                    pensionable_amount,
                    employee_amount,
                    employer_amount,
                ))

        col = 0
        for header in headers:
            worksheet.write(row, col, header, style_highlight)
            worksheet.set_column(col, col, 15)
            col += 1

        row = 1
        for employee_row in rows:
            col = 0
            for employee_data in employee_row:
                worksheet.write(row, col, employee_data, style_normal)
                col += 1
            row += 1

        workbook.close()
        xlsx_data = output.getvalue()
        response = http.request.make_response(
            xlsx_data,
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', f'attachment; filename=pension_nest.xlsx')],
        )
        return response

    @http.route(["/export/uk/nest/<string:employee_ids>/<int:run_id>"], type='http', auth='user')
    def export_pension_nest(self, employee_ids='', run_id=0, **kw):
        if not http.request.env.user.has_group('hr_payroll.group_hr_payroll_user') or not employee_ids or re.search(
                "[^0-9|,]", employee_ids):
            return http.request.not_found()

        ids = [int(s) for s in employee_ids.split(',')]
        employees = http.request.env['hr.employee'].browse(ids)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Worksheet')
        style_highlight = workbook.add_format({'bold': True, 'pattern': 1, 'bg_color': '#E0E0E0', 'align': 'center'})
        style_normal = workbook.add_format({'align': 'center', 'num_format': '0.00'})

        try:
            pension_fund = http.request.env.ref('l10n_uk_hr_payroll.l10n_uk_pension_fund_nest')
            _log.info("NEST Pension ID Found: " + str(pension_fund.id))

            payrun = http.request.env['hr.payslip.run'].search([
                ('id', '=', run_id),
                ('state', 'in', ['done', 'paid']),
                ])

            pension_details = http.request.env['l10n_uk_pension_fund_company'].search([
                ('pension_fund_id', '=', pension_fund.id),
                ('company_id', '=', payrun.company_id.id),
            ])

            if payrun:
                _log.info("Dates: "+ str(payrun.date_start) + " " + str(payrun.date_end))

                all_payslip_lines = http.request.env['hr.payslip.line'].search([
                    ('employee_id', 'in', ids),
                    ('slip_id.payslip_run_id', '=', run_id),
                  #  ('date_from', '>=', payrun.date_start),
                  #  ('date_to', '<=', payrun.date_end),
                    ('slip_id.state', 'in', ['done', 'paid']),
                    ('employee_id.contract_id.pension_fund', '=', pension_fund.id),
                    ('code', 'in', ['PENE','PENC'])
                ])

                if payrun.payment_date.day >= 6:
                    eped = payrun.payment_date + relativedelta(day=5, months=+1)
                else:
                    eped = payrun.payment_date + relativedelta(day=5)

                total = 0.00
                counter = 0


                csv_buffer = io.StringIO()
                writer = csv.writer(csv_buffer, quoting=csv.QUOTE_NONE)

                # https://www.nestpensions.org.uk/schemeweb/dam/nestlibrary/employer-payroll-guide-PDF.pdf
                writer.writerow(['H', pension_details.employer_ref, 'CS', payrun.payment_date,
                                 pension_details.payment_source,eped,'Monthly','','','',''])

                for employee in employees.filtered(lambda r: r.contract_id.pension_fund.id == pension_fund.id):
                    _log.info("Processing: " + str(employee.name))
                    pensionable_amount = round(
                        sum(all_payslip_lines.filtered(
                            lambda r: r.employee_id.id == employee.id and r.code == 'PENE').mapped(
                            'amount')), 2) or 0.0
                    employee_amount = round(
                        sum(all_payslip_lines.filtered(lambda r: r.employee_id.id == employee.id and r.code == 'PENE').mapped(
                            'total')), 2) or 0.0
                    employer_amount = round(
                        sum(all_payslip_lines.filtered(lambda r: r.employee_id.id == employee.id and r.code == 'PENC').mapped(
                            'total')), 2) or 0.0

                    _log.info("Pensionable Amount: " + str(pensionable_amount))
                    if pensionable_amount > 0.00:
                        writer.writerow([
                            'D',
                            employee.l10n_uk_surname or '',
                            employee.l10n_uk_ni_code or '',
                            employee.registration_number or '',
                            float_repr(pensionable_amount, 2),
                            '',     # Blank This field should only be used for member contributions if the reason for
                                    # partial or non-payment of contributions in field 9 is reason 3 - ‘Member is on
                                    # family leave’
                            float_repr(employer_amount, 2),
                            float_repr(employee_amount, 2),
                            '',     # Reason for partial or nonpayment of contributions This is the explanation for why
                                    # contributions received don’t match up with the payment schedule
                            '',     # Effective date of partial or non-payment Effective date of the event which
                                    # resulted in no contribution being paid
                            '','','','','','','','','','',''
                        ])
                        total += (employee_amount + employer_amount)
                        counter += 1

                # write footer
                writer.writerow(['T', counter, 4])

                # Prepare HTTP response
                csv_content = csv_buffer.getvalue()
                csv_buffer.close()

                filename = 'nest_pension_export_{}_{}.csv'.format(datetime.today().strftime('%Y%m%d'), run_id)

                # store in the database
                http.request.env['ir.attachment'].create({
                    'name': filename,
                    'type': 'binary',
                    'datas': base64.b64encode(csv_content.encode('utf-8')),
                    'mimetype': 'text/csv',
                    'res_model': 'hr.payslip.run',
                    'res_id': run_id,
                })

                response = http.request.make_response(
                    csv_content,
                    headers=[
                        ('Content-Type', 'text/csv'),
                        ('Content-Disposition', f'attachment; filename={filename}')],
                )
                return response

        except ValueError:
            pension_fund = None  # or log, or raise custom error
            _log.info("NEST pension fund NOT found")


class L10nUKHrPayrollPensionSmartController(http.Controller):

    @http.route(["/export/uk/smart/<string:employee_ids>/<int:run_id>"], type='http', auth='user')
    def export_pension_smart(self, employee_ids='', run_id=0, **kw):
        if not http.request.env.user.has_group('hr_payroll.group_hr_payroll_user') or not employee_ids or re.search(
                "[^0-9|,]", employee_ids):
            return http.request.not_found()

        ids = [int(s) for s in employee_ids.split(',')]
        employees = http.request.env['hr.employee'].browse(ids)
        _log.info('Generate SMART Pension Report')

        #payslip_batch = http.request.env['hr.payslip.run'].search([
        #                                    ('employee_id', 'in', ids),
        #                                    ('id', '=', run_id),
        #                                    ('state', 'in', ['done', 'paid']),
        #                                    ])

        try:
            pension_fund = http.request.env.ref('l10n_uk_hr_payroll.l10n_uk_pension_fund_smart')
            payrun = http.request.env['hr.payslip.run'].search([('id', '=', run_id),
                                                       ('state', 'in', ['done','paid'])
                                                       ])

            if pension_fund:
                all_payslip_lines = http.request.env['hr.payslip.line'].search([
                    ('employee_id', 'in', ids),
                    ('slip_id.payslip_run_id', '=', run_id),
                    #('date_from', '>=', payrun.date_start),
                    #('date_to', '<=', payrun.date_end),
                    ('slip_id.state', 'in', ['done', 'paid']),
                    ('employee_id.contract_id.pension_fund', '=', pension_fund.id),
                    ('code', 'in', ['PENE', 'PENC', 'GROSS'])
                ])

                pension_details = http.request.env['l10n_uk_pension_fund_company'].search([
                    ('pension_fund_id', '=', pension_fund.id),
                    ('company_id', '=', payrun.company_id.id),
                ])

                if not pension_details:
                    _log.info("Pension not found: " + str(pension_fund.id) + "Company ID: " + str(payrun.company_id.id))
                    return ''

                # Header
                csv_buffer = io.StringIO()
                writer = csv.writer(csv_buffer, quoting=csv.QUOTE_STRINGS)

                # https://thepeoplespension.co.uk/wp-content/uploads/TPP-GD-0006.0723-Full-file-data-requirements-guide_v2.pdf
                #writer.writerow(['H', pension_details.employer_ref, payrun.date_start, payrun.date_end, 'FL'])
                writer.writerow(['PAPDISVersion','PensionProviderId','EmployerId','Group','SubGroup','PayPeriodStartDate',
                                'PayPeriodEndDate','ContributionDeductionDate','FrequencyCode','TaxPeriod','Title',
                                'Forename1','Forename2','Surname','EmployeeId','BirthDate','Gender','NationalInsuranceNumber',
                                'Address1','Address2','Address3','Address4','Postcode','Country','EmailAddress',
                                'EmploymentStartDate','ExitDate','ExitReasonCode','AssessmentCode','EventCode','EventDate',
                                'DeferralDate','AEOptOutDate','AEOptOutReference','EnrolmentCommunicationsIssuedDate',
                                'EmployerContributionsAmount','EmployeeContributionsAmount',
                                'AdditionalVoluntaryContributionsAmount','AdditionalVoluntaryContributionsPercent',
                                'PensionableEarningsAmount','EmployerContributionsPercent','EmployeeContributionsPercent',
                                'SalarySacrificeIndicator'])
                total = 0.00

                for employee in employees.filtered(lambda r: r.contract_id.pension_fund.id == pension_fund.id):
                    _log.info("Processing: " + str(employee.name))

                    gross_amount = round(
                        sum(all_payslip_lines.filtered(
                            lambda r: r.employee_id.id == employee.id and r.code == 'GROSS').mapped(
                            'total')), 2)
                    pensionable_amount = round(
                            sum(all_payslip_lines.filtered(
                                lambda r: r.employee_id.id == employee.id and r.code == 'PENE').mapped(
                                'amount')), 2)
                    employee_amount = round(
                            sum(all_payslip_lines.filtered(
                                lambda r: r.employee_id.id == employee.id and r.code == 'PENE').mapped(
                                'total')), 2)
                    employer_amount = round(
                            sum(all_payslip_lines.filtered(
                                lambda r: r.employee_id.id == employee.id and r.code == 'PENC').mapped(
                                'total')), 2)

                    salutation = employee.get_salutation() or ''
                    payslip = http.request.env['hr.payslip'].search([('id', '=', run_id),
                                                                     ('state', 'in', ['done','paid']),
                                                                     ('employee_id', '=', employee.id),  ])
                    year_end = ( payrun.company_id.get_last_ytd_reset_date(payrun.payment_date)
                                + relativedelta(years=+1, days=-1))
                    year_start = payrun.company_id.get_last_ytd_reset_date(payrun.payment_date)
                    end_date = payrun.payment_date
                    period = relativedelta(end_date, year_start).months + 1

                    # Calendar Month # TODO Accommodate other pay periods
                    if payrun.date_start.day == 1:
                        month_date_start = payrun.date_start + relativedelta(day=1)
                    else:    # does not align to a calendar month but Smart Pensions requires calendar month
                             # construct a calendar month around the payment date
                        month_date_start = payrun.date_start + relativedelta(day=1, months=+1)

                    month_date_end = month_date_start + relativedelta(months=+1, days=-1)

                    _log.info(
                        "Period No: " + str(period) + " Tax Year: " + str(year_end) + " / "
                        + str(year_start) + " / " + str( end_date))

                    if employee.private_street2:
                        street2 =  employee.private_street2
                        street3 = employee.private_city
                    else:
                        street2 = employee.private_city
                        street3 = ''
                    # TODO: Add exit dates / Reason Code
                    # TODO: Add Opt Out Dates
                    # TODO: Status for Opt Outs
                    writer.writerow([
                        'PAP01',
                        'smartpension',
                        pension_details.employer_ref,
                        'default',
                        '',   # subgroup
                        month_date_start.strftime('%Y-%m-%d'),
                        month_date_end.strftime('%Y-%m-%d'),
                        payrun.payment_date,
                        'M1', # TODO add functionality for weekly
                        period, # Tax Period
                        salutation,
                        employee.l10n_uk_forename or '',
                        employee.l10n_uk_second_forename or '',
                        employee.l10n_uk_surname or '',
                        employee.registration_number or employee.contract_id.member_no or '',
                        employee.birthday or '',
                        'F' if employee.gender == 'female' else 'M',    # Default other to Male
                        employee.l10n_uk_ni_code or '',
                        employee.private_street or '',  # Address 1
                        street2 or '',     # Address 2
                        street3 or '',     # Address 3
                        employee.private_state_id.name or '',   # Address 4
                        employee.private_zip or '',     # Address 5
                        employee.private_country_id.name or '',
                        employee.private_email or '',
                        employee.contract_id.date_start or '',  # start date
                        '',
                        '',
                        # see: https://www.smartpension.co.uk/support/en/articles/4598845-papdis-specifications-and-assessment-codes
                        1, # 0 = Excluded, 1 = Eligible Jobholder, 2 = Non-Eligible Jobholder, 3 = Entitled Worker
                        0, # 0 = Not an Enrolment event, 1 - Automatic enrolment or re-enrolment, 2 = Opt-in,
                           # 3 = Voluntary Joiner/Joiner, 4 = contractual Enrolment
                        '',
                        '',
                        '',
                        '',
                        '',
                        float_repr(employer_amount, 2) or 0.00,
                        float_repr(employee_amount, 2) or 0.00,
                        float_repr(employee.contract_id.employer_pension_contribution_amount,2) or 0.00, # AVC amount
                        0, # AVC percentage
                        float_repr(pensionable_amount, 2) or 0.00,
                        float_repr(employee.contract_id.employer_pension_contribution,2) or 0.00, # standard: 3%
                        float_repr(employee.contract_id.employee_pension_contribution,2) or 0.00, # standard: 5%
                        'N'])
                    total += (employee_amount + employer_amount)

                # write footer
                #writer.writerow(['T', total])

                # Prepare HTTP response
                csv_content = csv_buffer.getvalue()
                csv_buffer.close()
                filename = 'smart_pension_export_{}_{}.csv'.format(datetime.today().strftime('%Y%m%d'), run_id)

                # store in the database
                http.request.env['ir.attachment'].create({
                    'name': filename,
                    'type': 'binary',
                    'datas': base64.b64encode(csv_content.encode('utf-8')),
                    'mimetype': 'text/csv',
                    'res_model': 'hr.payslip.run',
                    'res_id': run_id,
                })

                response = http.request.make_response(
                    csv_content,
                    headers=[
                    ('Content-Type', 'text/csv'),
                    ('Content-Disposition', f'attachment; filename={filename}')],
                )
                return response
        except ValueError:
            pension_fund = None  # or log, or raise custom error
            _log.info("Smart pension fund NOT found")


# The Peoples Pension
# https://thepeoplespension.co.uk/wp-content/uploads/TPP-GD-0006.0723-Full-file-data-requirements-guide_v2.pdf
# TODO Use this as the template to generate different formats from the one controller
# make sure you ask the user to select the required format (or detect it from the pension fund)
# when you generate the submission(s)
class L10nUKHrPayrollPensionPeoplesController(http.Controller):

    @http.route(["/export/uk/peoples/<string:employee_ids>/<int:run_id>"], type='http', auth='user')
    def export_pension_peoples(self, employee_ids='', run_id=0, **kw):
        if not http.request.env.user.has_group('hr_payroll.group_hr_payroll_user') or not employee_ids or re.search(
                "[^0-9|,]", employee_ids):
            return http.request.not_found()

        ids = [int(s) for s in employee_ids.split(',')]
        employees = http.request.env['hr.employee'].browse(ids)
        _log.info("Generate Peoples Pension Report")

        try:
            pension_fund = http.request.env.ref('l10n_uk_hr_payroll.l10n_uk_pension_fund_peoples')

            payrun = http.request.env['hr.payslip.run'].search([('id', '=', run_id)])

            if pension_fund and payrun:
                all_payslip_lines = http.request.env['hr.payslip.line'].search([
                    ('employee_id', 'in', ids),
                    ('slip_id.payslip_run_id', '=', run_id),
                    ('date_from', '>=', payrun.date_start),
                    ('date_to', '<=', payrun.date_end),
                    ('slip_id.state', 'in', ['done', 'paid']),
                    ('employee_id.contract_id.pension_fund', '=', pension_fund.id),
                    ('code', 'in', ['PENE', 'PENC', 'GROSS'])
                ])

                # Header
                csv_buffer = io.StringIO()
                writer = csv.writer(csv_buffer)

                writer.writerow(['H', pension_fund.employer_ref, payrun.date_start, payrun.date_end, 'FL'])   # Full Files
                writer.writerow(['Record Type','Title','Gender','Forename 1','Forename 2','Surname','Date of Birth',
                                 'National Insurance Number', 'Unique Identifier', 'Address 1','Address 2', 'Address 3',
                                 'Address 4','Address 5', 'Home Phone Number', 'Mobile Phone Number', 'Personal Email Address',
                                 'Date Employment Started','Starter / Leaver Flag','Employment Ended','AE Worker Group',
                                 'AE Status', 'AE Date', 'Scheme Join Date', 'Opt Out Date','Opt In Date',
                                 'Total Earnings Per PRP','Pensionable Earnings Per PRP', 'Employer Pension Contribution',
                                 'Employee Pension Contribution', 'Missing / Partial Pension Code','EAC / ELC Premium',
                                 'Date AE Information Received', 'Deferral Date'])

                rows = []
                total = 0.00

                for employee in employees.filtered(lambda r: r.contract_id.pension_fund.id == pension_fund.id):
                    _log.info("Processing: " + str(employee.name))

                    gross_amount = round(
                        sum(all_payslip_lines.filtered(
                            lambda r: r.employee_id.id == employee.id and r.code == 'GROSS').mapped(
                            'total')), 2)
                    pensionable_amount = round(
                        sum(all_payslip_lines.filtered(
                            lambda r: r.employee_id.id == employee.id and r.code == 'PENE').mapped(
                            'amount')), 2)
                    employee_amount = round(
                        sum(all_payslip_lines.filtered(
                            lambda r: r.employee_id.id == employee.id and r.code == 'PENE').mapped(
                            'total')), 2)
                    employer_amount = round(
                        sum(all_payslip_lines.filtered(
                            lambda r: r.employee_id.id == employee.id and r.code == 'PENC').mapped(
                            'total')), 2)

                    salutation = employee.get_salutation()

                    flag = ''
                    missing_flag = ''
                    age = relativedelta(payrun.payment_date, employee.birthday).years
                    if age < 22:
                        join_date = employee.contract_id.ae_date
                        ae_date = ''
                    else:
                        join_date = ''
                        ae_date = employee.contract_id.ae_date

                    if employee.contract_id.date_end:
                        missing_flag = '1'
                        # Left in this payrun
                        if payrun.date_start <= employee.contract_id.date_end <= payrun.date_end:
                            flag = 'LS'

                    # joined in this payrun
                    if payrun.date_start <= employee.contract_id.date_start <= payrun.date_end:
                        flag = 'NS'

                    writer.writerow([
                        'D',
                        salutation or '',
                        'F' if employee.gender == 'female' else 'M',    # Default other to Male
                        employee.l10n_uk_forename or '',
                        employee.l10n_uk_second_forename or '',
                        employee.l10n_uk_surname or '',
                        employee.birthday or '',
                        employee.l10n_uk_ni_code or '',
                        employee.registration_number or '',
                        employee.private_street or '',  # Address 1 (Mandatory)
                        employee.private_street2 or '', # Address 2
                        employee.private_city or '',    # Address 3
                        employee.private_state_id.name or '',   # Address 4
                        employee.private_zip or '',     # Address 5 (Mandatory)
                        employee.private_phone or '',
                         '',                            # mobile phone
                        employee.private_email or '',
                        employee.contract_id.date_start or '',   # start date
                        flag or '', # TODO Flag NS: New Starter, LS: Leaving Pensionable Service, RE: Re-enrolled
                        employee.contract_id.date_end or '',             #
                        employee.contract_id.ae_group or '',    # AE Worker Group
                        self._get_ae_status(employee.contract_id.ae_status),
                        ae_date or '',          # date employee joined AE
                        join_date or '',        # scheme join date - if opted in, this field needs to be
                                                # populated and ae_date is blank
                        '', # opt out date
                        '', # opt in date
                        float_repr(gross_amount,2) or 0.00,
                        float_repr(pensionable_amount,2) or 0.00,
                        float_repr(employer_amount,2) or 0.00,
                        float_repr(employee_amount,2) or 0.00,
                        missing_flag or '', # TODO Missing / Partial Pension Code
                        # Blank or number (see explanation below)
                        # 1 - Employee has left the company
                        # 2 - Employee is temporarily absent
                        # 3 - Employee is on family leave
                        # 4 - Employee has chosen to stop contributions
                        # 5 - Earnings are below the threshold or there are no pension-related earnings for the employee
                        # 8 - Employee has transferred to this account (from a different account with The People’s Pension)

                        0.00, # EAC/ELC Premium: The weekly premium If the employer operates B&CE Employee
                        # Accident Cover/Employee Life Cover (EAC/ELC)

                        '', # Date AE Joiner Information Sent to Employee
                        # Notes: This field only needs to be populated if you’re is sending out your own joiner
                        # information and need to record the start of the opt-out refund period.
                        # The People’s Pension will send joiner information for you unless otherwise agreed.

                        '', # Deferral Date
                    ])
                    total += (employee_amount + employer_amount)

                # write footer
                writer.writerow(['T', total])

                # Prepare HTTP response
                csv_content = csv_buffer.getvalue()
                csv_buffer.close()
                filename = 'peoples_pension_export_{}_{}.csv'.format(datetime.today().strftime('%Y%m%d'), run_id)

                response = http.request.make_response(
                    csv_content,
                    headers=[
                    ('Content-Type', 'text/csv'),
                    ('Content-Disposition', f'attachment; filename={filename}')],
                )
                return response

        except ValueError:
            pension_fund = None  # or log, or raise custom error
            _log.info("Peoples pension fund NOT found")

# Aviva Pension
class L10nUKHrPayrollPensionAvivaController(http.Controller):

    @http.route(["/export/uk/aviva/<string:employee_ids>/<int:run_id>"], type='http', auth='user')
    def export_pension_peoples(self, employee_ids='', run_id=0, **kw):
        if not http.request.env.user.has_group('hr_payroll.group_hr_payroll_user') or not employee_ids or re.search(
                "[^0-9|,]", employee_ids):
            return http.request.not_found()

        ids = [int(s) for s in employee_ids.split(',')]
        employees = http.request.env['hr.employee'].browse(ids)
        _log.info("Generate Aviva Pension Report")

        try:
            pension_fund = http.request.env.ref('l10n_uk_hr_payroll.l10n_uk_pension_fund_aviva')

            payrun = http.request.env['hr.payslip.run'].search([('id', '=', run_id)])

            if pension_fund and payrun:
                all_payslip_lines = http.request.env['hr.payslip.line'].search([
                    ('employee_id', 'in', ids),
                    ('slip_id.payslip_run_id', '=', run_id),
                    #('date_from', '>=', payrun.date_start),
                    #('date_to', '<=', payrun.date_end),
                    ('slip_id.state', 'in', ['done', 'paid']),
                    ('employee_id.contract_id.pension_fund', '=', pension_fund.id),
                    ('code', 'in', ['PENE', 'PENC', 'GROSS'])
                ])

                # Header
                csv_buffer = io.StringIO()
                writer = csv.writer(csv_buffer)

                writer.writerow(
                    ['Group_code','Title','Forename','Surname','DOB','Gender','Marital_status','NI_Number',
                     'Payroll_Reference_Code','Employer_pension_payment','Employee_pension_payment',
                     'Contractual_Earnings(current)','Noncontractual_Earnings(current)',
                     'Pensionable_earnings(current)','Employer_Single_Contribution',
                     'Employee_Single_Contribution','Address1','Address2','Address3','Address4','Postcode',
                     'Yearly_Pensionable_Earnings','Daytime_Telephone','Evening_Telephone','Email','Employment_start_date',
                     'Existing_member','Aviva_category'
                    ])

                rows = []
                total = 0.00

                for employee in employees.filtered(lambda r: r.contract_id.pension_fund.id == pension_fund.id):
                    _log.info("Processing: " + str(employee.name))

                    gross_amount = round(
                        sum(all_payslip_lines.filtered(
                            lambda r: r.employee_id.id == employee.id and r.code == 'GROSS').mapped(
                            'total')), 2)
                    pensionable_amount = round(
                        sum(all_payslip_lines.filtered(
                            lambda r: r.employee_id.id == employee.id and r.code == 'PENE').mapped(
                            'amount')), 2)
                    employee_amount = round(
                        sum(all_payslip_lines.filtered(
                            lambda r: r.employee_id.id == employee.id and r.code == 'PENE').mapped(
                            'total')), 2)
                    employer_amount = round(
                        sum(all_payslip_lines.filtered(
                            lambda r: r.employee_id.id == employee.id and r.code == 'PENC').mapped(
                            'total')), 2)

                    salutation = employee.get_salutation()

                    flag = ''
                    missing_flag = ''

                    if employee.contract_id.date_end:
                        missing_flag = '1'
                        # Left in this payrun
                        if payrun.date_start <= employee.contract_id.date_end <= payrun.date_end:
                            flag = 'LS'

                    # joined in this payrun
                    if payrun.date_start <= employee.contract_id.date_start <= payrun.date_end:
                        flag = 'N'
                    else:
                        flag = 'Y'

                    writer.writerow([
                        employee.contract_id.ae_group or '',    # AE Worker Group
                        salutation or '',                       # Title
                        employee.l10n_uk_forename or '',        # Forename
                        employee.l10n_uk_surname or '',         # Surname
                        employee.birthday or '',                # DOB
                        'F' if employee.gender == 'female' else 'M',  # Default other to Male
                        '',                                     # Marital Status
                        employee.l10n_uk_ni_code or '',
                        employee.registration_number or '',     # Payroll Reference Code
                        float_repr(employer_amount, 2) or 0.00, # Employer_pension_payment
                        float_repr(employee_amount, 2) or 0.00, # Employee_pension_payment
                        float_repr(gross_amount, 2) or 0.00,    # Contractual_Earnings(current)
                        0.00,                                   # Noncontractual_Earnings(current)
                        float_repr(pensionable_amount, 2) or 0.00, # Pensionable_earnings(current)
                        0.00,                                   # Employer_Single_Contribution
                        0.00,                                   # Employee_Single_Contribution
                        employee.private_street or '',          # Address 1 (Mandatory)
                        employee.private_street2 or '',         # Address 2
                        employee.private_city or '',            # Address 3
                        employee.private_state_id.name or '',   # Address 4
                        employee.private_zip or '',             # Address 5 (Mandatory)
                        float_repr(pensionable_amount * 12, 2) or 0.00, # Annual Pensionable Earnings ? YTD
                        employee.private_phone or '',
                        '',         # evening phone
                        employee.private_email or '',
                        employee.contract_id.date_start or '',  # start date
                        flag or 'Y', # Existing_member
                        '', # Aviva_category

                        #self._get_ae_status(employee.contract_id.ae_status),
                        #employee.contract_id.ae_date or '',  # date employee joined AE
                        #

                    ])
                    total += (employee_amount + employer_amount)

                # write footer
                writer.writerow(['T', total])

                # Prepare HTTP response
                csv_content = csv_buffer.getvalue()
                csv_buffer.close()
                filename = 'aviva_pension_export_{}_{}.csv'.format(datetime.today().strftime('%Y%m%d'), run_id)

                response = http.request.make_response(
                    csv_content,
                    headers=[
                        ('Content-Type', 'text/csv'),
                        ('Content-Disposition', f'attachment; filename={filename}')],
                )
                return response

        except ValueError:
            pension_fund = None  # or log, or raise custom error
            _log.info("Aviva pension fund NOT found")


    @staticmethod
    def _get_ae_status(status):

        if status:
            match status:
                case '1':
                    return 'Eligible'
                case '2':
                    return 'Non-eligible'
                case '3':
                    return 'Entitled'
                case '4':
                    return 'Contractual enrolment'
                case '5':
                    return 'Already in qualifying scheme'
                case '6':
                    return 'Not known'
                case  '7':
                    return 'Not applicable'

        return 'Not Known'





class P60(http.Controller):
    @http.route('/print/p60/<string:employee_ids>/<int:year>', type='http', auth='user')
    def uk_get_p60(self, employee_ids='', year=fields.Date.today().year, **kw):
        if not http.request.env.user.has_group('hr_payroll.group_hr_payroll_user') or not employee_ids or re.search(
                "[^0-9|,]", employee_ids):
            return http.request.not_found()

        ids = [int(s) for s in employee_ids.split(',')]
        employees = http.request.env['hr.employee'].browse(ids)
        _log.debug("Generate P60")

        pdf_writer = PdfFileWriter()

        for employee in employees:
            report = http.request.env.ref('l10n_uk_hr_payroll.action_report_p60', False)
            pdf_content, _ = http.request.env['ir.actions.report']. \
                with_context(lang='en_GB', year=year). \
                sudo()._render_qweb_pdf(report, employee.id)
            reader = PdfFileReader(io.BytesIO(pdf_content), strict=False, overwriteWarnings=False)

            for page in range(reader.getNumPages()):
                pdf_writer.addPage(reader.getPage(page))

        _buffer = io.BytesIO()
        pdf_writer.write(_buffer)
        merged_pdf = _buffer.getvalue()
        _buffer.close()

        report_name = "P60"

        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(merged_pdf)),
            ('Content-Disposition', http.content_disposition(report_name + '.pdf'))
        ]

        return http.request.make_response(merged_pdf, headers=pdfhttpheaders)
