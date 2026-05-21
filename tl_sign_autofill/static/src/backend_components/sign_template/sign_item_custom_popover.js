/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { SignItemCustomPopover } from "@sign/backend_components/sign_template/sign_item_custom_popover";

SignItemCustomPopover.props = {
    ...SignItemCustomPopover.props,

    auto_fill: {
        type: Boolean,
        optional: true,
    },
    by_system: {
        type: Boolean,
        optional: true,
    },
    key: {
        type: String,
        optional: true,
    },
};

patch(SignItemCustomPopover.prototype, {

    setup() {
        super.setup();

        this.state.auto_fill = this.props.auto_fill ?? false;
        this.state.by_system = this.props.by_system ?? false;
        this.state.key = this.props.key ?? " ";
    },
    get isAutoFillSupported() {
        return ["text", "textarea"].includes(this.props.type);
    },

    onValidate() {

        if (this.state.auto_fill && !this.state.key?.trim()) {

           const close = this.env.services.notification.add(
                "Key is required when Auto Fill is enabled.",
                {
                    title: "Validation Error",
                    type: "danger",
                    sticky: false,
                }
            );


            return;
        }

        this.props.onValidate(this.state);
    },
    onChange(key, value) {
        if (key === "auto_fill" && value === false) {
            this.state.by_system = false;
            this.state.key = "";
        }
        else if (key === "auto_fill" && value === true) {
            this.state.by_system = false;


            const variableName = this.state.placeholder
                .toLowerCase()
                .replace(/[^a-zA-Z0-9_$]/g, "_")
                .replace(/^[^a-zA-Z_$]+/, "");

            this.state.key = variableName;
        }

        this.state[key] = value;
    }
});