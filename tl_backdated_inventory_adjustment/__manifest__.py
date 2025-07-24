{
    'name': "Inventory Adjustment Backdated",
    'category': 'Inventory',
    'version': '18.0.1.0',
    'author': 'ThoughtLogik',
    'description': """
        This Module allows user to do adjustments in back dated-force dated.
        * Allow user to do adjustments in back dated-force dated..
        * Update the date in stock moves and product moves.
        * Update the date in journal entries if product have automated valuation method.
    """,

    'depends': ['stock_account'],
    'license': 'OPL-1',
    'website': "",
    'data': [
       # 'data/stock_view_bulk.xml',
        'views/stock_view.xml',
        
    ],
    
    'installable': True,
    'auto_install': False,
    'application': False,
}


