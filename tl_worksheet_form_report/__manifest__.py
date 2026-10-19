{
    'name': 'FSM Worksheet Form Report',
    'summary': 'Generate styled worksheet reports for Field Service interventions',
    'description': """
Render Field Service (planning.slot) worksheets with the CGUK report layout
and print them in PDF documents.
    """,
    'author': 'Thoughtlogik',
    'website': 'https://www.thoughtlogik.com',
    'category': 'Services/Field Service',
    'version': '20.0.1.0.0',
    'depends': [
        'planning_field_service',
        'planning_field_service_worksheet',
    ],
    'data': [
        'views/custom_fsm_layout.xml',
        'views/worksheet_custom_report_templates.xml',
        'views/external_layout_bold.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
