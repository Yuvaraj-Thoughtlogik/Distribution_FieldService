from odoo import api, fields, models
from odoo.tools.float_utils import float_compare


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_uk_cis_use_wrong_cis_taxes = fields.Boolean(compute='_compute_l10n_uk_cis_use_wrong_cis_taxes')
    l10n_uk_cis_use_inactivated_cis_partner = fields.Boolean(compute='_compute_l10n_uk_cis_use_inactivated_cis_partner',
                                                             store=True)

    @api.model
    def _l10n_uk_cis_get_taxes_for_companies(self, companies):

        uk_country_id = self.env.ref('base.uk').id
        tag_cisst = self.env['account.account.tag']._get_tax_tags('CISST', uk_country_id)
        tag_cispt = self.env['account.account.tag']._get_tax_tags('CISPT', uk_country_id)
        tags = tag_cisst + tag_cispt

        taxes_grouped_company = self.env['account.tax'].search([
            ('invoice_repartition_line_ids.tag_ids', 'in', tags.ids),
            ('company_id', 'in', companies.ids)
        ])

        return taxes_grouped_company

    @api.model
    def _l10n_uk_cis_get_taxes_groups_by_companies(self, companies):
        cis_taxes_for_companies = self._l10n_uk_cis_get_taxes_for_companies(companies)

        tax_groups_grouped_company = self.env['account.tax.group'].search([
            ('id', 'in', cis_taxes_for_companies.tax_group_id.ids),
            ('company_id', 'in', companies.ids)
        ]).grouped('company_id')

        return tax_groups_grouped_company

    @api.depends('partner_id', 'invoice_line_ids.tax_ids', 'partner_id.l10n_uk_cis_deduction_rate',
                 'l10n_uk_cis_use_inactivated_cis_partner')
    def _compute_l10n_uk_cis_use_wrong_cis_taxes(self):
        cis_taxes_by_company = self._l10n_uk_cis_get_taxes_for_companies(self.company_id).grouped('company_id')

        for move in self:
            if move.move_type in ('out_invoice', 'out_refund') or move.company_id not in cis_taxes_by_company:
                move.l10n_uk_cis_use_wrong_cis_taxes = False
                continue
            if move.l10n_uk_cis_use_inactivated_cis_partner:
                move.l10n_uk_cis_use_wrong_cis_taxes = True
                continue

            partner_invalid_taxes = cis_taxes_by_company[move.company_id].filtered(
                lambda tax: self.partner_id and float_compare(tax.amount,
                                                              self.partner_id.commercial_partner_id._get_deduction_amount_from_rate(),
                                                              precision_digits=0) != 0
            )
            move.l10n_uk_cis_use_wrong_cis_taxes = any(
                partner_invalid_tax.id in move.invoice_line_ids.tax_ids.ids for partner_invalid_tax in
                partner_invalid_taxes)

    @api.depends('partner_id', 'invoice_line_ids.tax_ids', 'partner_id.l10n_uk_cis_enable_construction_industry_scheme')
    def _compute_l10n_uk_cis_use_inactivated_cis_partner(self):
        cis_tax_group_by_company = self._l10n_uk_cis_get_taxes_groups_by_companies(self.company_id)

        for move in self:
            if move.company_id not in cis_tax_group_by_company or move.move_type in ('out_refund', 'out_invoice'):
                move.l10n_uk_cis_use_inactivated_cis_partner = False
                continue

            cis_enabled = move.partner_id.commercial_partner_id.l10n_uk_cis_enable_construction_industry_scheme
            use_cis_tax = any(tax_id.tax_group_id.id == cis_tax_group_by_company[move.company_id].id for tax_id in
                              move.invoice_line_ids.tax_ids)
            move.l10n_uk_cis_use_inactivated_cis_partner = not cis_enabled and use_cis_tax

    def action_open_partner_form(self):
        self.ensure_one()
        return {
            'view_mode': 'form',
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'res_id': self.partner_id.commercial_partner_id.id,
            'views': [(False, 'form')],
        }
