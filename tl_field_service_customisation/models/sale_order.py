from datetime import timedelta
from odoo import models,fields,api
from odoo.fields import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from markupsafe import Markup
from odoo.tools.safe_eval import safe_eval

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    sale_id = fields.Many2one('sale.order', string='Subscription')
    contract_id = fields.Many2one(comodel_name='service.contract',compute='_compute_contract_id')

    @api.depends('sale_id')
    def _compute_contract_id(self):
        for rec in self:
            contract = self.sale_id.contract_id if self.sale_id.contract_id else self.sale_id.contract_line_id.contract_id if self.sale_id.contract_line_id else False
            rec.contract_id = contract.id if contract else False

    def action_view_contract(self):
        self.ensure_one()
        return {
            'name':'Annual Service Contract',
            'type':'ir.actions.act_window',
            'res_model':'service.contract',
            'view_mode':'form',
            'res_id':self.contract_id.id,
            'target':'current'
        }
    def action_view_subscription(self):
        self.ensure_one()
        return {
            'name':'Subscription',
            'type':'ir.actions.act_window',
            'res_model':'sale.order',
            'view_mode':'form',
            'res_id':self.sale_id.id,
            'target':'current'
        }

class SaleOrder(models.Model):
    _inherit = 'sale.order'


    available_shipping_ids = fields.Many2many(comodel_name='res.partner',compute='_compute_available_address_ids')
    available_invoice_ids = fields.Many2many(comodel_name='res.partner',compute='_compute_available_address_ids')

    contract_id = fields.Many2one(comodel_name='service.contract',string='Service Contract',compute="_compute_contract_id")
    contract_line_id = fields.Many2one(comodel_name='service.contract.line',string='Service Contract Line')

    sign_template_id =  fields.Many2one(comodel_name='sign.template',string='Sign Template')


    next_recurring_date = fields.Date(
        string='Next Recurring Date',
        compute='_compute_next_recurring_date',
        store=True
    )
    lead_id = fields.Many2one(
        'crm.lead',
        string='Renewal Opportunity',
        copy=False,
    )
    origin_lead_id = fields.Many2one(
        'crm.lead',
        string='Renewal Opportunity',
        copy=False,
    )


    @api.model_create_multi
    def create(self,val_list):
        res = super().create(val_list)
        self.assign_subscription_to_asset()
        for rec in res:
            if not rec.is_subscription:
                continue
            if not rec.origin_order_id:
                contract = self.env['service.contract'].create({
                    'sale_id': rec.id,
                })
                # rec.contract_id = contract.id
                line = self.env['service.contract.line'].create({
                    'sale_id': rec.id,
                    'contract_id': contract.id
                })
                rec.contract_line_id = line.id
            elif rec.origin_order_id:
                line = self.env['service.contract.line'].create({
                    'sale_id': rec.id,
                    'contract_id': rec.origin_order_id.contract_id.id
                })
                rec.contract_line_id = line.id
        return res

    def write(self,vals_list):

        res = super().write(vals_list)
        self.assign_subscription_to_asset()
        return res


    def assign_subscription_to_asset(self):
        for rec in self:
            order = rec
            if rec.origin_order_id:
                order = rec.origin_order_id
            for asset in rec.subscription_customer_assets_ids:
                asset.subscription_id = order.id

    @api.depends('partner_id')
    def _compute_available_address_ids(self):
        Partner = self.env['res.partner']

        for rec in self:
            partners = Partner.browse()
            delivery_partners = Partner.browse()
            invoice_partners = Partner.browse()

            if rec.partner_id:
                partners |= rec.partner_id

                if rec.partner_id.parent_id:
                    partners |= rec.partner_id.parent_id
                    delivery_partners |= rec.partner_id.parent_id.child_ids.filtered(lambda p: p.type == 'delivery')
                    invoice_partners |= rec.partner_id.parent_id.child_ids.filtered(lambda p: p.type == 'invoice')

                delivery_partners |= rec.partner_id.child_ids.filtered(lambda p:p.type == 'delivery')
                invoice_partners |= rec.partner_id.child_ids.filtered(lambda p:p.type == 'invoice')


                delivery_partners |= partners
                invoice_partners |= partners

            rec.available_shipping_ids = delivery_partners
            rec.available_invoice_ids = invoice_partners

    def prepare_renewal_order(self):
        self.ensure_one()

        if not self.contract_id or not self.contract_id.signed_document:
            raise UserError(
                "You cannot renew this subscription because the contract is not signed."
            )

        res = super().prepare_renewal_order()
        renew_order = self.browse(res.get('res_id')) if res.get('res_id') else False

        if renew_order:
            if self.subscription_customer_assets_ids:
                renew_order.subscription_customer_assets_ids = [
                    (6, 0, self.subscription_customer_assets_ids.ids)
                ]

            if self.sign_template_id:
                renew_order.sign_template_id = self.sign_template_id

        return res

    def action_confirm(self):
        res = super().action_confirm()
        self._create_fsm_tasks_for_year()
        return res

    def _create_fsm_tasks_for_year(self):
        """Create all FSM tasks for the subscription for the current year"""
        for rec in self:
            if not rec.is_subscription:
                continue
            created_tasks = []

            for line in rec.order_line:
                for asset in rec.subscription_customer_assets_ids:
                    num_services = int(line.product_template_id.number_of_services_per_year)
                    for service in range(num_services):
                        values = {
                            'sale_order_id': rec.id,
                            'sale_line_id': line.id,
                            'name': f"{rec.name} - {rec.partner_id.display_name} - {line.product_template_id.display_name} - {asset.name} - {datetime.now().year} - Service-{service + 1}",
                            'project_id': line.product_template_id.project_id.id,
                            'worksheet_template_id':line.product_template_id.worksheet_template_id.id if line.product_template_id.worksheet_template_id else False,
                            'partner_id': rec.partner_id.id,
                            'is_fsm': True,
                            'recurring_task': False,  # NO automatic recurrence
                            'planned_date_begin': datetime.now(),
                            'date_deadline': rec.end_date if rec.end_date else False,
                            'user_ids': [(4, rec.user_id.id)] if rec.user_id else [],
                            'customer_assets_ids': [(4, asset.id)],
                        }
                        task = self.env['project.task'].sudo().create(values)
                        created_tasks.append(task)

                        if line.task_id:
                            line.task_id.unlink()
            if created_tasks:
                rec.tasks_ids = [(4, t.id) for t in reversed(created_tasks)]


            if created_tasks:
                full_msg = Markup(
                    f"""
                    <b>FSM Tasks Created</b><br/>
                    <span>Tasks created for the year from subscription: <b>{rec.name}</b></span>
                    <br/><br/>
                    <b>Created Tasks:</b>
                    <ul>
                        {''.join(f"<li>{task.display_name}</li>" for task in created_tasks)}
                    </ul>
                    """
                )

                rec.message_post(
                    body=full_msg,
                    message_type="comment",
                    subtype_xmlid="mail.mt_note",
                )

    @api.depends('start_date', 'plan_id', 'plan_id.billing_period_unit')
    def _compute_next_recurring_date(self):
        for order in self:
            if not order.is_subscription or not order.start_date:
                order.next_recurring_date = False
                continue
            interval = 1
            unit = order.plan_id.billing_period_unit  # month / year

            current = order.start_date or order.date_order

            # Move forward until next date >= today
            if unit == 'month':
                current += relativedelta(months=interval)
            elif unit == 'year':
                current += relativedelta(years=interval)

            next_date = current
            order.next_recurring_date = next_date

    @api.depends('contract_line_id')
    def _compute_contract_id(self):
        for rec in self:
            rec.contract_id = rec.contract_line_id.contract_id.id if rec.contract_line_id else False

    def action_create_renewal_opportunity(self):
        """Create CRM Opportunity 1 month before recurring date"""
        team = self.env.ref(
            'tl_field_service_customisation.crm_team_service_contracts',
            raise_if_not_found=False
        )

        # Subscriptions to create opportunities for
        subscriptions = self.env['sale.order'].search([
            ('subscription_state', '=', '3_progress'),
            ('is_subscription', '=', True),
            ("next_recurring_date", ">=", datetime.now().strftime("%Y-%m-%d")),
            ("next_recurring_date", "<=",(datetime.now() + relativedelta(months = 1)).strftime("%Y-%m-%d")),
        ])
        for sub in subscriptions:
            if sub.lead_id:
                continue

            parent_contract = sub.contract_id
            parent_contract_desc = f'Contract No: {parent_contract.name}\n' if parent_contract else ''
            last_product = sub.order_line[-1].product_id if sub.order_line else False
            product_id = last_product.id if last_product else False
            lead = self.env['crm.lead'].create({
                'name': f'Service Contract Renewal - {sub.name}',
                'partner_id': sub.partner_id.id,
                'type': 'opportunity',
                'team_id': team.id if team else False,
                'user_id': sub.user_id.id or False,
                'products': product_id,
                'expected_revenue': sub.recurring_total or sub.amount_total,
                'description': (
                    f"{sub.name} Service Contract Renewal Details\n"
                    f"----------------------------------------\n"
                    f"Customer        : {sub.partner_id.name or ''}\n"
                    f"Subscription    : {sub.name}\n"
                    f"Renewal Date    : {sub.next_recurring_date or 'N/A'}\n"
                    f"Salesperson     : {sub.user_id.name or 'N/A'}\n"
                    f"Expected Revenue: {sub.recurring_total or sub.amount_total}\n"
                    f"\n"
                    f"Parent Contract\n"
                    f"----------------------------------------\n"
                    f"{'Contract No: ' + sub.contract_id.name if sub.contract_id else 'N/A'}"
                ),
                'sale_id': sub.id,
            })
            sub.write({
                'lead_id':lead.id
            })

    def action_view_renewal_opportunity(self):
        self.ensure_one()
        return {
            'name':'Renewal Opportunity',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'res_id': self.lead_id.id,
            'target': 'current'
        }

    def action_view_service_contract(self):
        self.ensure_one()
        return {
            'name': 'Annual Service Contract',
            'type': 'ir.actions.act_window',
            'res_model': 'service.contract',
            'view_mode': 'form',
            'res_id': self.contract_id.id,
            'target': 'current'
        }

    def action_assign_sign_role(self):
        return {
            'name': 'Assign Sign Role',
            'type': 'ir.actions.act_window',
            'res_model': 'send.contract.sign',
            'view_mode': 'form',
            'context': {
                'template_id': self.sign_template_id.id,
                'default_order_id': self.id,
            },
            'target': 'new'
        }

    def send_sign_request_autofill(self):
        self.ensure_one()

        return self.sign_template_id.send_sign_request_autofill(

        )


