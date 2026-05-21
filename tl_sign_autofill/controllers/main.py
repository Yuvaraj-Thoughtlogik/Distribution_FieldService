from odoo.addons.sign.controllers.main import Sign
from odoo.http import request
from odoo import http


class SignController(Sign):

    def get_document_qweb_context(self, sign_request_id, token, **post):

        res = super().get_document_qweb_context(
            sign_request_id,
            token,
            **post
        )

        sign_request = res.get('sign_request')

        role_id = res.get('role')
        if sign_request and role_id:

            auto_values = request.env[
                'sign.auto.fill.value'
            ].sudo().search([
                ('sign_request_id', '=', sign_request.id),
                '|',('role_id', '=', role_id),('by_system', '=', True),
            ])
            item_values = dict(res.get('item_values') or {})
            frame_values = dict(res.get('frame_values') or {})
            for item_value in auto_values:
                if item_value.sign_item_id and item_value.value:
                    item_values[item_value.sign_item_id.id] = item_value.value
                    frame_values[item_value.sign_item_id.id] = False
            res['item_values'] = item_values

            res['frame_values'] = frame_values

        return res