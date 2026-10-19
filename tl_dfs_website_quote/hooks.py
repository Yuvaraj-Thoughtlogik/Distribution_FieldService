import logging

from odoo.tools import BinaryBytes, file_open

_logger = logging.getLogger(__name__)

# Brand palette (website builder "user palette", editable afterwards in the builder):
#   o-color-1: brand blue (primary accent), o-color-2: deep navy (secondary),
#   o-color-3: light grey surface, o-color-4: white, o-color-5: dark text / footer.
BRAND_PALETTE = {
    "o-color-1": "#0057B8",
    "o-color-2": "#0B2545",
    "o-color-3": "#F2F4F7",
    "o-color-4": "#FFFFFF",
    "o-color-5": "#14213D",
}


def _setup_theme(env, website):
    Assets = env["website.assets"].with_context(website_id=website.id)
    try:
        Assets.make_scss_customization(
            "/website/static/src/scss/options/colors/user_color_palette.scss",
            dict(BRAND_PALETTE),
        )
        Assets.make_scss_customization(
            "/website/static/src/scss/options/user_values.scss",
            {
                "btn-border-radius": "0.25rem",
                "btn-border-radius-sm": "0.2rem",
                "btn-border-radius-lg": "0.3rem",
            },
        )
    except Exception:  # noqa: BLE001 - theme is cosmetic, never block the install
        _logger.exception("Could not apply the brand palette on website %s", website.id)


def _setup_logo(website):
    try:
        with file_open("tl_dfs_website_quote/static/src/img/brand_mark.png", "rb") as f:
            website.logo = BinaryBytes(f.read())
    except Exception:  # noqa: BLE001
        _logger.exception("Could not set the website logo")


def post_init_hook(env):
    env["website"]._dfs_setup_websites()
    for website in env["website"].search([]):
        _setup_theme(env, website)
        _setup_logo(website)
