from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, Command
from markupsafe import Markup
from odoo.tools import _
from odoo.exceptions import UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)

class ServiceContract(models.Model):
    _name = 'service.contract'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = "Service Contract"

    sale_id = fields.Many2one('sale.order', string="Sale Order", required=True)
    asset_ids = fields.Many2many(
        comodel_name='customer.asset',
        compute='_compute_asset_ids',
        string="Customer Assets"
    )
    partner_id = fields.Many2one(comodel_name='res.partner',related='sale_id.partner_id')
    partner_shipping_id = fields.Many2one(comodel_name='res.partner',related='sale_id.partner_shipping_id')
    state = fields.Selection(string="Status",selection=[
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('upcoming', 'Upcoming Renewal'),
        ('pending', 'Pending Renewal'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
        ('terminated', 'Terminated'),
    ], default='draft', compute='_compute_state',store=True,tracking=1)

    history_count = fields.Integer(related='sale_id.history_count',store=True,tracking=1)

    name = fields.Char(
        string="Contract No",
        related='sale_id.name',
        store=True
    )

    start_date = fields.Date(
        string='Start Date',
        compute='_compute_contract_dates',
        store=True,
        readonly=False
    )

    end_date = fields.Date(
        string='End Date',
        compute='_compute_contract_dates',
        store=True,
        readonly=False
    )
    next_recurring_date = fields.Date(
        string='Next Recurring Date',
        compute='_compute_next_recurring_date',
        store=True
    )

    product_id = fields.Many2one(
        related='sale_id.order_line.product_id',
        string="Product",
        store=False
    )

    contract_line_ids = fields.One2many(
        'service.contract.line',
        'contract_id',
        string="Contract",
        tracking=2

    )
    sign_template_id =  fields.Many2one(comodel_name='sign.template',string='Sign Template',related='sale_id.sign_template_id')

    current_sign_id = fields.Many2one(
        'sign.request',
        string='Current Sign Request',
        compute='_compute_current_sign_id',
        store=True,tracking=1
    )
    current_subscription_id = fields.Many2one(
        comodel_name='sale.order',
        string="Current Subscription",
        compute="_compute_current_subscription_id",
        store=True, tracking=1
    )
    signed_document = fields.Binary(
        string="Signed Document",
        related='current_sign_id.completed_document',
        store=True
    )
    signed_document_filename = fields.Char(
        string="Signed Document",
        related='current_sign_id.reference',
        store=True
    )

    @api.depends('sale_id', 'sale_id.start_date', 'sale_id.next_recurring_date')
    def _compute_contract_dates(self):
        for rec in self:
            if rec.sale_id:
                rec.start_date = rec.sale_id.start_date
                rec.end_date = rec.sale_id.end_date
            else:
                rec.start_date = False
                rec.end_date = False

    @api.depends('contract_line_ids.state')
    def _compute_state(self):
        for rec in self:
            last_line = rec.contract_line_ids[-1] if rec.contract_line_ids else False
            if last_line:
                rec.state = last_line.state
            else:
                rec.state = 'terminated'

    @api.depends('sale_id.subscription_customer_assets_ids')
    def _compute_asset_ids(self):
        for rec in self:
            rec.asset_ids = [(6, 0, rec.sale_id.subscription_customer_assets_ids.ids)]

    @api.depends('contract_line_ids.sign_request_id')
    def _compute_current_sign_id(self):
        for contract in self:
            lines = contract.contract_line_ids.filtered('sign_request_id')
            contract.current_sign_id = lines[-1].sign_request_id if lines else False
    @api.depends('contract_line_ids.sale_id')
    def _compute_current_subscription_id(self):
        for rec in self:
            lines = rec.contract_line_ids.filtered('sale_id')
            rec.current_subscription_id = lines[-1].sale_id if lines else False
    @api.depends(
        'contract_line_ids',
        'contract_line_ids.sale_id',
        'contract_line_ids.sale_id.next_recurring_date'
    )
    def _compute_next_recurring_date(self):
        for rec in self:
            lines = rec.contract_line_ids.filtered('sale_id').sorted('id')

            rec.next_recurring_date = (
                lines[-1].sale_id.next_recurring_date
                if lines else False
            )

    def open_subscription_history(self):
        self.ensure_one()
        return self.sale_id.open_subscription_history()

    def open_sign_request(self):
        self.ensure_one()
        return {
            'name':"Sign Request",
            'type':'ir.actions.act_window',
            'res_model':'sign.request',
            'view_mode':'form',
            'res_id':self.current_sign_id.id,
            'target':'current'
        }

    def open_current_subscription(self):
        self.ensure_one()
        return {
            'name': "Subscription",
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.current_subscription_id.id,
            'target': 'current'
        }

    def create_sign_request(self):
        self.ensure_one()
        if self.current_subscription_id.state != 'sale':
            raise ValidationError(
                _("Please confirm the Subscription before creating a sign request.")
            )
        return {
            'name': 'Assign Sign Role',
            'type': 'ir.actions.act_window',
            'res_model': 'send.contract.sign',
            'view_mode': 'form',
            'context': {
                'template_id': self.sign_template_id.id,
                'default_contract_id': self.id,
                'default_order_id': self.sale_id.id,
            },
            'target': 'new'
        }

    def send_sign_email(self):
        self.ensure_one()
        if self.current_subscription_id.state != 'sale':
            raise ValidationError(
                _("Please confirm the Subscription before creating a sign request mail.")
            )

        recipients = []
        for item in self.current_sign_id.request_item_ids:
            if item.state not in ['completed','canceled']:
                item.send_signature_accesses()
            partner = item.partner_id.name or ''
            role = item.role_id.name or ''
            recipients.append(f"{partner} ({role})")
        recipient_text = ", ".join(recipients)
        body = Markup(
            f"<b>Signature Request Sent</b><br/>"
            "<ul>"
            f"<li><b>Recipients:</b> {recipient_text}</li>"
            f"<li><b>Document:</b> {self.current_sign_id.reference}</li>"
            f"<li><b>Status:</b> {self.current_sign_id.state}</li>"
            "</ul>"
        )
        if self.current_sign_id.state == 'signed':
            body = f'Signed Document Resent to the Recipients: {recipient_text}'
            self.current_sign_id._send_completed_document()


        self.message_post(body=body)
        return {'type': 'ir.actions.client', 'tag': 'soft_reload'}

    def share_sign_link(self):
        self.ensure_one()

        return {
            'name': 'Share Sign Link',
            'type': 'ir.actions.act_window',
            'res_model': 'share.sign.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': self.name,
                'default_sign_request_id': self.current_sign_id.id,
                'default_service_contract_id': self.id,
            }
        }


class ServiceContractLine(models.Model):
    _name = 'service.contract.line'
    _description = 'Service Contract line'

    name = fields.Char(string="Name",compute="_compute_name")
    sale_id = fields.Many2one('sale.order', string="Sale Order", required=True, ondelete='cascade',store=True)
    contract_id = fields.Many2one(
        'service.contract',
        string='Service Contract',
        ondelete='cascade',
        required=True
    )

    start_date = fields.Date(
        string='Contract Start Date',
        compute='_compute_contract_dates',
        store=True,
        readonly=False
    )

    end_date = fields.Date(
        string='Contract End Date',
        compute='_compute_contract_dates',
        store=True,
        readonly=False
    )


    crm_task_id = fields.Many2one(
        'project.task',
        string='CRM / Project Task'
    )

    sign_request_id = fields.Many2one(
        'sign.request',
        string='Sign Request',store=True
    )
    sign_status = fields.Selection(selection=[('not_shared','Not Shared'),('shared','Shared'),('sent','To Sign'),('signed','Fully Signed'),('canceled','Canceled'),('expired','Expired')], string="Sign Status",store=True,compute='_compute_sign_state')
    signed_document = fields.Binary(string="Signed Document",related='sign_request_id.completed_document',store=True)
    signed_document_filename = fields.Char(string="Signed Document",related='sign_request_id.reference',store=True)

    state = fields.Selection(string="Status",selection=[
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('upcoming', 'Upcoming Renewal'),
        ('pending', 'Pending Renewal'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
        ('terminated', 'Terminated'),
    ], default='draft', compute='_compute_state',store=True)

    is_complete = fields.Boolean(default=False)


    @api.depends(
        'sale_id.subscription_state',
        'sale_id.lead_id.stage_id.is_won',
        'end_date','sign_request_id.state'
    )
    def _compute_state(self):
        today = fields.Date.today()

        for rec in self:
            rec.state = 'terminated'
            if not rec.sale_id:
                continue
            sub_state = rec.sale_id.subscription_state
            end_date = rec.end_date

            if sub_state == '5_renewed':
                rec.state = 'done'
            elif rec.contract_id.sale_id == rec.sale_id and not rec.sign_request_id:
                rec.state = 'draft'
            elif rec.sign_request_id and rec.sign_request_id.state == 'signed':
                rec.state = 'active'
            elif rec.sign_request_id and rec.sign_request_id.state != 'signed':
                rec.state = 'pending'
            elif end_date and end_date <= (today + relativedelta(months=1)):
                rec.state = 'upcoming'
            elif sub_state in ('1_draft', '2_renewal'):
                rec.state = 'draft'
            elif sub_state == '6_churn':
                rec.state = 'cancelled'
            else:
                rec.state = 'terminated'

    @api.depends('sign_request_id.state')
    def _compute_sign_state(self):
        for rec in self:
            if rec.sign_request_id:
                rec.sign_status = rec.sign_request_id.state
                if rec.sign_request_id.state == 'signed':
                    body = Markup(
                        "<b>Document Signed</b><br/>"
                        "<ul>"
                        f"<li><b>Customer:</b> {rec.sale_id.partner_id.name}</li>"
                        f"<li><b>Contract:</b> {rec.contract_id.name}</li>"
                        f"<li><b>Contract Line:</b> {rec.name}</li>"
                        f"<li><b>Document:</b> {rec.sign_request_id.reference}</li>"
                        f"<li><b>Status:</b> Signed</li>"
                        "</ul>"
                    )
                    rec.contract_id.message_post(body=body)
            else:
                rec.sign_status = 'not_shared'


    @api.depends('sale_id.start_date','sale_id.next_recurring_date')
    def _compute_contract_dates(self):
        for rec in self:
            if rec.sale_id:
                rec.start_date = rec.sale_id.start_date
                rec.end_date = rec.sale_id.next_recurring_date
            else:
                rec.start_date = False
                rec.end_date = False

    @api.depends('sale_id')
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.sale_id.name} - Service Contract"

    def create_service_contract_lognote(self):
        for rec in self:
            contract = self.contract_id
            message = Markup(
                "<b>New Service Contract Created</b><br/>"
                "<ul>"
                f"<li><b>Customer:</b> {rec.sale_id.partner_id.name}</li>"
                f"<li><b>Subscription Order:</b> {rec.sale_id.name}</li>"
                f"<li><b>Contract:</b> {contract.name}</li>"
                f"<li><b>Contract Line:</b> {rec.name}</li>"
                f"<li><b>Start Date:</b> {rec.start_date or ''}</li>"
                f"<li><b>End Date:</b> {rec.end_date or ''}</li>"
                "</ul>"
            )

            if contract:
                contract.message_post(
                    body=message,
                    subtype_xmlid="mail.mt_note"
                )

            if rec.sale_id:
                rec.sale_id.message_post(
                    body=message,
                    subtype_xmlid="mail.mt_note"
                )

    def create_sign_request_lognote(self,sign_request):
        for rec in self:

            contract = rec.contract_id
            message = Markup(
                "<b>Signature Request Created</b><br/>"
                "<ul>"
                f"<li><b>Customer:</b> {rec.sale_id.partner_id.name}</li>"
                f"<li><b>Subscription Order:</b> {rec.sale_id.name}</li>"
                f"<li><b>Contract:</b> {contract.name}</li>"
                f"<li><b>Contract Line:</b> {rec.name}</li>"
                f"<li><b>Document Reference:</b> {sign_request.reference}</li>"
                "</ul>"
            )
            if contract:
                contract.message_post(
                    body=message,
                    subtype_xmlid="mail.mt_note"
                )

            if rec.sale_id:
                rec.sale_id.message_post(
                    body=message,
                    subtype_xmlid="mail.mt_note"
                )

    def create_sign_request(self,signers):
        self.ensure_one()

        contract = self.contract_id
        template = contract.sign_template_id
        if self.sign_request_id:
            return self.sign_request_id
        if not template or not self.sale_id.state == 'sale':
            raise ValidationError(
                _("Please confirm the Subscription before creating a sign request.")
            )

        sign_request = self.env['sign.request'].with_context(
            no_sign_mail=True,
            auto_fills=self.get_auto_fills()
        ).create({
            'template_id': template.id,
            'reference': f"{self.sale_id.name} - {self.sale_id.start_date} - Service Contract",
            'request_item_ids': [Command.create({
                'partner_id': signer['partner_id'],
                'role_id': signer['role_id'],
            }) for signer in signers],
        })
        self.create_sign_request_lognote(sign_request)

        self.sign_request_id = sign_request.id
        self.send_non_customer_emails()
        return sign_request

    def get_auto_fills(self):
        self.ensure_one()

        equipment_list = '\n'.join(
            [f"{i + 1}. {name}" for i, name in enumerate(self.contract_id.asset_ids.mapped('display_name'))]
        )
        partner = self.contract_id.partner_id
        address_parts = []

        if partner.parent_id:
            address_parts.append(partner.parent_id.name)

        street = ', '.join(filter(None, [
            partner.street,
            partner.street2,
        ]))

        if street:
            address_parts.append(street)

        city_line = ', '.join(filter(None, [
            partner.city,
            partner.state_id.name if partner.state_id else '',
            partner.zip,
        ]))

        if city_line:
            address_parts.append(city_line)

        if partner.country_id:
            address_parts.append(partner.country_id.name)

        address = '\n'.join(address_parts)

        return {
            'service_contract_no': self.name,
            'address': address,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'no_of_services': self.contract_id.product_id.number_of_services_per_year,
            'equipments': equipment_list,

            'user_name_job': (
                f"{self.sale_id.user_id.name}, "
                f"{self.sale_id.user_id.partner_id.function or ''}"
            ),

            'customer_name_job': (
                f"{self.contract_id.partner_id.name}, "
                f"{self.contract_id.partner_id.function or ''}"
            ),
        }

    def send_non_customer_emails(self):
        self.ensure_one()

        role_customer_id = self.env['ir.model.data']._xmlid_to_res_id(
            'sign.sign_item_role_customer'
        )

        for item in self.sign_request_id.request_item_ids:
            if item.state not in ['completed','canceled'] and item.role_id.id != role_customer_id:
                try:
                    item.send_signature_accesses()
                    body = f"Signature request sent to recipient: {item.partner_id.name}"
                    self.contract_id.message_post(
                        body=body,
                        subtype_xmlid="mail.mt_note"
                    )
                    self.sale_id.message_post(
                        body=body,
                        subtype_xmlid="mail.mt_note"
                    )
                except Exception as e:
                    _logger.exception(
                        "Failed to send signature access for item %s: %s",
                        item.id,
                        e
                    )



