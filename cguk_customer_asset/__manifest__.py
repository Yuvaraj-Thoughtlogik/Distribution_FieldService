{
    "name": "TL_CGUK_Customer_Assets",
    "version": "1.0",
    "depends": ["base","sale", "contacts", "product","helpdesk_fsm","project","sale_subscription","stock"],
    'author': 'Thoughtlogik Solutions',
    'website': 'www.thoughtlogik.com',
    "category": "custom",
    "summary": "Custom module for Track sold equipment per customer",
    "data": [
        "security/ir.model.access.csv",
        "views/customer_asset_views.xml",
        "views/sale_order_views.xml",
        "views/smart_buttons.xml",
        "views/product_template_views.xml",
        "views/repair.xml",
        'wizard/lot_selection.xml'
    ],
    "assets":{
      'web.assets_backend':[
          "cguk_customer_asset/static/css/style.css",
          "cguk_customer_asset/static/src/js/lot_wizard.js",
      ]
    },
    "installable": True,
    "application": True
}
