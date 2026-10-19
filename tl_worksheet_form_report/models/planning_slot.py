from markupsafe import Markup, escape

from odoo import models

SECTION_STYLE = (
    "font-size:12px; font-weight:700; color:#111827; text-transform:uppercase;"
    " letter-spacing:0.4px; margin-top:6px; margin-bottom:4px;"
    " border-bottom:1px solid #E5E7EB; padding-bottom:2px;"
)
CARD_STYLE = (
    "font-family:'Inter', Arial, sans-serif; font-size:12px; color:#1F2937; width:100%;"
    " background-color:#FFFFFF; border:1px solid #E5E7EB; border-top:3px solid #714B67;"
    " border-radius:4px; padding:10px 14px; margin-top:6px;"
    " box-shadow:0 1px 3px rgba(0,0,0,0.05); box-sizing:border-box;"
)
TABLE_STYLE = "width:100%; margin-bottom:2px; border:0px solid transparent !important; border-collapse:collapse;"
LABEL_STYLE = (
    "width:45%; font-weight:600; color:#4B5563; font-size:11.5px; vertical-align:middle;"
    " padding:2px 4px 2px 0px; border:0px solid transparent !important; line-height:1.5;"
)
VALUE_STYLE = (
    "width:55%; font-size:11.5px; color:#1F2937; vertical-align:middle; padding:2px 0px;"
    " border:0px solid transparent !important; word-break:break-word; line-height:1.5;"
)


class PlanningSlot(models.Model):
    _inherit = "planning.slot"

    def _render_worksheet_value_html(self, prop):
        prop_type = prop.get('type')
        value = prop.get('value')
        if prop_type == 'boolean':
            checked = 'checked="checked"' if value else ''
            return Markup(
                '<input type="checkbox" %s disabled="disabled" '
                'style="width:13px; height:13px; margin:0; vertical-align:middle;"/>'
            ) % Markup(checked)
        if prop_type in ('signature', 'image'):
            if not value:
                return Markup('<span style="color:#9CA3AF; font-style:italic; font-size:11px;">%s</span>') % self.env._("No file uploaded")
            return Markup(
                '<div style="display:inline-block; border:1px solid #E5E7EB; border-radius:4px; padding:2px;'
                ' background-color:#F9FAFB; max-width:180px;"><img src="data:image/png;base64,%s"'
                ' style="max-width:100%%; max-height:100px; display:block; object-fit:contain;"/></div>'
            ) % (value.decode() if isinstance(value, bytes) else value)
        if prop_type == 'binary':
            if not value:
                return Markup('<span style="color:#9CA3AF; font-style:italic; font-size:11px;">%s</span>') % self.env._("No file uploaded")
            return Markup(
                '<span style="color:#2563EB; font-size:11px; font-weight:500; background-color:#EFF6FF;'
                ' padding:2px 6px; border-radius:8px;">%s</span>'
            ) % (value.get('filename') if isinstance(value, dict) else self.env._("Attachment File Provided"))
        if prop_type == 'tags':
            return Markup(', ').join(escape(tag.get('name', '')) for tag in (value or []))
        if value is False or value is None:
            return Markup('&nbsp;')
        if isinstance(value, Markup):
            return value
        return escape(value)

    def _render_worksheet_field_html(self, prop):
        return Markup(
            '<table border="0" cellpadding="0" cellspacing="0" style="%s"><tr style="border:0px solid transparent !important;">'
            '<td style="%s">%s</td><td style="%s">%s</td></tr></table>'
        ) % (TABLE_STYLE, LABEL_STYLE, prop.get('name') or '', VALUE_STYLE, self._render_worksheet_value_html(prop))

    def _render_worksheet_html(self, props_formatted):
        """Render a list of formatted worksheet properties (see
        `worksheet.template.format_props` / `planning.slot._get_props_formatted`) with the
        CGUK styled layout (purple card, sections, two columns label/value)."""
        if not props_formatted:
            return Markup('')
        html = Markup('<div style="%s">') % CARD_STYLE
        for prop in props_formatted:
            if prop.get('type') == 'separator':
                html += Markup('<div style="%s">%s</div>') % (SECTION_STYLE, prop.get('name') or '')
            elif prop.get('type') == 'studio_columns':
                html += Markup('<table border="0" cellpadding="0" cellspacing="0" style="%s"><tr>') % TABLE_STYLE
                for column in prop.get('columns', []):
                    html += Markup('<td style="width:50%; vertical-align:top; padding-right:15px; border:0px solid transparent !important;">')
                    for column_prop in column:
                        html += self._render_worksheet_field_html(column_prop)
                    html += Markup('</td>')
                html += Markup('</tr></table>')
            else:
                html += self._render_worksheet_field_html(prop)
        html += Markup('</div>')
        return html

    def generate_worksheet_html(self):
        """Styled HTML of the intervention's own worksheet (single worksheet mode)."""
        self.ensure_one()
        return self._render_worksheet_html(self._get_props_formatted())
