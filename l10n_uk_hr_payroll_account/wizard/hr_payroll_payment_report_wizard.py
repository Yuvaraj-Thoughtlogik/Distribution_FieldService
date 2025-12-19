# AUGUR Payroll Proprietary License v1.0
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
import base64
import csv
from datetime import datetime, date
import logging

from odoo import api, fields, models, http, _
from odoo.tools.misc import xlsxwriter
from odoo.tools import format_list, float_repr
from odoo.exceptions import UserError

_log = logging.getLogger(__name__)

# This is a temporary fix for the Natwest file format.
# TODO A better way to do this would be to mimic the NATCHA format and generate a new payment type
# or extend the iso20022 implementation
class HrPayrollPaymentReportWizard(models.TransientModel):
    _inherit = 'hr.payroll.payment.report.wizard'

    export_format = fields.Selection(selection_add=[('uk_natwest_bankline', 'UK Natwest Bankline')],
                                     default='uk_natwest_bankline', ondelete={'uk_natwest_bankline': 'set csv'})

    payment_date = fields.Date(string='Payment Date',
                                 help='Payment Date: the banking day on which you intend the payslip batch to be settled.',
                                 default=fields.Date.context_today)
    journal_id = fields.Many2one(
        string='Bank Journal', comodel_name='account.journal', required=True,
        default=lambda self: self.env['account.journal'].search([('type', '=', 'bank')], limit=1))

    def generate_payment_lines(self):
        """Mimics the SQL logic to generate a custom export structure."""
        lines = []

        # Header row (type 08) - Pay from account
        partner_banks = self.env['res.partner.bank'].search([
            ('allow_out_payment', '=', True),
            ('currency_id', '=', self.payslip_run_id.company_id.currency_id.id),
            ('partner_id', '=', self.payslip_run_id.company_id.partner_id.id),
        ])
        for bank in partner_banks:
            bic_acc_number = (bank.bank_id.bic or '') + (bank.acc_number or '')
            lines.append([
                *[''] * 3, '08', *[''] * 8,
                bic_acc_number, *[''] * 5, self.payslip_run_id.payment_date.strftime('%d%m%Y'),
                *[''] * 76
            ])

        #for slip in self.payslip_ids.filtered(lambda p: p.state == "done" and p.net_wage > 0):
        #    lines.append(slip._get_payments_vals(self.journal_id))
        #payment_method_code = self.env.context.get('payment_method') or 'uk_bacs'


        # Detail rows (type 09) - Pay to account
        payslips = self.env['hr.payslip'].search([
            ('payslip_run_id', '=', self.payslip_run_id.id),
            ('company_id', '=', self.company_id.id),
            ('state', '=', 'done'),
            ('net_wage', '>', 0),
        ])

        for payslip in payslips:
            net_line = payslip.line_ids.filtered(lambda l: l.code == 'NET')
            if not net_line:
                continue
            amount = net_line[0].total
            employee = payslip.employee_id
            bank = employee.bank_account_id
            if not bank:
                continue
            sort_code = bank.bank_id.bic if bank.bank_id else ''
            acc_number = bank.acc_number or ''

            lines.append([
                *[''] * 3, '09', *[''] * 11,
                'GBP',
                float_repr(amount, 2),
                *[''] * 6,
                sort_code, *[''] * 4, acc_number, '', employee.name or '',
                *[''] * 2, self.company_id.name or '',
                *[''] * 48
            ])

        return lines

    def _perform_checks(self):
        super()._perform_checks()
        if self.export_format == 'uk_natwest_bankline' or self.export_format == 'csv':
            employees = self.payslip_ids.employee_id.filtered(lambda e: not e.bank_account_id)
            if employees:
                raise UserError(_(
                    "Some employees (%s) don't have a bank account.",
                    format_list(self.env, employees.mapped('name'))))

            employees = self.payslip_ids.employee_id.filtered(lambda e: not e.bank_account_id.bank_id.bic )
            if employees:
                raise UserError(_(
                    "Some employees (%s) don't have a valid bank account sort code.",
                    format_list(self.env, employees.mapped('name'))))

            #if self.journal_id.bank_account_id.acc_type != 'iban':
            #    raise UserError(_(
            #        "The journal '%s' requires a proper IBAN account to pay via UK BACS. "
            #        "Please configure it first.",
            #        self.journal_id.name))

    def _export_natwest(self):
        lines = self.generate_payment_lines()

        output = io.StringIO()
        report_data = csv.writer(output)
        report_data.writerows(lines)

        _log.info("Report: " + output.getvalue())

        return base64.encodebytes(output.getvalue().encode())

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if 'export_format' in fields_list:
            defaults['export_format'] = 'uk_natwest_bankline'
        return defaults


    def generate_payment_report(self):
        super().generate_payment_report()
        if self.export_format == 'uk_natwest_bankline' or self.export_format == 'csv':
            _log.info("After export format: " + str(self.export_format))
            # The payment report is generated for a batch
            if self.payslip_run_id:
                self.payslip_run_id.payment_date = self.payment_date
            # The payment report is generated for a single payslip
            else:
                self.payslip_ids[0].paid_date = self.payment_date

            payment_report = self._export_natwest()
            filename = 'payroll_uk_natwest_export_{}_{}.txt'.format(datetime.today().strftime('%Y%m%d'),
                                                                 self.payslip_run_id.name)

            self._write_file(payment_report, filename)

        return None