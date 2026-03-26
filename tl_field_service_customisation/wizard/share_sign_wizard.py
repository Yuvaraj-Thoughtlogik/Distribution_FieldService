from odoo import api, fields, models, tools

class ShareSignWizard(models.TransientModel):
    _name = 'share.sign.wizard'
    _description = 'Share Sign Wizard'

    name = fields.Char(required=True, string="Name")
    sign_request_id = fields.Many2one('sign.request', string="Sign Request")

    line_ids = fields.One2many(
        'share.sign.line',
        'wizard_id',
        string="Signers",
        compute="_compute_line_ids"
    )

    @api.depends('sign_request_id')
    def _compute_line_ids(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        for rec in self:
            lines = []

            if rec.sign_request_id:
                for item in rec.sign_request_id.request_item_ids:
                    lines.append((0, 0, {
                        'name': item.partner_id.name,
                        'signer_id': item.partner_id.id,
                        'role': item.role_id.name,
                        'url': f"{base_url}/sign/document/{rec.sign_request_id.id}/{item.access_token}",
                    }))

            rec.line_ids = lines

class ShareSignWizardLine(models.TransientModel):
    _name = 'share.sign.line'
    _description = 'Share Sign Line'

    name = fields.Char(required=True, string="Name")
    signer_id = fields.Many2one('res.partner', string="Partner")
    role = fields.Char(required=True, string="Role")

    wizard_id = fields.Many2one(
        'share.sign.wizard',
        string="Wizard"
    )

    url = fields.Char(string="URL")

