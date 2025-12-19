from odoo import fields, models, _
from odoo.tools import SQL


class AccountTaxReportHandler(models.AbstractModel):
    _inherit = 'account.tax.report.handler'

    def _get_vat_closing_entry_additional_domain(self):
        uk_country_id = self.env.ref('base.uk').id
        tag_cisst = self.env['account.account.tag']._get_tax_tags('CISST', uk_country_id)
        tag_cispt = self.env['account.account.tag']._get_tax_tags('CISPT', uk_country_id)
        tags = tag_cisst + tag_cispt

        # EXTENDS account_reports
        domain = super()._get_vat_closing_entry_additional_domain()
        domain += [
            ('tax_tag_ids', 'not in', tags.ids),
        ]
        return domain


class BritishFPSTaxReportCustomHandler(models.AbstractModel):
    _name = 'fps.tax.report.handler'
    _inherit = 'account.tax.report.handler'
    _description = 'British Tax Report Custom Handler'

    def _custom_options_initializer(self, report, options, previous_options=None):
        super()._custom_options_initializer(report, options, previous_options)
        options['ignore_totals_below_sections'] = True

        options['buttons'] = [button for button in options['buttons'] if button['action'] != 'action_periodic_paye_entries']
        options['buttons'].append({'name': _("Send to HMRC"), 'sequence': 40, 'action': 'action_open_monthly_return_wizard'})
        options['buttons'].append({'name': _("Refresh HMRC request"), 'sequence': 40, 'action': 'action_refresh_hmrc_request'})

        # We want to only allow moves that has cis taxes in it as they are the only relevent moves for this report
        tax_cisp0 = self.env.ref(f'account.{self.env.company.id}_CISP0', raise_if_not_found=False)
        tax_cisp20 = self.env.ref(f'account.{self.env.company.id}_CISP20', raise_if_not_found=False)
        tax_cisp30 = self.env.ref(f'account.{self.env.company.id}_CISP30', raise_if_not_found=False)
        tax_ciss0 = self.env.ref(f'account.{self.env.company.id}_CISS0', raise_if_not_found=False)
        tax_ciss20 = self.env.ref(f'account.{self.env.company.id}_CISS20', raise_if_not_found=False)
        tax_ciss30 = self.env.ref(f'account.{self.env.company.id}_CISS30', raise_if_not_found=False)

        if not all([tax_ciss0, tax_ciss20, tax_ciss30, tax_cisp0, tax_cisp20, tax_cisp30]):
            options['forced_domain'] = [(0, '=', 1)]
        else:
            tax_cis = tax_ciss0 + tax_ciss20 + tax_ciss30 + tax_cisp0 + tax_cisp20 + tax_cisp30
            options['forced_domain'] = [*options.get('forced_domain', []), ('move_id.line_ids.tax_ids', 'in', tax_cis.ids)]

    def _customize_warnings(self, report, options, all_column_groups_expression_totals, warnings):
        queries = []
        for column_group in all_column_groups_expression_totals:
            column_group_options = report._get_column_group_options(options, column_group)
            queries.append(
                SQL(
                    """
                    SELECT
                    COALESCE(
                        ARRAY_AGG(DISTINCT move.partner_id),
                        '{}'
                    ) AS unregistered_partners
                    FROM account_move move
                    WHERE move.l10n_uk_cis_use_inactivated_cis_partner = TRUE
                    AND move.date >= %(period_start)s
                    AND move.date <= %(period_end)s
                    """,
                    period_start=fields.Date.from_string(column_group_options['date']['date_from']),
                    period_end=fields.Date.from_string(column_group_options['date']['date_to']),
                )
            )

        self._cr.execute(SQL(" UNION ALL ").join(queries))
        result = self._cr.dictfetchall()
        unregistered_partners = list({
            id for column_group_result in result
            for id in column_group_result['unregistered_partners']
        })

        if unregistered_partners:
            warnings['l10n_uk_cis.warning_cis_unregistered_partner'] = {
                'partner_ids': unregistered_partners,
                'alert_type': 'warning'
            }

    def action_open_paye_fps_return_wizard(self, options):
        context = self.env.context.copy()
        context.update({'options': options})
        return {
            'type': 'ir.actions.act_window',
            'name': _("FPS return"),
            'view_mode': 'form',
            'res_model': 'paye_fps_return_wizard',
            'target': 'new',
            'context': context,
            'views': [[False, 'form']],
        }

    def action_refresh_hmrc_request(self, options):
        self.env.ref('l10n_uk_hmrc.ir_cron_l10n_uk_cis_process_transactions')._trigger()
        return {'type': 'ir.actions.act_window_close'}

    def action_open_partners_view_with_unregistered_cis(self, options, params=None):
        partner_ids = params.get('partner_ids')
        partners = self.env['res.partner'].browse(partner_ids)
        name = _("Unregistered partners") if len(partners) > 1 else _("Unregistered partner")
        return partners._get_records_action(name=name)
