{
    'name': 'Crm and Contact customisation',
    'version': '20.0.1.1.0',
    'author': 'ThoughtLogik',
    'category': 'Custom',
    'summary': 'Custom module for Odoo',
    'depends': ['base','crm','product','calendar','mail','helpdesk','tl_cguk_contacts_custom'],
    'data': [
        'security/ir.access.csv',
        'views/crm_contact_customisation.xml',
        'views/calendar_view.xml',
        'views/custom_activity.xml',
        'views/menu.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
}