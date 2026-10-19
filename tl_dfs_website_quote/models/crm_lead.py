import logging

from odoo import api, fields, models
from odoo.tools import email_normalize

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = "crm.lead"

    dfs_is_quote_request = fields.Boolean(
        string="Website Quote Request", copy=False, readonly=True, index="btree_not_null"
    )

    def _dfs_send_quote_acknowledgement(self):
        template = self.env.ref(
            "tl_dfs_website_quote.mail_template_quote_request_ack", raise_if_not_found=False
        )
        if not template:
            return
        for lead in self:
            if not (lead.email_from or lead.partner_id.email):
                continue
            try:
                lead.with_context(mail_notify_force_send=False).message_post_with_source(
                    template.sudo(),
                    subtype_xmlid="mail.mt_comment",
                    partner_ids=lead.partner_id.ids,
                    message_type="comment",
                    email_layout_xmlid="mail.mail_notification_light",
                )
            except Exception:  # noqa: BLE001 - never block a quote request on e-mail issues
                _logger.exception("Could not send the quote request acknowledgement for %s", lead)


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def _dfs_get_quote_partner(self, form, website):
        """Find or create the contact person (and company) for a website quote request.

        * logged-in (non public) user: use their partner, completing missing data only;
        * otherwise: match an existing contact on the e-mail address, else create the company
          (matched on its name) and the contact person under it.
        """
        user = self.env.user
        Partner = self.sudo()
        country_id = form.get("country_id") or False
        address = {
            "street": form.get("street") or False,
            "city": form.get("city") or False,
            "zip": form.get("zip") or False,
            "country_id": country_id,
        }

        if user and not user._is_public() and user.partner_id != website.user_id.partner_id:
            partner = user.partner_id.sudo()
            missing = {
                key: value for key, value in {**address, "phone": form.get("phone")}.items()
                if value and not partner[key]
            }
            if missing and not partner.parent_id:
                partner.write(missing)
            return partner

        email = email_normalize(form.get("email") or "")
        partner = Partner
        if email:
            partner = Partner.search(
                [("email_normalized", "=", email), ("type", "=", "contact")],
                order="parent_id desc, id", limit=1,
            )
        if partner:
            return partner

        company = Partner
        company_name = (form.get("company") or "").strip()
        if company_name:
            company = Partner.search(
                [("is_company", "=", True), ("name", "=ilike", company_name)], limit=1
            )
            if not company:
                company = Partner.create({
                    "name": company_name,
                    "is_company": True,
                    "phone": form.get("phone") or False,
                    "company_id": False,
                    **address,
                })
        vals = {
            "name": form.get("name") or email,
            "email": form.get("email") or False,
            "phone": form.get("phone") or False,
            "type": "contact",
        }
        if company:
            vals["parent_id"] = company.id
            # Contact address is synchronised from the company; only fill it when the
            # company has no address yet.
            if not company.street and address.get("street"):
                company.write({k: v for k, v in address.items() if v})
        else:
            vals.update(address)
        partner = Partner.create(vals)
        return partner
