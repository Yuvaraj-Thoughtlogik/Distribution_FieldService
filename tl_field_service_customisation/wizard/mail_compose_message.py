from odoo import _, api, fields, models, Command, tools
from markupsafe import Markup


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    send_with_service_contract = fields.Boolean(string='Send with Service Contract Sign Request')
    service_contract_sign_url = fields.Char(string='Sign Url')
    contract_line_id = fields.Many2one(string='Contract Line',comodel_name='service.contract.line')


    def _set_value_from_template(self, template_fname, composer_fname=False):
            res = super()._set_value_from_template(template_fname, composer_fname)

            composer_fname = composer_fname or template_fname

            if (
                    template_fname == 'body_html'
                    and composer_fname == 'body'
                    and self.send_with_service_contract
                    and self.body
                    and 'Service Contract' not in self.body  # avoid duplicate
            ):
                sign_url = self.service_contract_sign_url

                extra_html = Markup(f"""
                     <div style="margin: 16px 0;">
                         <p><strong>Signature Required:</strong></p>
                         <a href="{sign_url}"
                            style="background-color:#875A7B; padding:10px 15px; text-decoration:none; color:#fff; border-radius:5px; font-size:13px; display:inline-block;">
                             Click here to Sign Contract
                         </a>
                     </div>
                 """)

                # Ensure body is treated as HTML
                self.body = Markup(self.body) + extra_html

            return res

    def action_send_mail(self):
        res = super().action_send_mail()
        if self.send_with_service_contract:
            self.contract_line_id.send_non_customer_emails()
        return res
