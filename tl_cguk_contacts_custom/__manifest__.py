# -*- coding: utf-8 -*-
{
    'name': 'TL_CGUK_Contacts',
    'version': '1.3',
    'summary': 'Create a contact field',
    'author': 'Thoughtlogik Solutions',
    'website': 'www.thoughtlogik.com',
    'depends': ['contacts' ],

    'data': [
        'security/ir.model.access.csv',
        'views/custom_contact_views.xml',
        'views/equipment_type_views.xml',

    ],

    'installable': True,
    'auto_install': False,
    'application': True,

}