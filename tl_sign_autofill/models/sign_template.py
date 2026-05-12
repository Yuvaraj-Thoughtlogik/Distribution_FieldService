# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import _


class SignItem(models.Model):
    _inherit = 'sign.item'

    is_editable = fields.Boolean(default=False, compute='_compute_is_editable')

    @api.depends('responsible_id')
    def _compute_is_editable(self):
        system_role = self.env.ref('tl_sign_autofill.sign_role_system')
        for record in self:
            record.is_editable = True if record.responsible_id == system_role else False


class SignRequest(models.Model):
    _inherit = 'sign.request'

    def _check_signers_roles_validity(self):
        for sign_request in self:
            system_role = self.env.ref('tl_sign_autofill.sign_role_system')

            template_roles = sign_request.sudo().template_id.sign_item_ids.responsible_id.filtered(
                lambda r: r.id != system_role.id
            )
            print(template_roles)
            sign_request_items = sign_request.request_item_ids.filtered(
                lambda r: r.role_id.id != system_role.id
            )
            if len(sign_request_items) != max(len(template_roles), 1) or \
                    set(sign_request_items.role_id.ids) != (set(template_roles.ids) if template_roles else set([self.env.ref('sign.sign_item_role_default').id])):
                raise ValidationError(_("You must specify one signer for each role of your sign template"))

