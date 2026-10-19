{
    'name': 'FSM Multi Worksheet',
    'version': '20.0.1.0.0',
    'category': 'Services/Field Service',
    'summary': 'Manage multiple worksheets per Field Service intervention',
    'description': """
FSM Multi Worksheet
===================
Allows multiple worksheets (one per worksheet template / customer asset) to be
filled for a single Field Service intervention (planning.slot).
    """,
    'author': 'Thoughtlogik Technology Solutions',
    'website': 'https://www.thoughtlogik.com',
    'license': 'LGPL-3',
    'depends': [
        'planning_field_service_worksheet',
        'cguk_customer_asset',
        'tl_worksheet_form_report',
    ],
    'data': [
        'security/ir.access.csv',
        'views/worksheet_template_views.xml',
        'views/planning_slot_worksheet_views.xml',
        'views/planning_slot_form.xml',
        'views/worksheet_custom_report_templates.xml',
        'views/planning_slot_portal_templates.xml',
    ],
    'installable': True,
    'application': False,
}
