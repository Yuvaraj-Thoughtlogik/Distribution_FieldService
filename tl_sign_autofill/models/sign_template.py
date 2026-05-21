# -*- coding: utf-8 -*-
import re

from odoo import models, fields, api, Command
from odoo.exceptions import ValidationError
from odoo.tools import _

class SignTemplate(models.Model):
    _inherit = 'sign.template'

    def send_sign_request_autofill(self, context = None , response=None):
        if context is None:
            context = {}
        self.ensure_one()

        valid_keys = set(
            self.sign_item_ids.filtered(lambda i: i.auto_fill).mapped('key')
        )

        incoming_keys = set(context.keys())

        invalid_keys = incoming_keys - valid_keys

        if invalid_keys:
            raise ValidationError(
                f"Invalid autofill keys: {', '.join(invalid_keys)}"
            )

        context = {
            'response': response,
            'default_template_id': self.id,
            **{k: v for k, v in context.items() if k in valid_keys},
        }

        return {
            'name': 'New Sign Request',
            'type': 'ir.actions.act_window',
            'res_model': 'sign.send.request',
            'view_mode': 'form',
            'context': context,
            'target': 'new',
        }

    def create_sign_request(self,reference,signers):
        self.ensure_one()
        values = []
        auto_fills = self.env.context.get('auto_fills')

        if not auto_fills:
            auto_fills = {}

        if not reference:
            raise ValidationError("Reference cannot be empty.")

        for item in self.sign_item_ids.filtered(lambda i: i.auto_fill):
            value = {
                'name': item.key,
                'value': auto_fills.get(item.key),
                'role_id': item.responsible_id.id,
                'sign_item_id': item.id,
                'by_system': item.by_system,
            }
            values.append((0, 0, value))

        sign_request = self.env['sign.request'].with_context(no_sign_mail=True).create({
            'template_id': self.id,
            'reference': reference,
            'request_item_ids': [Command.create({
                'partner_id': signer['partner_id'],
                'role_id': signer['role_id'],
            }) for signer in signers],
            'sign_autofill_ids':values,
        })

        return sign_request


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




