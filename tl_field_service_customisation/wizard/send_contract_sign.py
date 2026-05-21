from odoo import api, fields, models, tools


class SendContractSign(models.TransientModel):
    _name = 'send.contract.sign'
    _description = 'Send Contract with Sign'

    @api.model
    def _default_signer_ids(self):
        template = self.env['sign.template']
        if self.env.context.get('template_id'):
            template = self.env['sign.template'].browse(self.env.context.get('template_id'))
        if not template:
            return []
        template._check_send_ready()
        user_role_id = self.env['ir.model.data']._xmlid_to_res_id('sign.sign_item_role_user')
        role_customer_id = self.env['ir.model.data']._xmlid_to_res_id('sign.sign_item_role_customer')

        order_id = self.env['sale.order'].browse(self.env.context.get('default_order_id'))

        # system_role = self.env.ref('tl_sign_autofill.sign_role_system')
        # roles = template.sign_item_ids.responsible_id.filtered(
        #     lambda r: r.id != system_role.id
        # ).sorted(
        #     key=lambda r: r.id == role_customer_id
        # )
        roles = template.sign_item_ids
        signer_ids = []

        for default_signing_order, role in enumerate(roles):
            signer_vals = {
               'role_id': role.id,
               'partner_id': False,
            }
            if len(roles) == 1:
                signer_vals['partner_id'] = order_id.partner_id.id
            else:
                if role.id == user_role_id:
                    signer_vals['partner_id'] =  order_id.user_id.partner_id.id
                if role.id == role_customer_id:
                    signer_vals['partner_id'] = order_id.partner_id.id

            signer_ids.append((0, 0, signer_vals))
        return signer_ids

    order_id = fields.Many2one(comodel_name='sale.order',string='Order')
    signer_ids = fields.One2many('sign.send.request.signer', 'send_contract_sign_id', string="Signers", default=_default_signer_ids)
    set_sign_order = fields.Boolean(string="Set Sign Order")
    contract_id = fields.Many2one(comodel_name='service.contract', string="Contract")

    def action_assign(self):
        order = self.order_id
        if order:
            action = order.action_quotation_send()
            ctx = action.get('context', {})
            if order.contract_line_id and order.state == 'sale':
                contract_line = order.contract_line_id
                signers = [{'partner_id': signer.partner_id.id, 'role_id': signer.role_id.id,
                            'mail_sent_order': signer.mail_sent_order} for signer in self.signer_ids]

                contract_line.create_sign_request(signers = signers)
                sign_request = contract_line.sign_request_id

                sign_url = ""
                if sign_request and sign_request.request_item_ids:
                    base_url = order.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    role_customer_id = self.env['ir.model.data']._xmlid_to_res_id(
                        'sign.sign_item_role_customer'
                    )
                    item = sign_request.request_item_ids.filtered(
                        lambda r: r.role_id.id == role_customer_id
                    )[:1]

                    item = item and item[0] or False
                    sign_url = f"{base_url}/sign/document/{sign_request.id}/{item.access_token}"

                ctx.update({
                    'default_send_with_service_contract': True,
                    'default_service_contract_sign_url': sign_url,
                    'default_contract_line_id': order.contract_line_id.id,
                })

                action['context'] = ctx
            return action
        return None

    def action_send(self):
        line = self.contract_id.contract_line_ids[-1] if self.contract_id.contract_line_ids else False
        signers = [{'partner_id': signer.partner_id.id, 'role_id': signer.role_id.id,
                    'mail_sent_order': signer.mail_sent_order} for signer in self.signer_ids]
        if line:
            line.create_sign_request(signers=signers)
        return {'type': 'ir.actions.client', 'tag': 'soft_reload'}


class SignSendRequestSigner(models.TransientModel):
    _inherit = "sign.send.request.signer"

    send_contract_sign_id = fields.Many2one('send.contract.sign')