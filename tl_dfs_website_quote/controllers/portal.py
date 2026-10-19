from odoo.http import request, route

from odoo.addons.portal.controllers.portal import CustomerPortal


class DfsQuotePortal(CustomerPortal):
    def _dfs_quote_request_domain(self):
        partner = request.env.user.partner_id
        return [
            ("dfs_is_quote_request", "=", True),
            ("partner_id", "child_of", [partner.commercial_partner_id.id]),
        ]

    @route("/my/quote-requests", type="http", auth="user", website=True, sitemap=False)
    def dfs_portal_my_quote_requests(self, **kwargs):
        # Leads are not readable by portal users: read them as superuser, restricted to the
        # requests of the user's own company, and only expose non-price information.
        leads = request.env["crm.lead"].sudo().with_context(active_test=False).search(
            self._dfs_quote_request_domain(), order="create_date desc", limit=100
        )
        values = self._prepare_portal_layout_values()
        values.update({
            "quote_requests": leads,
            "page_name": "dfs_quote_requests",
        })
        return request.render("tl_dfs_website_quote.portal_my_quote_requests", values)
