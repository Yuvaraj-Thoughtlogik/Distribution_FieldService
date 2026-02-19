{
    "name": "TL Field Service Customisation",
    "version": "1.0",
    "depends": ['cguk_customer_asset','sign','crm','sale_subscription'],
    'author': 'Thoughtlogik Solutions',
    'website': 'www.thoughtlogik.com',
    "category": "custom",
    "summary": "Custom module for Task and project management",
    "data": [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/service_contract_views.xml',
        'data/data.xml',
    ],
    "assets":{
      'web.assets_backend':[

      ]
    },
    "installable": True,
    "application": True
}
