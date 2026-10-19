# tl_dfs_website_quote - B2B "request a quote" website

Quote-only eCommerce + corporate website for a UK distributor of food-testing /
laboratory equipment and field service (fictional brand "Northbrook Analytical";
the displayed name always comes from `res.company.name`).

## Quote flow
* `/shop/cart` renders the "Quote request" list (qty editing via `/shop/quote/update`).
* `/shop/quote/request` collects contact/company/e-mail/phone/address/notes (prefilled for
  logged-in users), `/shop/quote/submit` creates/finds the partner (company + contact),
  a `crm.lead` opportunity (team = `website.crm_default_team_id`, else `website.salesteam_id`),
  links the website cart as a **draft** `sale.order` (`dfs_quote_request=True`,
  `opportunity_id` set, excluded from abandoned carts) and e-mails an acknowledgement
  (no prices). `/shop/quote/thank-you` shows the reference.
* Checkout, address, payment, express checkout, pricelist switch, `/shop/print` and the GMC
  feed are disabled while `website.dfs_quote_mode` is set (default True).
* Portal: `/my/quote-requests`.

## Images
All images in `static/src/img` are original illustrations generated locally with Pillow
(gradients and geometric shapes) for this module. No third-party, Wikimedia or brand
imagery is used, so no attribution is required.
