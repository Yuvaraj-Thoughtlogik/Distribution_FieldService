from odoo import api, fields, models
from odoo.http import request

from odoo.addons.website_sale.models.website import CART_SESSION_CACHE_KEY


class Website(models.Model):
    _inherit = "website"

    dfs_quote_mode = fields.Boolean(
        string="Quote-only eCommerce",
        default=True,
        help="Hide every price on the website, replace checkout/payment by a quote request "
             "that creates a CRM opportunity and a draft quotation.",
    )

    def _dfs_hide_prices(self):
        """Return True when prices must be hidden on this website (frontend only)."""
        website = self[:1] or self.env["website"].get_current_website()
        return bool(website.dfs_quote_mode)

    def _dfs_get_quote_team(self):
        """Sales team for website quote requests."""
        self.ensure_one()
        team = self.crm_default_team_id or self.salesteam_id
        if not team:
            team = self.env.ref("sales_team.team_sales_department", raise_if_not_found=False)
        if not team:
            team = self.env["crm.team"].sudo().search(
                [("company_id", "in", [False, self.company_id.id])], limit=1
            )
        return team

    def _get_product_sort_mapping(self):
        mapping = super()._get_product_sort_mapping()
        if self._dfs_hide_prices():
            mapping = [item for item in mapping if "list_price" not in item[0]]
        return mapping

    def _get_and_cache_current_cart(self):
        cart_sudo = super()._get_and_cache_current_cart()
        if cart_sudo and cart_sudo.dfs_quote_request:
            # A submitted quote request must never be resurrected as a cart.
            self.sale_reset()
            if request and not self.env.user._is_public():
                # Remember "no cart" to avoid searching an abandoned cart again.
                request.session[CART_SESSION_CACHE_KEY] = False
            cart_sudo = self.env["sale.order"].sudo()
        return cart_sudo

    def _search_get_details(self, search_type, order, options):
        # Never allow ordering search results by price on a quote-only website.
        if order and "list_price" in order and self._dfs_hide_prices():
            order = "name asc"
        return super()._search_get_details(search_type, order, options)

    # ------------------------------------------------------------------
    # Setup helpers (called by post_init_hook, idempotent)
    # ------------------------------------------------------------------
    @api.model
    def _dfs_setup_websites(self):
        for website in self.search([]):
            website._dfs_setup_menus()
            website._dfs_setup_settings()

    def _dfs_setup_settings(self):
        self.ensure_one()
        # Quote requests are not carts: never send abandoned-cart follow-ups.
        self.write({"send_abandoned_cart_followup": False})

    def _dfs_setup_menus(self):
        """Create / reorder the main menu: Products, Industries, Services, Support, About,
        Contact. Existing menus are matched on their URL so that this is idempotent."""
        self.ensure_one()
        Menu = self.env["website.menu"]
        root = self.menu_id
        if not root:
            return
        wanted = [
            ("Home", "/", 5),
            ("Products", "/shop", 10),
            ("Industries", "/industries", 20),
            ("Services", "/services", 30),
            ("Support", "/helpdesk", 40),
            ("About", "/about-us", 50),
            ("Contact", "/contactus", 60),
        ]
        existing = Menu.search([("website_id", "=", self.id), ("parent_id", "=", root.id)])
        for name, url, seq in wanted:
            menu = existing.filtered(lambda m, u=url: (m.url or "").rstrip("/") == u.rstrip("/")
                                     or (u == "/" and m.url == "/"))[:1]
            if menu:
                menu.write({"name": name, "sequence": seq})
            else:
                Menu.create({
                    "name": name, "url": url, "sequence": seq,
                    "parent_id": root.id, "website_id": self.id,
                })
