{
    "name": "TL_CGUK_Customer_Assets",
    "version": "1.0",
    "depends": ["base","sale", "contacts", "product","helpdesk","project","sale_subscription","stock"],
    'author': 'Thoughtlogik Solutions',
    'website': 'www.thoughtlogik.com',
    "category": "custom",
    "summary": "Custom module for Track sold equipment per customer",
    "data": [
        "security/ir.model.access.csv",
        # 'data/sequence.xml',
        "views/customer_asset_views.xml",
        "views/sale_order_views.xml",
        "views/smart_buttons.xml",
    ],
    "assets":{
      'web.assets_backend':[
          "cguk_customer_asset/static/css/style.css",
      ]
    },
    "installable": True,
    "application": True
}
