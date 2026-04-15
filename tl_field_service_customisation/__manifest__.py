{
    "name": "TL Field Service Customisation",
    "version": "1.0",
    "depends": ['cguk_customer_asset','sign','crm','sale_subscription','tl_cguk_crm_custom','industry_fsm_report','stock','industry_fsm_sale','product'],
    'author': 'Thoughtlogik Solutions',
    'website': 'www.thoughtlogik.com',
    "category": "custom",
    "summary": "Custom module for Task and project management",
    "data": [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/service_contract_views.xml',
        'views/warehouse_product_and_fsm.xml',
        'data/data.xml',
        'wizard/share_sign_wizard.xml',
    ],
    "assets":{
      'web.assets_backend':[

      ]
    },
    "installable": True,
    "application": True
}
