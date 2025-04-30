from odoo.api import Environment, SUPERUSER_ID

def post_init_hook(cr, registry):
    env = Environment(cr, SUPERUSER_ID, {})
    env['crm.lead'].search([])._recompute_store(['company_name'])
