def post_init_hook(env):
    # company_name is a non-stored computed field: nothing to recompute in DB.
    # Kept for compatibility (Odoo 17+ hook signature: post_init_hook(env)).
    env['crm.lead'].search([]).invalidate_recordset(['company_name'])
