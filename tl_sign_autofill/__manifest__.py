# -*- coding: utf-8 -*-
{
    'name': "Sign Auto fill",

    'summary': "Sign Template Auto Fill Values",

    'description': """
Long description of module's purpose
    """,

    'author': 'Thoughtlogik Solutions',
    'website': 'www.thoughtlogik.com',
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['sign'],

    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/sign_template.xml',
        'views/sign_template_templates.xml',
        'wizard/send_sign_request.xml',
    ],
    "assets": {
        'web.assets_backend': [
            'tl_sign_autofill/static/src/backend_components/sign_template/sign_item_custom_popover.js',
            'tl_sign_autofill/static/src/backend_components/sign_template/sign_item_custom_popover.xml',
            'tl_sign_autofill/static/src/backend_components/sign_template/sign_template_iframe.js',
            'tl_sign_autofill/static/src/backend_components/sign_template/sign_template_body.js',
        ],
        'sign.assets_public_sign': [
            'tl_sign_autofill/static/src/components/sign_request/PDF_iframe.js',
            'tl_sign_autofill/static/src/components/sign_request/sign_items.xml',
        ],
    },
}

