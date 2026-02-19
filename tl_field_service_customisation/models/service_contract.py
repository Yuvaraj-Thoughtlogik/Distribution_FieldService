from dateutil.relativedelta import relativedelta
from odoo import models,fields,api

class ServiceContract(models.Model):
    _name = 'service.contract'
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
    ], default='draft', compute='_compute_state')

    history_count = fields.Integer(related='sale_id.history_count')

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
        string="Contract"
    )
    sign_template_id =  fields.Many2one(comodel_name='sign.template',string='Sign Template',related='sale_id.sign_template_id')

    current_sign_id = fields.Many2one(
        'sign.request',
        string='Current Sign Request',
        compute='_compute_current_sign_id',
        store=True
    )
    current_subscription_id = fields.Many2one(comodel_name='sale.order',string="Current Subscription",compute="_compute_current_subscription_id")
    signed_document = fields.Binary(string="Signed Document", related='current_sign_id.completed_document')
    signed_document_filename = fields.Char(string="Signed Document", related='current_sign_id.reference')

    @api.depends('sale_id', 'sale_id.start_date', 'sale_id.next_recurring_date')
    def _compute_contract_dates(self):
        for rec in self:
            if rec.sale_id:
                rec.start_date = rec.sale_id.start_date
                rec.end_date = rec.sale_id.end_date
            else:
                rec.start_date = False
                rec.end_date = False

    @api.depends('sale_id.state')
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

    def send_sign_request(self):
        self.ensure_one()


class ServiceContractLine(models.Model):
    _name = 'service.contract.line'
    _description = 'Service Contract line'

    name = fields.Char(string="Name",compute="_compute_name")
    sale_id = fields.Many2one('sale.order', string="Sale Order", required=True, ondelete='cascade')
    contract_id = fields.Many2one(
        'service.contract',
        string='Service Contract',
        ondelete='cascade',
        required=True
    )

    start_date = fields.Date(
        string='Contract Start Date',
        compute='_compute_contract_dates',
    )

    end_date = fields.Date(
        string='Contract End Date',
        compute='_compute_contract_dates',
    )


    crm_task_id = fields.Many2one(
        'project.task',
        string='CRM / Project Task'
    )

    sign_request_id = fields.Many2one(
        'sign.request',
        string='Sign Request'
    )
    sign_status = fields.Selection(related='sign_request_id.state',string="Sign Status")
    signed_document = fields.Binary(string="Signed Document",related='sign_request_id.completed_document')
    signed_document_filename = fields.Char(string="Signed Document",related='sign_request_id.reference')

    state = fields.Selection(string="Status",selection=[
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('upcoming', 'Upcoming Renewal'),
        ('pending', 'Pending Renewal'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
        ('terminated', 'Terminated'),
    ], default='draft', compute='_compute_state')

    is_complete = fields.Boolean(default=False)



    def create_sign_request(self):
        for line in self:

            contract = line.contract_id
            template = contract.sign_template_id
            if line.sign_request_id:
                continue
            if not template or not line.sale_id.state == 'sale':
                continue

            request_items = []

            roles = template.sign_item_ids.mapped('responsible_id')

            for role in roles:
                request_items.append((0, 0, {
                    'partner_id': line.sale_id.partner_id.id,
                    'role_id': role.id,
                }))

            sign_request = self.env['sign.request'].create({
                'template_id': template.id,
                'reference': f"{line.sale_id.name} - {line.sale_id.start_date} - Service Contract",
                'request_item_ids': request_items,
            })

            line.sign_request_id = sign_request.id

    @api.depends(
        'sale_id.subscription_state',
        'sale_id.lead_id.stage_id.is_won',
        'end_date',
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
