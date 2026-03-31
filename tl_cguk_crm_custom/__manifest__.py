{
    'name': 'Crm and Contact customisation',
    'version': '1.1',
    'author': 'ThoughtLogik',
    'category': 'Custom',
    'summary': 'Custom module for Odoo',
    'depends': ['base','crm','product','calendar','mail','helpdesk','tl_cguk_contacts_custom'],
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