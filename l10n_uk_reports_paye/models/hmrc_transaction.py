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
from urllib.parse import urlparse

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools.misc import format_date
from odoo.tools import float_repr, DEFAULT_SERVER_DATETIME_FORMAT
import json
from lxml import etree
from markupsafe import Markup

from odoo.addons.l10n_uk_hmrc.models.hmrc_transaction import _send_request

# Log ticket to get test credentials
CLASS_PAYE_FPS_RETURN = "HMRC-PAYE-RTI-FPS"
CLASS_PAYE_EPS_RETURN = "HMRC-PAYE-RTI-EPS"
TEMPLATE_PAYE_FPS_RETURN_BODY = "l10n_uk_reports_paye.hmrc_paye_fps_return_body"
TEMPLATE_PAYE_EPS_RETURN_BODY = "l10n_uk_reports_paye.hmrc_paye_eps_return_body"
TEMPLATE_TRANSACTION_ENGINE_BASE = "l10n_uk_reports_paye.hmrc_transaction_engine_base"

# URLs for namespace

namespaces_fps = {
    2013: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/FullPaymentSubmission/13-14/2",
    2014: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/FullPaymentSubmission/14-15/4",
    2015: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/FullPaymentSubmission/15-16/1",
    2016: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/FullPaymentSubmission/16-17/2",
    2017: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/FullPaymentSubmission/17-18/1",
    2018: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/FullPaymentSubmission/18-19/1",
    2019: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/FullPaymentSubmission/19-20/1",
    2020: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/FullPaymentSubmission/20-21/1",
    2021: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/FullPaymentSubmission/21-22/1",
    2022: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/FullPaymentSubmission/22-23/1",
    2023: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/FullPaymentSubmission/23-24/2",
    2024: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/FullPaymentSubmission/24-25/1",
    2025: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/FullPaymentSubmission/25-26/1",
    2026: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/FullPaymentSubmission/26-27/1",
}

namespaces_eps = {
    2013: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/EmployerPaymentSummary/13-14/2",
    2014: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/EmployerPaymentSummary/14-15/4",
    2015: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/EmployerPaymentSummary/15-16/1",
    2016: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/EmployerPaymentSummary/16-17/2",
    2017: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/EmployerPaymentSummary/17-18/1",
    2018: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/EmployerPaymentSummary/18-19/1",
    2019: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/EmployerPaymentSummary/19-20/1",
    2020: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/EmployerPaymentSummary/20-21/1",
    2021: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/EmployerPaymentSummary/21-22/1",
    2022: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/EmployerPaymentSummary/22-23/1",
    2023: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/EmployerPaymentSummary/23-24/2",
    2024: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/EmployerPaymentSummary/24-25/1",
    2025: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/EmployerPaymentSummary/25-26/1",
    2026: "http://www.govtalk.gov.uk/taxation/PAYE/RTI/EmployerPaymentSummary/26-27/1",
}



import logging

_log = logging.getLogger(__name__)

class HmrcTransaction(models.Model):
    _inherit = "l10n_uk.hmrc.transaction"

    transaction_type = fields.Selection(
        string="Transaction type",
        selection_add=[('paye_fps_return', 'FPS Return'),
                       ('paye_eps_return', 'EPS Return')],
        ondelete={
            'paye_fps_return': 'set default',
            'paye_eps_return': 'set default',
        },
    )

    document_attachment_id = fields.Many2one(string="Document Attachment", comodel_name='ir.attachment')

    def _generate_fps_mr_xml_data(self, credentials, document_data):
        self.ensure_one()
        nil_return_indicator = not bool(document_data['employee_return_ids'])

        # TODO remove this once all of the fields are mapped
        dummy = 'dummy'


        related_tax_year = '24-25'
        year = self.company_id.get_last_ytd_reset_date(self.period_end).strftime('%Y')
        related_tax_year = year[-2:] + '-' + str(int(year[-2:]) + 1)
        _log.debug("Year: " + related_tax_year + " " + year)

        # "no" by default: see data/ir_cron.xml
        if self.env['ir.config_parameter'].sudo().get_param('l10n_uk_hmrc.api_live') == 'yes':
            doc_class = CLASS_PAYE_FPS_RETURN
        else:
            doc_class = CLASS_PAYE_FPS_RETURN + '-TIL'

        xml_data = {
            'credentials': credentials,
            'document': {
                'employees': [],
                'namespaces': {
                    'year': namespaces_fps[int(year)],
                },
                'related_tax_year': related_tax_year,
                'period_end': self.period_end,
                'scheme_ceased_date': document_data['scheme_ceased_date'],
                # TODO Nil Return required
                # 'nil_return_indicator': self.nil_return_indicator,
                # 'inactivity_indicator': self.inactivity_indicator,
            },
            'transaction': {
                'mode': self.env['ir.config_parameter'].sudo().get_param("l10n_uk_hmrc.api_mode", 'production'),
                'class': doc_class,
                'body_template': TEMPLATE_PAYE_FPS_RETURN_BODY,
            },
        }

        if not nil_return_indicator:
            for employee_return in document_data['employee_return_ids']:
                xml_data['document']['employees'].append({
                        'id': employee_return['id'],
                        'nino': employee_return['nino'],
                        'forename': employee_return['forename'],
                        'surname': employee_return['surname'],
                        'address1': employee_return['address1'],
                        'address2': employee_return['address2'],
                        'address3': employee_return['address3'],
                        'postcode': employee_return['postcode'],
                        'dob': employee_return['dob'],
                        'gender': employee_return['gender'],
                        'is_director': employee_return['is_director'],
                        'ytd_basis': employee_return['ytd_basis'],
                        'appointed_week': employee_return['appointed_week'],
                        'works_id': employee_return['works_id'],
                        'leaving_date': employee_return['leaving_date'],
                        'taxable_pay_ytd': employee_return['taxable_pay_ytd'],
                        'total_tax_ytd': employee_return['total_tax_ytd'],
                        'total_pension_paid': employee_return['total_pension_paid'],
                        'pay_frequency': employee_return['pay_frequency'],
                        'payment_date': employee_return['payment_date'],
                        'late_reason': employee_return['late_reason'],
                        'period_no': employee_return['period_no'],
                        'periods_covered': employee_return['periods_covered'],
                        'hours_worked': employee_return['hours_worked'],
                        'tax_code': employee_return['tax_code'],
                        'tax_regime': employee_return['tax_regime'],
                        'non_cumulative': employee_return['non_cumulative'],
                        'taxable_pay': employee_return['taxable_pay'],
                        'pay_after_stat_deductions': employee_return['pay_after_stat_deductions'],
                        'employee_pension_contributions_not_paid': employee_return['employee_pension_contributions_not_paid'],
                        'employee_pension_contributions_not_paid_ytd': employee_return['employee_pension_contributions_not_paid_ytd'],
                        'employee_pension_contributions_paid': employee_return['employee_pension_contributions_paid'],
                        'employee_pension_contributions_paid_ytd': employee_return['employee_pension_contributions_paid_ytd'],
                        'tax_deducted_or_refunded': employee_return['tax_deducted_or_refunded'],
                        'has_student_loan': employee_return['has_student_loan'],
                        'has_post_graduate_loan': employee_return['has_post_graduate_loan'],
                        'sl_amt': employee_return['sl_amt'],
                        'pl_amt': employee_return['pl_amt'],
                        'payroll_benefits': employee_return['payroll_benefits'],
                        'payroll_benefits_ytd': employee_return['payroll_benefits_ytd'],
                        'total_sl_ytd': employee_return['total_sl_ytd'],
                        'total_pl_ytd': employee_return['total_pl_ytd'],
                        'sl_plan': employee_return['sl_plan'],
                        'ni_letter': employee_return['ni_letter'],
                        'gross_earnings_for_nic_in_period': employee_return['gross_earnings_for_nic_in_period'],# float_repr(employee_return['gross_earnings_for_nic_in_period'], 2),
                        'gross_earnings_for_nic_ytd': employee_return['gross_earnings_for_nic_ytd'],
                        'gross_earnings_at_lel_ytd': employee_return['gross_earnings_at_lel_ytd'],
                        'gross_earnings_lel_to_pt_ytd': employee_return['gross_earnings_lel_to_pt_ytd'],
                        'gross_earnings_pt_to_uel_ytd': employee_return['gross_earnings_pt_to_uel_ytd'],
                        'total_employer_nic_in_period': employee_return['total_employer_nic_in_period'],
                        'total_employer_nic_ytd': employee_return['total_employer_nic_ytd'],
                        'employee_ni_contributions_in_period': employee_return['employee_ni_contributions_in_period'],
                        'employee_ni_contributions_ytd': employee_return['employee_ni_contributions_ytd'],
                        'on_strike': employee_return['on_strike'],
                        'unpaid_absence': employee_return['unpaid_absence'],
                        'smp_ytd': employee_return['smp_ytd'],
                        'spp_ytd': employee_return['spp_ytd'],
                        'sap_ytd': employee_return['sap_ytd'],
                        'shpp_ytd': employee_return['shpp_ytd'],
                        'spb_ytd': employee_return['spb_ytd'],
                })
        xml_data['ir_mark'] = self._generate_ir_mark(xml_data)
        _log.debug('IRMark: ' + str(xml_data['ir_mark']))
        return xml_data

    def _submit_fps_mr_transaction(self, credentials, document_data):
        self.ensure_one()

        xml_data = self._generate_fps_mr_xml_data(credentials, document_data)
        return_document = self._generate_xml_document(xml_data)

        # todo Temporary Logging - has clear text password
        _log.info("Sending Document: " + str(return_document))

        # We render it twice. The second time without credentials to store it in an attachment
        xml_data['credentials'] = {}
        return_document_safe = self._generate_xml_document(xml_data)
        document_string = etree.tostring(etree.fromstring(return_document_safe), pretty_print=True,
                                         xml_declaration=True, encoding='UTF-8').decode()
        self.document_attachment_id = self.env['ir.attachment'].create({
            'raw': document_string,
            'name': f'hmrc_transaction_document_paye_fps_{self.period_end}.xml',
            'res_model': self._name,
            'res_id': self.id,
        })

        response, header = _send_request(self, return_document)

        if header['qualifier'] != 'acknowledgement':
            self._handle_submission_error(response, header)

        response_write_vals = {
            'next_endpoint': urlparse(header['response_end_point']).path,
            'next_polling': fields.Datetime.add(fields.Datetime.now(), seconds=int(header['poll_interval'])).strftime(
                DEFAULT_SERVER_DATETIME_FORMAT),
            'correlation_id': header['correlation_id'],
            'state': 'polling',
        }
        self.write(response_write_vals)
        self.env.ref('l10n_uk_hmrc.ir_cron_l10n_uk_hmrc_process_transactions')._trigger()

    def _generate_eps_mr_xml_data(self, credentials, document_data):
        self.ensure_one()
        # nil_return_indicator = not bool(document_data['employee_return_ids'])

        # TODO remove this once all of the fields are mapped

        related_tax_year = '24-25'
        year = self.company_id.get_last_ytd_reset_date(self.period_end).strftime('%Y')
        related_tax_year = year[-2:] + '-' + str(int(year[-2:]) + 1)
        _log.debug("Year: " + related_tax_year + " " + year)

        # "no" by default: see data/ir_cron.xml
        if self.env['ir.config_parameter'].sudo().get_param('l10n_uk_hmrc.api_live') == 'yes':
            doc_class = CLASS_PAYE_EPS_RETURN
        else:
            doc_class = CLASS_PAYE_EPS_RETURN + '-TIL'

        xml_data = {
            'credentials': credentials,
            'document': {
                'namespaces': {
                    'year': namespaces_eps[int(year)],
                },
                'related_tax_year': related_tax_year,
                'period_end': self.period_end,
                # TODO Nil Return required
                # 'nil_return_indicator': self.nil_return_indicator,
                # 'inactivity_indicator': self.inactivity_indicator,

            },
            'eps': document_data,
            'transaction': {
                'mode': self.env['ir.config_parameter'].sudo().get_param("l10n_uk_hmrc.api_mode", 'production'),
                'class': doc_class,
                'body_template': TEMPLATE_PAYE_EPS_RETURN_BODY,
            },

        }

        xml_data['ir_mark'] = self._generate_ir_mark(xml_data)
        return xml_data

    def _submit_eps_mr_transaction(self, credentials, document_data):
        self.ensure_one()

        xml_data = self._generate_eps_mr_xml_data(credentials, document_data)
        return_document = self._generate_xml_document(xml_data)

        # todo Temporary Logging - has clear text password
        _log.info("Sending Document: " + str(return_document))

        # We render it twice. The second time without credentials to store it in an attachment
        xml_data['credentials'] = {}
        return_document_safe = self._generate_xml_document(xml_data)
        document_string = etree.tostring(etree.fromstring(return_document_safe), pretty_print=True,
                                         xml_declaration=True, encoding='UTF-8').decode()
        self.document_attachment_id = self.env['ir.attachment'].create({
            'raw': document_string,
            'name': f'hmrc_transaction_document_paye_eps_{self.period_end}.xml',
            'res_model': self._name,
            'res_id': self.id,
        })

        response, header = _send_request(self, return_document)

        if header['qualifier'] != 'acknowledgement':
            self._handle_submission_error(response, header)

        response_write_vals = {
            'next_endpoint': urlparse(header['response_end_point']).path,
            'next_polling': fields.Datetime.add(fields.Datetime.now(), seconds=int(header['poll_interval'])).strftime(
                DEFAULT_SERVER_DATETIME_FORMAT),
            'correlation_id': header['correlation_id'],
            'state': 'polling',
        }
        self.write(response_write_vals)
        self.env.ref('l10n_uk_hmrc.ir_cron_l10n_uk_hmrc_process_transactions')._trigger()

    def _handle_success(self):

        # TODO Update status and payslip statistics
        # Update IRMARK on Payslips & and mark as submitted
        # send submission to Augur Solutions for metrics

        # for payslip in self.env['hr.payslip'].search([('state', 'in', ['paid']),
        #                                             ('l10n_uk_hmrc_status', '=', 'S'),
        #                                             ('company_id', '=', self.env.company.id),
        #                                             ('l10n_uk_hmrc_transaction', '=', self.id),
        #                                              ]):
        #    payslip.set_hmrc_status = 'C'

        # TODO send status to Augur Solutions

        super()._handle_success()
        email_template_fps = self.env.ref('l10n_uk_reports_paye.email_template_fps_response', raise_if_not_found=False)
        email_template_eps = self.env.ref('l10n_uk_reports_paye.email_template_eps_response', raise_if_not_found=False)

        if self.transaction_type == 'paye_fps_return' and email_template_fps:
            email_template_fps.send_mail(
                self.id,
                force_send=True,
                email_values={'attachment_ids': self.response_attachment_id.ids},
            )
        elif self.transaction_type == 'paye_eps_return' and email_template_eps:
            email_template_eps.send_mail(
                self.id,
                force_send=True,
                email_values={'attachment_ids': self.response_attachment_id.ids},
            )

    def _handle_request_error(self, error_data, transaction_type):

        # for error in error_data['errors']:
        #    message = str(error_data['type']) +  ": HMRC Transaction Error Code: " + str(error['code']) + ' ' + str(error['message']) + str(transaction_type)
        #    _log.info(message)

        # TODO Work around this bug - make sure we log a PR
        # caused by the translation of the HMRC code at line 166
        # doo.tools.translate: no translation language detected, skipping translation <frame at 0x7e09216dece0, file '/mnt/extra-addons/l10n_uk_hmrc/models/hmrc_transaction.py', line 166, code <genexpr>>
        # web_1  | Stack (most recent call last):
        # web_1  |   File "/usr/lib/python3.12/threading.py", line 1030, in _bootstrap
        # web_1  |     self._bootstrap_inner()
        # web_1  |   File "/usr/lib/python3.12/threading.py", line 1073, in _bootstrap_inner
        # web_1  |     self.run()
        # web_1  |   File "/usr/lib/python3.12/threading.py", line 1010, in run
        # web_1  |     self._target(*self._args, **self._kwargs)
        # web_1  |   File "/usr/lib/python3/dist-packages/odoo/service/server.py", line 500, in target
        # web_1  |     self.cron_thread(i)
        # web_1  |   File "/usr/lib/python3/dist-packages/odoo/service/server.py", line 483, in cron_thread
        # web_1  |     _run_cron(cr)

        super()._handle_request_error(error_data, transaction_type)

        """
                Handles the request when it resulted with an error after sending it to HMRC Transaction engine.
                Can be overidden.
                Refer to this link for an example (CIS monthly return): https://assets.publishing.service.gov.uk/media/5a7ed5b8e5274a2e87db234c/monthly-return-response-messages.pdf
                """
        if error_data['type'] == 'fatal':
            html_body = Markup("""
                        <h4>Fatal: %s</h4>
                        <p>%s:%s</p>
                    """) % (error_data['code'], error_data['location'], error_data['message'])
            self.company_id.message_post(body=html_body, attachment_ids=self.response_attachment_id.ids)
            _log.info("HMRC Error: " + str(html_body))
            return

        errors = Markup().join(
            Markup("<li>{title}:{code} {location}:{message}</li>").format(
                title=("Code"),
                code=error['code'],
                location=error['location'],
                message=error['message']
            ) for error in error_data['errors']
        )

        error_message = _("HMRC transaction error") if transaction_type == 'polling' else _(
            "HMRC transaction deletion error")
        html_body = Markup("""
                    <p>%s:</p>
                    <ul>%s</ul>
                """) % (error_message, errors)
        self.company_id.message_post(body=html_body, attachment_ids=self.response_attachment_id.ids)

        email_template_fps = self.env.ref('l10n_uk_reports_paye.email_template_fps_response_failure',
                                          raise_if_not_found=False)
        email_template_eps = self.env.ref('l10n_uk_reports_paye.email_template_eps_response_failure',
                                          raise_if_not_found=False)

        if self.transaction_type == 'paye_fps_return' and transaction_type == 'polling' and email_template_fps:

            email_template_fps.send_mail(
                self.id,
                force_send=True,
                email_values={'attachment_ids': self.response_attachment_id.ids},
            )
        elif self.transaction_type == 'paye_eps_return' and transaction_type == 'polling' and email_template_eps:
            email_template_eps.send_mail(
                self.id,
                force_send=True,
                email_values={'attachment_ids': self.response_attachment_id.ids},
            )

    def _handle_submission_error(self, response, header):
        error = self._get_errors_from_response(response.content)
        _log.info("HMRC Transaction Error Code: " + str(error['code']) + ' ' + str(error['message']) + ' ' + str(
            error['location']))

        super()._handle_submission_error(response, header)

    def _get_transaction_class(self):

        # "no" by default: see data/ir_cron.xml
        message_add = '-TIL' if self.env['ir.config_parameter'].sudo().get_param('l10n_uk_hmrc.api_live') != 'yes' else ''

        match str(self.transaction_type):
            case 'paye_fps_return':
                return CLASS_PAYE_FPS_RETURN + message_add
            case 'paye_eps_return':
                return CLASS_PAYE_EPS_RETURN + message_add
            case 'cis_monthly_return':
                return 'IR-CIS-CIS300MR'

        super()._get_transaction_class()


    @api.model
    def _generate_xml_document(self, xml_data):
        # redefine the template
        return self.env['ir.qweb']._render(TEMPLATE_TRANSACTION_ENGINE_BASE, xml_data)

class hmrcConfirmationWizard(models.TransientModel):
    _name = 'hmrc.confirmation.wizard'
    _description = 'HMRC Confirmation Wizard'

    message = fields.Text(default="Your HMRC return has been sent", readonly=True)
