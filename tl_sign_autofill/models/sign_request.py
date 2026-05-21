from odoo.exceptions import ValidationError
from odoo import models, fields, api
from odoo.tools import _

class SignRequest(models.Model):
    _inherit = 'sign.request'

    sign_autofill_ids = fields.One2many(comodel_name='sign.auto.fill.value',inverse_name='sign_request_id', string='Sign Auto Fill')


    def _check_signers_roles_validity(self):
        for sign_request in self:
            system_role = self.env.ref('tl_sign_autofill.sign_role_system')

            template_roles = sign_request.sudo().template_id.sign_item_ids.responsible_id.filtered(
                lambda r: r.id != system_role.id
            )
            sign_request_items = sign_request.request_item_ids.filtered(
                lambda r: r.role_id.id != system_role.id
            )
            if len(sign_request_items) != max(len(template_roles), 1) or \
                    set(sign_request_items.role_id.ids) != (set(template_roles.ids) if template_roles else set([self.env.ref('sign.sign_item_role_default').id])):
                raise ValidationError(_("You must specify one signer for each role of your sign template"))

    def _check_signers_partners_validity(self):
        system_role = self.env.ref('tl_sign_autofill.sign_role_system', raise_if_not_found=False)

        for sign_request in self:
            sign_request_items = sign_request.request_item_ids

            if system_role:
                sign_request_items = sign_request_items.filtered(
                    lambda r: r.role_id != system_role
                )

            if sign_request.state == 'shared' and (
                    len(sign_request_items) != 1 or sign_request_items.partner_id
            ):
                raise ValidationError(
                    _("A shared sign request should only have one signer with an empty partner")
                )

            if sign_request.state != 'shared' and any(
                    not sri.partner_id for sri in sign_request_items
            ):
                raise ValidationError(
                    _("A non-shared sign request's should not have any signer with an empty partner")
                )

class SignRequestItem(models.Model):
    _inherit = "sign.request.item"

    is_editable = fields.Boolean(default=False,store=True)
    # sign_autofill_value_ids = fields.One2many(comodel_name='sign.auto.fill.value',inverse_name='sign_request_item_id', string='Sign Auto Fill')