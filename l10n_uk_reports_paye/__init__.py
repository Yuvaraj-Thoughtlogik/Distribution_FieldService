from . import models
from . import tests
from . import tools



#def _l10n_uk_paye_post_init(env):
#    paye_eps_report = env.ref('l10n_uk_paye.tax_report_paye_eps')
#    for company in env['res.company'].search([('chart_template', '=', 'uk')]):
#        ChartTemplate = env['account.chart.template'].with_company(company)
#        ChartTemplate._load_data({
#            'account.account': ChartTemplate._get_uk_account_account(),
#            'account.tax': ChartTemplate._get_uk_account_tax(),
#            'account.tax.group': ChartTemplate._get_uk_account_tax_group(),
#        })
#        # Replace the start date for the paye EPS report
#        paye_eps_report.with_company(company).tax_closing_start_date = paye_eps_report.with_company(company).tax_closing_start_date.replace(day=6)
