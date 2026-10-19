import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { t, useProps } from "@odoo/owl";
import { SignItemCustomPopover } from "@sign/backend_components/sign_template/sign_item_custom_popover";

patch(SignItemCustomPopover.prototype, {
    setup() {
        super.setup();
        // Odoo 20 / OWL 3: props are declared with useProps(); declare the extra ones here.
        this.autoFillProps = useProps({
            auto_fill: t.any().optional(),
            by_system: t.any().optional(),
            key: t.any().optional(),
        });
        this.state.auto_fill = Boolean(this.autoFillProps.auto_fill);
        this.state.by_system = Boolean(this.autoFillProps.by_system);
        this.state.key = this.autoFillProps.key || "";
    },

    get isAutoFillSupported() {
        return ["text", "textarea"].includes(this.props.type);
    },

    async onValidate() {
        if (this.state.auto_fill && !this.state.key?.trim()) {
            this.notification.add(_t("Key is required when Auto Fill is enabled."), {
                title: _t("Validation Error"),
                type: "danger",
            });
            return;
        }
        return super.onValidate();
    },

    onChange(key, value) {
        if (key === "auto_fill" && value === false) {
            this.state.by_system = false;
            this.state.key = "";
        } else if (key === "auto_fill" && value === true) {
            this.state.by_system = false;
            this.state.key = (this.state.placeholder || "")
                .toLowerCase()
                .replace(/[^a-zA-Z0-9_$]/g, "_")
                .replace(/^[^a-zA-Z_$]+/, "");
        }
        return super.onChange(key, value);
    },
});
