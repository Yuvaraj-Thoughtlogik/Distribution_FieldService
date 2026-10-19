import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class TlDfsDemoLoader(models.AbstractModel):
    _inherit = "tl.dfs.demo.loader"

    @api.model
    def _setup_contract_sign_template(self):
        """Use the Service Agreement template on the demo service-contract subscriptions and send one
        sample signature request so the Sign app shows a contract in progress. Idempotent."""
        template = self.env.ref("tl_dfs_demo_data_custom.sign_template_service_agreement", raise_if_not_found=False)
        if not template:
            return
        # "Name and position" on the agreement comes from the contact's job title: copy it from the employee.
        for employee in self.env["hr.employee"].search([("user_id", "!=", False), ("job_title", "!=", False)]):
            if not employee.user_id.partner_id.function:
                employee.user_id.partner_id.function = employee.job_title
        subscriptions = self._our_records("sale.order").filtered(lambda o: o.is_subscription)
        subscriptions.filtered(lambda o: not o.sign_template_id).sign_template_id = template

        if template.sign_request_ids:
            return
        line = self.env["service.contract.line"].search([
            ("sale_id", "in", subscriptions.filtered(lambda o: o.state == "sale").ids),
            ("sign_request_id", "=", False),
        ], order="id", limit=1)
        if not line:
            return
        Contract = self.env["service.contract"]
        order = line.sale_id
        signers = [
            {"partner_id": order.partner_id.id, "role_id": Contract._get_sign_role("customer").id},
            {"partner_id": (order.user_id or self.env.user).partner_id.id, "role_id": Contract._get_sign_role("user").id},
        ]
        request = line.create_sign_request(signers)
        _logger.info("tl_dfs_demo_data_custom: sample signature request %s for %s", request.reference, line.contract_id.name)
