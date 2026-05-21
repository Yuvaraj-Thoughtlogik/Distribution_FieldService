from odoo.exceptions import ValidationError
from odoo import models, fields, api
from odoo.tools import _

class SignRequest(models.Model):
    _inherit = 'sign.request'

    sign_autofill_ids = fields.One2many(comodel_name='sign.auto.fill.value',inverse_name='sign_request_id', string='Sign Auto Fill')

    @api.model_create_multi
    def create(self, vals_list):

        auto_fills = self.env.context.get('auto_fills', {})

        for vals in vals_list:

            template = self.env['sign.template'].browse(
                vals.get('template_id')
            )

            for item in template.sign_item_ids.filtered(
                    lambda i: i.auto_fill and i.required and i.by_system
            ):

                value = auto_fills.get(item.key)

                if not value:
                    raise ValidationError(_(
                        "Please provide a value for required readonly field: %s"
                    ) % item.name)

            vals['sign_autofill_ids'] = template.get_auto_fill_values()

        return super().create(vals_list)
    # def _check_signers_roles_validity(self):
    #     for sign_request in self:
    #         system_role = self.env.ref('tl_sign_autofill.sign_role_system')
    #
    #         template_roles = sign_request.sudo().template_id.sign_item_ids.responsible_id.filtered(
    #             lambda r: r.id != system_role.id
    #         )
    #         sign_request_items = sign_request.request_item_ids.filtered(
    #             lambda r: r.role_id.id != system_role.id
    #         )
    #         if len(sign_request_items) != max(len(template_roles), 1) or \
    #                 set(sign_request_items.role_id.ids) != (set(template_roles.ids) if template_roles else set([self.env.ref('sign.sign_item_role_default').id])):
    #             raise ValidationError(_("You must specify one signer for each role of your sign template"))

    # def _check_signers_partners_validity(self):
    #     system_role = self.env.ref('tl_sign_autofill.sign_role_system', raise_if_not_found=False)
    #
    #     for sign_request in self:
    #         sign_request_items = sign_request.request_item_ids
    #
    #         if system_role:
    #             sign_request_items = sign_request_items.filtered(
    #                 lambda r: r.role_id != system_role
    #             )
    #
    #         if sign_request.state == 'shared' and (
    #                 len(sign_request_items) != 1 or sign_request_items.partner_id
    #         ):
    #             raise ValidationError(
    #                 _("A shared sign request should only have one signer with an empty partner")
    #             )
    #
    #         if sign_request.state != 'shared' and any(
    #                 not sri.partner_id for sri in sign_request_items
    #         ):
    #             raise ValidationError(
    #                 _("A non-shared sign request's should not have any signer with an empty partner")
    #             )


class SignItem(models.Model):
    _inherit = 'sign.item'

    auto_fill = fields.Boolean(default=False,store=True)
    by_system = fields.Boolean(default=True)
    key = fields.Char(compute='_compute_key',store=True,readonly=False)

    @api.constrains('key', 'template_id', 'responsible_id')
    def _check_unique_key(self):

        for record in self:
            if (
                    not record.key
                    or not record.template_id
            ):
                continue

            duplicate = self.search([
                ('id', '!=', record.id),
                ('template_id', '=', record.template_id.id),
                ('key', '=', record.key),
            ], limit=1)

            if duplicate:
                raise ValidationError(
                    f'Key "{record.key}" already exists in this template.'
                )

    @api.depends('name')
    def _compute_key(self):
        for record in self:

            # Keep existing key if already set manually
            if record.key:
                continue

            base_key = (record.name or '').strip().lower().replace(' ', '_')
            auto_fill_key = base_key
            count = 1

            # Make unique key inside template
            while self.search([
                ('id', '!=', record.id),
                ('template_id', '=', record.template_id.id),
                ('key', '=', auto_fill_key),
            ], limit=1):
                auto_fill_key = f"{base_key}_{count}"
                count += 1

            record.key = auto_fill_key

class SignAutoFillValue(models.Model):
    _name = 'sign.auto.fill.value'
    _description = 'Sign Autofill Value'

    name = fields.Char()
    value = fields.Text()
    type = fields.Selection([('text','Text'),('line_item','Line Item')],default='text')
    role_id = fields.Many2one('sign.item.role', string="Role",compute='_compute_role_id',store=True)
    fill_by = fields.Selection([('system','System'),('partner','Partner')])
    by_system = fields.Boolean(default=False)

    readonly = fields.Boolean(default=True)
    required = fields.Boolean()
    sign_request_id = fields.Many2one(comodel_name='sign.request')
    sign_item_id = fields.Many2one(comodel_name='sign.item', string='Sign Item')

    @api.depends( 'sign_item_id.responsible_id')
    def _compute_role_id(self):
        for record in self:
            record.role_id = record.sign_item_id.responsible_id.id


class SignTemplate(models.Model):
    _inherit = 'sign.template'


    def get_auto_fill_values(self):
        self.ensure_one()

        auto_fills = self.env.context.get('auto_fills', {})

        autofill_values = []

        for item in self.sign_item_ids.filtered(lambda i: i.auto_fill):

            value = auto_fills.get(item.key)

            autofill_values.append((0, 0, {
                'name': item.key,
                'value': value,
                'required': item.required,
                'role_id': item.responsible_id.id,
                'sign_item_id': item.id,
                'by_system': item.by_system,
            }))
        return autofill_values

