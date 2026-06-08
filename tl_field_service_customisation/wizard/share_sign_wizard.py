from markupsafe import Markup

from odoo import api, fields, models, tools

class ShareSignWizard(models.TransientModel):
    _name = 'share.sign.wizard'
    _description = 'Share Sign Wizard'

    # @api.model
    # def default_get(self, fields_list):
    #     res = super().default_get(fields_list)
    #
    #     sign_request = self.env['sign.request'].browse(
    #         self.env.context.get('default_sign_request_id')
    #     )
    #
    #     lines = []
    #     base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
    #
    #     for item in sign_request.request_item_ids:
    #         lines.append((0, 0, {
    #             'name': item.partner_id.name,
    #             'signer_id': item.partner_id.id,
    #             'request_item_id': item.id,
    #             'role': item.role_id.name,
    #             'url': f"{base_url}/sign/document/{sign_request.id}/{item.access_token}",
    #         }))
    #
    #     res['line_ids'] = lines
    #     return res
    #

    name = fields.Char(required=True, string="Name")
    sign_request_id = fields.Many2one('sign.request', string="Sign Request")
    service_contract_id = fields.Many2one(comodel_name='service.contract',string="Service Contract")
    request_item_ids = fields.One2many(related='sign_request_id.request_item_ids')

    # line_ids = fields.One2many(
    #     'share.sign.line',
    #     'wizard_id',
    #     string="Signers",
    #     # compute="_compute_line_ids",store=True,
    # )

# class ShareSignWizardLine(models.TransientModel):
#     _name = 'share.sign.line'
#     _description = 'Share Sign Line'
#
#     name = fields.Char(required=True, string="Name")
#     signer_id = fields.Many2one('res.partner', string="Partner")
#     role = fields.Char(required=True, string="Role")
#     request_item_id = fields.Many2one(comodel_name='sign.request.item',string="Request Item",required=True)
#     state = fields.Selection(related='request_item_id.state', string="State")
#     wizard_id = fields.Many2one(
#         'share.sign.wizard',
#         string="Wizard"
#     )
#
#     url = fields.Char(string="URL")

class SignRequestItem(models.Model):
    _inherit = 'sign.request.item'

    request_url = fields.Char(string="Request URL",compute='_compute_request_url')

    @api.depends('sign_request_id')
    def _compute_request_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for rec in self:
            rec.request_url = f"{base_url}/sign/document/{rec.sign_request_id.id}/{rec.access_token}"