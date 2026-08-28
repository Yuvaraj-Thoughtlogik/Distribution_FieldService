# -*- coding: utf-8 -*-

from lxml import etree
from markupsafe import Markup,escape

from odoo import models, fields
from odoo.tools.safe_eval import safe_eval


class FSMTask(models.Model):
    _inherit = "project.task"


    def _is_node_invisible(self, node, record):
        invisible_attr = node.attrib.get("invisible")
        if not invisible_attr:
            return False

        if invisible_attr in ("1", "True", "true"):
            return True
        if invisible_attr in ("0", "False", "false"):
            return False

        try:
            eval_context = {
                'record': record,
                'context': self.env.context,
                'uid': self.env.uid,
                'user': self.env.user,
            }
            for field_name in record._fields:
                eval_context[field_name] = record[field_name]

            result = safe_eval(invisible_attr, eval_context)
            return bool(result)
        except Exception:
            return False

    def _render_worksheet_node(self, node, record):
        html = ""

        if self._is_node_invisible(node, record) or node.attrib.get('name') == 'x_project_task_id':
            return ""

        if node.tag == "group":
            title = node.attrib.get("string", "")
            child_groups = [c for c in node if c.tag == "group"]

            # Layout group (<group><group/><group/></group>)
            if child_groups:
                # Render the Master Parent Group Header if it has a string title (e.g., INFORMATION)
                if title:
                    html += f"""
                    <div style="
                        font-size:13px;
                        font-weight:700;
                        color:#714B67; /* Odoo Theme Purple Accent */
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                        margin-top: 10px;
                        margin-bottom: 6px;
                        border-bottom: 1.5px solid #714B67;
                        padding-bottom: 3px;
                    ">
                        {title}
                    </div>
                    """

                html += """
                <table border="0" cellpadding="0" cellspacing="0" style="
                    width:100%;
                    border:0px solid transparent !important;
                    border-collapse:collapse;
                    margin-bottom:6px;
                ">
                """

                for i in range(0, len(child_groups), 2):
                    html += '<tr style="border:0px solid transparent !important;">'

                    for child in child_groups[i:i + 2]:
                        # Skip inner columns if they are evaluated to invisible
                        if self._is_node_invisible(child, record):
                            html += '<td style="width:50%; border:none !important;"></td>'
                            continue

                        html += """
                        <td style="
                            width:50%;
                            vertical-align:top;
                            padding-right:15px;
                            border:0px solid transparent !important;
                        ">
                        """

                        child_title = child.attrib.get("string")
                        if child_title:
                            # Standard Odoo Inner Column Section Heading Style
                            html += f"""
                            <div style="
                                font-size:12px;
                                font-weight:700;
                                color:#111827;
                                text-transform: uppercase;
                                letter-spacing: 0.4px;
                                margin-top: 2px;
                                margin-bottom: 4px;
                                border-bottom: 1px solid #E5E7EB;
                                padding-bottom: 2px;
                            ">
                                {child_title}
                            </div>
                            """

                        for subchild in child:
                            html += self._render_worksheet_node(subchild, record)

                        html += "</td>"

                    if len(child_groups[i:i + 2]) == 1:
                        html += '<td style="width:50%;border:0px solid transparent !important;"></td>'

                    html += "</tr>"

                html += "</table>"
                return html

            # Normal single group heading (Single columns)
            if title:
                html += f"""
                <div style="
                    font-size:12px;
                    font-weight:700;
                    color:#111827;
                    text-transform: uppercase;
                    letter-spacing: 0.4px;
                    margin-top:6px;
                    margin-bottom:4px;
                    border-bottom:1px solid #E5E7EB;
                    padding-bottom:2px;
                ">
                    {title}
                </div>
                """

            for child in node:
                html += self._render_worksheet_node(child, record)

            return html

        elif node.tag == "field":
            field_name = node.attrib.get("name")

            if not field_name or field_name not in record._fields:
                return ""

            field = record._fields[field_name]
            value = record[field_name]
            field_string = node.attrib.get("string") or field.string

            if field.type == "many2one":
                value_html = value.display_name if value else ""
            elif field.type in ("many2many", "one2many"):
                value_html = ", ".join(value.mapped("display_name"))
            elif field.type == "boolean":
                checked_attr = 'checked="checked"' if value else ''
                value_html = f"""
                <input type="checkbox" {checked_attr} disabled="disabled" style="
                    width: 13px;
                    height: 13px;
                    margin: 0;
                    vertical-align: middle;
                    cursor: not-allowed;
                "/>
                """
            elif field.type == "html":
                value_html = value or ""
            elif field.type == "binary":
                if value:
                    base64_str = value.decode('utf-8') if isinstance(value, bytes) else str(value)
                    is_image = any(base64_str.startswith(prefix) for prefix in ('iVBORw0KG', '/9j/', 'R0lGOD', 'UklGR'))

                    if is_image:
                        value_html = f"""
                        <div style="
                            display: inline-block;
                            border: 1px solid #E5E7EB;
                            border-radius: 4px;
                            padding: 2px;
                            background-color: #F9FAFB;
                            max-width: 180px;
                        ">
                            <img src="data:image/png;base64,{base64_str}" style="
                                max-width: 100%;
                                max-height: 100px;
                                display: block;
                                object-fit: contain;
                            "/>
                        </div>
                        """
                    else:
                        value_html = """
                        <span style="
                            color: #2563EB; 
                            font-size: 11px; 
                            font-weight: 500;
                            background-color: #EFF6FF;
                            padding: 2px 6px;
                            border-radius: 8px;
                        ">
                            📎 Attachment File Provided
                        </span>
                        """
                else:
                    value_html = '<span style="color: #9CA3AF; font-style: italic; font-size: 11px;">No file uploaded</span>'
            elif field.type == "text":
                value_html = "<br/>".join(
                    line.strip() for line in (value or "").splitlines() if line.strip()
                )
            elif field.type == "selection":
                value_html = dict(field.selection).get(value, "") if value else ""

            else:
                value_html = str(value) if value is not False and value is not None else ""

            return f"""
            <table border="0" cellpadding="0" cellspacing="0" style="
                width:100%;
                margin-bottom:2px;
                border:0px solid transparent !important;
                border-collapse:collapse;
            ">
                <tr style="border:0px solid transparent !important;">
                    <td style="
                        width:45%;
                        font-weight:600;
                        color:#4B5563;
                        font-size:11.5px;
                        vertical-align:middle;
                        padding: 2px 4px 2px 0px;
                        border:0px solid transparent !important;
                        line-height: 1.5;
                    ">
                        {field_string}
                    </td>

                    <td style="
                        width:55%;
                        font-size:11.5px;
                        color:#1F2937;
                        vertical-align:middle;
                        padding: 2px 0px;
                        border:0px solid transparent !important;
                        word-break: break-word;
                        line-height: 1.5;
                    ">
                        {value_html if value_html else ' '}
                    </td>
                </tr>
            </table>
            """

        else:
            for child in node:
                html += self._render_worksheet_node(child, record)

        return html

    def generate_worksheet_html(self, worksheet_template_id, worksheet_id=False):
        self.ensure_one()

        worksheet_template = self.env['worksheet.template'].sudo().browse(worksheet_template_id)
        if not worksheet_template:
            return ""

        if not worksheet_template.model_id:
            return ""

        worksheet_model = worksheet_template.model_id.model
        if not worksheet_model or worksheet_model not in self.env:
            return ""

        if worksheet_id:
            worksheet = self.env[worksheet_model].sudo().browse(worksheet_id)
        else:
            worksheet = self.env[worksheet_model].sudo().search([('x_project_task_id', '=', self.id)], limit=1)

        if not worksheet or not worksheet.exists():
            return ""

        view = self.env["ir.ui.view"].sudo().search([
            ("model", "=", worksheet_model),
            ("type", "=", "form"),
            ("mode", "=", "primary")
        ], limit=1)

        if not view:
            return ""

        view_data = worksheet.sudo().get_view(view_id=view.id, view_type="form")
        arch = etree.fromstring(view_data["arch"])

        # Styled as an Odoo Sheet Container Component Card with condensed spacing
        html = """
        <div style="
            font-family: 'Inter', Arial, sans-serif;
            font-size:12px;
            color:#1F2937;
            width:100%;
            background-color: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-top: 3px solid #714B67; /* Standard Odoo Purple accent header bar */
            border-radius: 4px;
            padding: 10px 14px;
            margin-top: 6px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            box-sizing: border-box;
        ">
        """

        html += self._render_worksheet_node(arch, worksheet)
        html += "</div>"

        return Markup(html)