{
    'name': 'DFS Demo Data - Custom Modules Bridge',
    'version': '20.0.1.1.0',
    'summary': 'Loads demo data for the CGUK custom models once they are installed',
    'description': """
Loads customer assets and service contracts for the Northbrook Analytical demo, tidies sales teams,
and adds the "Service Agreement" Sign template used to send service contracts for signature
(fields are auto-filled from the contract through tl_sign_autofill).
""",
    'category': 'Hidden',
    'author': 'Thoughtlogik',
    'license': 'LGPL-3',
    'depends': ['tl_dfs_demo_data', 'tl_field_service_customisation', 'tl_dfs_website_quote', 'tl_sign_autofill'],
    'data': [
        'data/sign_template_data.xml',
        'data/demo_loader_data.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'auto_install': True,
    'installable': True,
}
