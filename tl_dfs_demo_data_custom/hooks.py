import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Run the custom-model loader now that every custom model exists, and tidy sales teams."""
    env['tl.dfs.demo.loader'].action_load_custom_data()

    # Merge the demo "Service & Contracts" team into the team used by contract renewals.
    contract_team = env.ref('tl_field_service_customisation.crm_team_service_contracts', raise_if_not_found=False)
    demo_team = env.ref('tl_dfs_demo_data.crm_team_service', raise_if_not_found=False)
    if contract_team and demo_team and demo_team.active:
        contract_team.write({
            'user_id': demo_team.user_id.id or contract_team.user_id.id,
            'member_ids': [(4, user.id) for user in demo_team.member_ids],
        })
        for model in ('crm.lead', 'sale.order'):
            env[model].with_context(active_test=False).search([('team_id', '=', demo_team.id)]).write({'team_id': contract_team.id})
        demo_team.action_archive()

    # Route website traffic to "Website Enquiries" and retire the empty default website team.
    website_team = env.ref('tl_dfs_demo_data.crm_team_website', raise_if_not_found=False)
    default_team = env.ref('sales_team.salesteam_website_sales', raise_if_not_found=False)
    if website_team:
        env['website'].search([]).write({'salesteam_id': website_team.id, 'crm_default_team_id': website_team.id})
        if default_team and default_team.active and not default_team.member_ids:
            env['sale.order'].with_context(active_test=False).search([('team_id', '=', default_team.id)]).write({'team_id': website_team.id})
            default_team.action_archive()
    # Contracts only exist now, so link the Service Agreement template after loading them.
    env['tl.dfs.demo.loader']._setup_contract_sign_template()
    _logger.info('tl_dfs_demo_data_custom: custom demo data loaded and sales teams tidied')
