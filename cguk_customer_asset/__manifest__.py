{
    "name": "TL_CGUK_Customer_Assets",
    "version": "20.0.1.2.0",
    "depends": [
        "contacts",
        "product",
        "sale_management",
        "sale_subscription",
        "stock",
        "repair",
        "helpdesk",
        # Field Service (Odoo 20: interventions are planning.slot records)
        "planning_field_service",
        "planning_field_service_sale_timesheet",
        "helpdesk_planning_field_service",
    ],
    'author': 'Thoughtlogik Solutions',
    'website': 'www.thoughtlogik.com',
    "category": "custom",
    "license": "LGPL-3",
    "summary": "Custom module for Track sold equipment per customer",
    "data": [
        "security/ir.access.csv",
        "views/customer_asset_views.xml",
        "views/sale_order_views.xml",
        "views/smart_buttons.xml",
        "views/product_template_views.xml",
        "views/repair.xml",
        "views/res_partner.xml",
        'views/reports.xml',
        'views/helpdesk_ticket_views.xml',
        'views/planning_slot_views.xml',
    ],
    "assets": {
        'web.assets_backend': [
            "cguk_customer_asset/static/css/style.css",
        ]
    },
    "installable": True,
    "application": True,
}
