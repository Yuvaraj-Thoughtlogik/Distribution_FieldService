{
    'name': 'Tl_report_custom',
    'version': '1.0',
    'author': 'Felix',
    'category': 'Custom',
    'summary': 'Custom Reports for Inventory',
    "license": "LGPL-3",
    'depends': ['stock','sale'],
    'data': [
        'report/report_stockpicking_operations_inherit.xml',
        'views/sale_order_view.xml'
    ],
    'assets':{
        'web.assets_backend':[
            'tl_report_custom/static/src/css/style.css',
        ]
    },
    'installable': True,
    'application': True,
}