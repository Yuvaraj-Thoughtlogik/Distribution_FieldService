{
    "name": "DFS Website - B2B Request a Quote",
    "version": "20.0.1.0.0",
    "author": "ThoughtLogik",
    "category": "Website/Website",
    "summary": "Corporate lab-equipment website with a quote-only (price-less) eCommerce flow "
               "that creates CRM opportunities and draft quotations.",
    "description": """
Quote-only B2B website for a UK distributor of food-testing / laboratory
equipment and field service.

* Corporate look & feel (homepage, About, Services, Industries, Contact, Support)
* eCommerce without prices, payment or delivery: "Add to quote" + quote request form
* Submitting a request creates the customer, a CRM opportunity and a draft quotation
* Portal page "My quote requests"
""",
    "depends": [
        "website_sale",
        "website_crm",
        "sale_crm",
        "crm",
        "website_helpdesk",
        "portal",
    ],
    "data": [
        "data/mail_template_data.xml",
        "data/portal_entry_data.xml",
        "views/layout_templates.xml",
        "views/shop_templates.xml",
        "views/quote_templates.xml",
        "views/portal_templates.xml",
        "views/page_home.xml",
        "views/page_about.xml",
        "views/page_services.xml",
        "views/page_industries.xml",
        "views/page_contact.xml",
        "views/support_templates.xml",
        "views/website_pages.xml",
        "views/backend_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "tl_dfs_website_quote/static/src/scss/dfs_website.scss",
            "tl_dfs_website_quote/static/src/js/quote_cart.js",
            "tl_dfs_website_quote/static/src/xml/cart_notification.xml",
        ],
    },
    "post_init_hook": "post_init_hook",
    "license": "LGPL-3",
    "installable": True,
    "application": False,
}
