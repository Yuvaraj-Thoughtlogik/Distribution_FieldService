{
    "name": "Customer Asset",
    "version": "1.0",
    "depends": ["sale", "contacts", "product","helpdesk","project"],
    "author": "Felix Hilbert",
    "category": "Sales",
    "summary": "Track sold equipment per customer",
    "data": [
        "security/ir.model.access.csv",
        'data/sequence.xml',
        "views/customer_asset_views.xml",
        "views/sale_order_views.xml"
    ],
    "assets":{
      'web.assets_backend':[
          "cguk_customer_asset/static/css/style.css",
      ]
    },
    "installable": True,
    "application": False
}
