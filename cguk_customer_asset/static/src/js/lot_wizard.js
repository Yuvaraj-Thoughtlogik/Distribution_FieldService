/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { registry } from "@web/core/registry";

export class CustomerAssetFormController extends FormController {
    async onFieldChanged(params) {
        await super.onFieldChanged(params);
        const { fieldName, data } = params;

        if (fieldName === "product_id" && data.product_id) {
            console.log("product_id changed", data.product_id);
            const resId = this.props.resId;
            if (resId) {
                const action = await this.orm.call("customer.asset", "action_open_lot_selector", [resId]);
                if (action) {
                    this.env.services.action.doAction(action);
                }
            }
        }
    }
}

// Register the controller under your custom key
registry.category("views").add("customer_asset_form", {
    ...registry.category("views").get("form"),
    Controller: CustomerAssetFormController,
});
