{
    "name": "DFS Demo Data - Northbrook Analytical (UK lab equipment distribution & field service)",
    "version": "20.0.1.4.0",
    "category": "Hidden/Tools",
    "summary": "Configures a fresh database for a UK distributor of food-testing laboratory "
               "equipment with field service, and loads realistic sample data.",
    "description": """
Configuration + sample data for a typical UK distribution and field-service company
(fictional "Northbrook Analytical Ltd", Milton Keynes):

* company, GBP, UK chart of accounts (l10n_uk) with 20% VAT defaults, payment terms, incoterms
* settings: UoM, serial/lot tracking + expiry, storage locations, purchase approval, pricelists,
  discounts, leads, recurring revenue, field service materials/equipment/worksheets
* customers, contacts, vendors, employees (with users and planning roles), CRM pipeline,
  products with images, opening stock with serials, sales/purchases/deliveries/invoices,
  subscriptions (service contracts), helpdesk team + SLAs + tickets, field-service interventions
  (planning.slot) and shifts.

Data for the custom models (customer.asset, service.contract, website quote settings) is loaded
by "Settings > Technical > DFS Demo Data > Load Data for Custom Modules" (or
``env['tl.dfs.demo.loader'].action_load_custom_data()``) once those modules are installed.
""",
    "author": "Thoughtlogik Solutions",
    "website": "https://www.thoughtlogik.com",
    "license": "LGPL-3",
    "depends": [
        "contacts",
        "crm",
        "sale_management",
        "sale_crm",
        "sale_pdf_quote_builder",
        "purchase",
        "stock",
        "product_expiry",
        "planning",
        "planning_field_service",
        "planning_field_service_worksheet",
        "planning_field_service_sale_stock",
        "helpdesk",
        "website_helpdesk",
        "helpdesk_planning_field_service",
        "hr",
        "hr_skills",
        "account_accountant",
        "l10n_uk",
        "website_sale",
        "website_crm",
        "repair",
        "mrp",
        "sale_subscription",
        "sign",
    ],
    "data": [
        "data/res_company_data.xml",
        "data/res_partner_category_data.xml",
        "data/res_partner_vendor_data.xml",
        "data/res_partner_customer_data.xml",
        "data/planning_data.xml",
        "data/product_category_data.xml",
        "data/product_public_category_data.xml",
        "data/product_data.xml",
        "data/pricelist_data.xml",
        "data/crm_data.xml",
        "data/hr_data.xml",
        "data/helpdesk_data.xml",
        "data/worksheet_data.xml",
        "data/server_actions.xml",
        "data/quote_builder_data.xml",
        "data/mail_template_data.xml",
        "data/manufacturing_data.xml",
    ],
    "assets": {
        "web.report_assets_common": [
            "tl_dfs_demo_data/static/src/scss/report_fonts.scss",
        ],
    },
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}
