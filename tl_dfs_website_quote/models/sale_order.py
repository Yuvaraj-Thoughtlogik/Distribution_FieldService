import logging

from markupsafe import Markup, escape

from odoo import fields, models
from odoo.fields import Domain

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    dfs_quote_request = fields.Boolean(
        string="Website Quote Request",
        copy=False,
        readonly=True,
        index="btree_not_null",
        help="This quotation was requested through the quote-only website. "
             "It is not considered an abandoned cart.",
    )

    # ------------------------------------------------------------------
    # Abandoned cart: a submitted quote request is never an abandoned cart
    # ------------------------------------------------------------------
    def _compute_abandoned_cart(self):
        super()._compute_abandoned_cart()
        self.filtered("dfs_quote_request").is_abandoned_cart = False

    def _search_abandoned_cart(self, operator, value):
        domain = super()._search_abandoned_cart(operator, value)
        if domain is NotImplemented:
            return domain
        return Domain(domain) & Domain("dfs_quote_request", "=", False)

    # ------------------------------------------------------------------
    # Quote request submission
    # ------------------------------------------------------------------
    def _dfs_get_utm_source(self):
        Source = self.env["utm.source"].sudo()
        source = Source.search([("name", "=", "Website")], limit=1)
        return source or Source.create({"name": "Website"})

    def _dfs_prepare_lead_description(self, form):
        self.ensure_one()
        rows = Markup("").join(
            Markup("<li>%s &times; %s%s</li>") % (
                self._dfs_format_qty(line.product_uom_qty),
                line.name_short if "name_short" in line._fields else line.product_id.display_name,
                Markup(" (%s)") % line.product_uom_id.name if line.product_uom_id else "",
            )
            for line in self.order_line.filtered(lambda l: not l.display_type and l.product_id)
        )
        parts = [
            Markup("<p><strong>Quote requested from the website</strong> (%s)</p>") % self.name,
            Markup("<ul>%s</ul>") % rows,
        ]
        if form.get("notes"):
            parts.append(
                Markup("<p><strong>Customer notes:</strong><br/>%s</p>")
                % Markup("<br/>").join(escape(form["notes"]).splitlines())
            )
        if form.get("reference"):
            parts.append(Markup("<p><strong>Customer reference:</strong> %s</p>") % form["reference"])
        return Markup("").join(parts)

    @staticmethod
    def _dfs_format_qty(qty):
        return ("%f" % qty).rstrip("0").rstrip(".")

    def _dfs_submit_quote_request(self, form, visitor=None):
        """Turn the current website cart into a draft quotation linked to a new opportunity.

        :param dict form: cleaned form values (name, company, email, phone, street, city, zip,
            country_id, notes, reference)
        :param website.visitor visitor: current visitor (optional)
        :return: the created `crm.lead`
        """
        self.ensure_one()
        order = self.sudo()
        website = order.website_id or self.env["website"].get_current_website()

        partner = self.env["res.partner"].sudo()._dfs_get_quote_partner(form, website)

        # Re-assign the cart to the customer (recomputes pricelist / fiscal position / prices
        # with the customer's own pricelist).
        order._update_address(
            partner.id, ["partner_id", "partner_invoice_id", "partner_shipping_id"]
        )

        team = website._dfs_get_quote_team()
        user = website.crm_default_user_id or team.user_id
        Lead = self.env["crm.lead"].sudo()
        company_name = form.get("company") or partner.commercial_partner_id.name
        lead_vals = {
            "name": self.env._(
                "Website quote request - %(who)s", who=company_name or partner.name
            ),
            "type": "opportunity",
            "partner_id": partner.id,
            "contact_name": form.get("name") or partner.name,
            "partner_name": company_name,
            "street": form.get("street") or partner.street,
            "city": form.get("city") or partner.city,
            "zip": form.get("zip") or partner.zip,
            "country_id": form.get("country_id") or partner.country_id.id,
            "team_id": team.id,
            "user_id": user.id or False,
            "company_id": website.company_id.id,
            "medium_id": self.env["utm.mixin"]._utm_ref("utm.utm_medium_website").id,
            "source_id": order._dfs_get_utm_source().id,
            "description": order._dfs_prepare_lead_description(form),
            "dfs_is_quote_request": True,
            "expected_revenue": order.amount_untaxed,
        }
        # Same behaviour as website_crm forms: the partner holds the contact data.
        if not partner.email:
            lead_vals["email_from"] = form.get("email")
        if not partner.phone:
            lead_vals["phone"] = form.get("phone")
        tag = self.env.ref("tl_dfs_website_quote.crm_tag_website_quote", raise_if_not_found=False)
        if tag:
            lead_vals["tag_ids"] = [fields.Command.link(tag.id)]
        if visitor:
            lead_vals["visitor_ids"] = [fields.Command.link(visitor.id)]
        lead = Lead.with_context(mail_create_nosubscribe=True).create(lead_vals)

        order.write({
            "dfs_quote_request": True,
            "opportunity_id": lead.id,
            "team_id": team.id,
            "user_id": user.id or False,
            "origin": self.env._("Website quote request"),
            "client_order_ref": form.get("reference") or False,
            "date_order": fields.Datetime.now(),
            "cart_recovery_email_sent": True,  # never send cart recovery e-mails
        })
        if form.get("notes"):
            order.message_post(
                body=Markup("<p><strong>%s</strong><br/>%s</p>") % (
                    self.env._("Customer notes:"),
                    Markup("<br/>").join(escape(form["notes"]).splitlines()),
                ),
                message_type="comment",
                subtype_xmlid="mail.mt_note",
            )
        lead._dfs_send_quote_acknowledgement()
        return lead
