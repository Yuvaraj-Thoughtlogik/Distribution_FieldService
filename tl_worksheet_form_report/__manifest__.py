# -*- coding: utf-8 -*-
{
    'name': 'FSM Worksheet Form Report',
    'summary': 'Generate worksheet reports from FSM form views',

    'description': """
Convert FSM worksheet form views into HTML reports
and print them in PDF documents.
    """,

    'author': 'Thoughtlogik',
    'website': 'https://www.thoughtlogik.com',

    'category': 'Services/Field Service',
    'version': '18.0.1.0.0',

    'depends': [
        'project','industry_fsm','industry_fsm_report',
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