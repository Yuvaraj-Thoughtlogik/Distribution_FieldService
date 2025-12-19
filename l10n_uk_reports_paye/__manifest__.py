{
    'name': 'UK - HMRC PAYE RTI',
    'countries': ['gb'],
    'author': 'Augur Solutions Ltd',
    'category': 'Accounting/Localizations/UK/PAYE',
    'depends': ['l10n_uk_hmrc', 'l10n_uk_reports','l10n_uk_hr_payroll'],
    'website': 'https://www.auguraccountants.com/odoo-uk-payroll',
    'summary': 'UK HMRC RTI PAYE Gateway for UK Payroll',
    'currency': 'EUR',
    'price': '129.99',
    'support': 'payroll@auguraccountants.com',
    'version': '18.0.1.1',
    'description': """
    PAYE HMRC RTI Scheme for United Kingdom
    ================================================
    """,
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'data/mail_template_data.xml',
#        'views/account_move_views.xml',
        'views/template_paye_fps_return_body.xml',
        'views/template_paye_eps_return_body.xml',
        'views/template_transaction_engine_base.xml',
        'views/ir_ui_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'l10n_uk_reports_paye/static/src/components/**/*',
        ],
    },
    'license': 'OPL-1',
    'installable': True,
    #    'post_init_hook': '_l10n_uk_paye_post_init',
}
