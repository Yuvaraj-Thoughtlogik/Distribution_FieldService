{
    'name': 'FSM Multi Worksheet',
    'version': '18.0.1.0.0',
    'category': 'Field Service',
    'summary': 'Manage multiple worksheets in Field Service',
    'description': """
FSM Multi Worksheet
===================
Allows multiple worksheets to be created and managed for Field Service tasks.
    """,
    'author': 'Thoughtlogik Technology Solutions',
    'website': 'https://www.thoughtlogik.com',
    'license': 'LGPL-3',
    'depends': [
        'industry_fsm',
        'industry_fsm_report',
        'cguk_customer_asset',
        'tl_worksheet_form_report',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/worksheet_template_views.xml',
        'views/project_task_form.xml',
        'views/project_task_worksheet_views.xml',
        'views/worksheet_custom_report_templates.xml',
        'views/project_portal_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tl_fsm_multi_worksheet/static/src/js/FsmWorksheetListRenderer.js',
        ],
    },
    'installable': True,
    'application': False,
}