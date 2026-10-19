{
    'name': 'DFS Demo Data - Custom Modules Bridge',
    'version': '20.0.1.0.0',
    'summary': 'Loads demo data for the CGUK custom models once they are installed',
    'category': 'Hidden',
    'author': 'Thoughtlogik',
    'license': 'LGPL-3',
    'depends': ['tl_dfs_demo_data', 'tl_field_service_customisation', 'tl_dfs_website_quote'],
    'post_init_hook': 'post_init_hook',
    'auto_install': True,
    'installable': True,
}
