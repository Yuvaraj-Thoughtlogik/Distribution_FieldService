from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SignSendRequest(models.TransientModel):
    _inherit = 'sign.send.request'

    @api.model
    def _default_updated_signer_ids(self):
        template = self.env['sign.template']

        if self.env.context.get('active_model') == 'sign.template':
            template = self.env['sign.template'].browse(
                self.env.context.get('active_id') or self.env.context.get('default_template_id')
            )

        if not template:
            return []

        template._check_send_ready()

        default_signer = self.env.context.get(
            "default_signer_id",
            self.env.user.partner_id.id
        )

        user_role_id = self.env['ir.model.data']._xmlid_to_res_id(
            'sign.sign_item_role_user'
        )

        system_role = self.env.ref(
            'tl_sign_autofill.sign_role_system'
        )

        roles = template.sign_item_ids.responsible_id.sorted()

        signer_ids = []
        for default_signing_order, role in enumerate(roles):

            if role == system_role:
                continue

            signer_vals = {
                'role_id': role.id,
                'partner_id': False,
                'mail_sent_order': (
                    default_signing_order + 1
                    if self.set_sign_order else 1
                ),
            }

            if len(roles) == 1:
                signer_vals['partner_id'] = default_signer

            elif role.id == user_role_id:
                signer_vals['partner_id'] = default_signer

            signer_ids.append((0, 0, signer_vals))
        return signer_ids

    @api.model
    def _default_request_item_value_ids(self):
        template = self.env['sign.template']

        if self.env.context.get('active_model') == 'sign.template':
            template = self.env['sign.template'].browse(
                self.env.context.get('active_id')
            )
        else:
            template = self.env['sign.template'].browse(self.env.context.get('default_template_id'))

        if not template:
            return []

        values = []

        for item in template.sign_item_ids.filtered(lambda i: i.auto_fill):
            value = {
                'name': item.key,
                'required': item.required,
                'by_system': item.by_system,
                'value': self.env.context.get(item.key),
                'role_id': item.responsible_id.id,
                'sign_item_id': item.id,
            }
            values.append((0, 0, value))

        return values



    signer_ids = fields.One2many(
        'sign.send.request.signer',
        'sign_send_request_id',
        string="Signers",
        default=_default_updated_signer_ids
    )

    request_item_value_ids = fields.One2many(
        comodel_name='sign.send.item.value',
        inverse_name='sign_send_request_id',
        string="Request Item Values",
        default=_default_request_item_value_ids
    )

    @api.onchange('template_id', 'set_sign_order')
    def _onchange_template_id(self):
        super()._onchange_template_id()

        system_role = self.env.ref(
            'tl_sign_autofill.sign_role_system',
            raise_if_not_found=False
        )

        if not system_role:
            return

        self.signer_ids = self.signer_ids.filtered(
            lambda s: s.role_id.id != system_role.id
        )

        self.signers_count = len(self.signer_ids)

    def create_request(self):
        self.ensure_one()
        if any(
                v.required and v.by_system and not v.value
                for v in self.request_item_value_ids
        ):
            raise ValidationError(
                "Please provide values for all required 'Fill by System' fields."
            )
        sign_request = super().create_request()

        auto_fill_vals = []

        for item_value in self.request_item_value_ids:
            values = {
                'name': item_value.name,
                'value': item_value.value,
                'required': item_value.required,
                'by_system': item_value.by_system,
                'role_id': item_value.role_id.id,
                'sign_request_id': sign_request.id,
                'sign_item_id': item_value.sign_item_id.id,
            }
            # if item_value.role_id == system_role:
            #     values['fill_by'] = 'system'

            auto_fill_vals.append(values)
        if auto_fill_vals:
            self.env['sign.auto.fill.value'].create(auto_fill_vals)
        return sign_request

    def send_request(self):
        res = super().send_request()
        if self.env.context.get('response'):
            return self.env.context.get('response')
        else:
            return res

class SignSendItemValue(models.TransientModel):
    _name = "sign.send.item.value"
    _description = 'Sign Send Request Item Value'

    name = fields.Char()
    value = fields.Text()
    type = fields.Selection([('text','Text'),('line_item','Line Item')],default='text')
    fill_by = fields.Selection([('system','System'),('partner','Partner')])
    by_system = fields.Boolean(default=False)

    sign_item_id = fields.Many2one(comodel_name='sign.item', string='Sign Item',required=True)

    role_id = fields.Many2one('sign.item.role', string="Role")

    readonly = fields.Boolean(default=True)
    required = fields.Boolean()
    sign_send_request_id = fields.Many2one(comodel_name='sign.send.request')


