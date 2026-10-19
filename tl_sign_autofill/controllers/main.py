from odoo.addons.sign.controllers.main import Sign
from odoo.http import request


class SignController(Sign):

    def get_document_qweb_context(self, sign_request_id, token, **post):
        res = super().get_document_qweb_context(sign_request_id, token, **post)

        # Odoo 20: the template values live in res['rendering_context']
        ctx = res.get('rendering_context')
        if not ctx:
            return res

        sign_request = ctx.get('sign_request')
        role_id = ctx.get('role')

        if sign_request and role_id:
            auto_values = request.env['sign.auto.fill.value'].sudo().search([
                ('sign_request_id', '=', sign_request.id),
                '|',
                ('role_id', '=', role_id),
                ('by_system', '=', True),
            ])

            item_values = dict(ctx.get('item_values') or {})
            frame_values = dict(ctx.get('frame_values') or {})

            for item_value in auto_values:
                if item_value.sign_item_id:
                    item_values[item_value.sign_item_id.id] = str(item_value.value or '')
                    frame_values[item_value.sign_item_id.id] = False

            ctx['item_values'] = item_values
            ctx['frame_values'] = frame_values

        return res
