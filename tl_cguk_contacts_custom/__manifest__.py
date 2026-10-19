# -*- coding: utf-8 -*-
{
    'name': 'TL_CGUK_Contacts',
    'version': '20.0.1.3.0',
    'summary': 'Create a contact field',
    'author': 'Thoughtlogik Solutions',
    'website': 'www.thoughtlogik.com',
    "license": "LGPL-3",
    'depends': ['base','contacts' ],
    'data': [
        'security/ir.access.csv',
        'views/custom_contact_views.xml',
        'views/equipment_type_views.xml',

    ],

    'installable': True,
    'auto_install': False,
    'application': True,

}