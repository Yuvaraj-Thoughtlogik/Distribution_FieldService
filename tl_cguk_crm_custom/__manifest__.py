{
    'name': 'Crm and Contact customisation',
    'version': '1.1',
    'author': 'Felix',
    'category': 'Custom',
    'summary': 'Custom module for Odoo',
    'depends': ['base','crm','product','calendar'],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_contact_customisation.xml',
        'views/calendar_view.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
}