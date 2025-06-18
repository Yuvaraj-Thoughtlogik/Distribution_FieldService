# -*- coding: utf-8 -*-
{
    'name': 'TL_CGUK_CRM',
    'version': '1.3',
    'summary': 'Create a crm custom field',
    'author': 'Thoughtlogik Solutions',
    'website': 'www.thoughtlogik.com',
    'depends': ['base','crm','product','calendar','mail','helpdesk'],
    'post_init_hook': 'hooks.post_init_hook',
    'data': [
        'security/ir.model.access.csv',
        'views/crm_contact_customisation.xml',
        'views/calendar_view.xml',
        'views/custom_activity.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
}
