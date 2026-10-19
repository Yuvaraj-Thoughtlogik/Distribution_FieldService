import { patch } from "@web/core/utils/patch";
import { SignTemplateIframe } from "@sign/backend_components/sign_template/sign_template_iframe";
import { SignItemCustomPopover } from "@sign/backend_components/sign_template/sign_item_custom_popover";

/**
 * Odoo 20: core `updateSignItem` already keeps keys that are not part of the
 * item data, so only the popover props need to be extended with the
 * auto-fill values (auto_fill / by_system / key).
 */
patch(SignTemplateIframe.prototype, {
    async openSignItemPopup(signItem) {
        const popoverService = this.popover;
        const originalAdd = popoverService.add;
        this.popover = Object.assign(Object.create(popoverService), {
            add: (target, Comp, props, options) => {
                if (Comp === SignItemCustomPopover) {
                    props = {
                        ...props,
                        auto_fill: signItem.data.auto_fill ?? false,
                        by_system: signItem.data.by_system ?? false,
                        key: signItem.data.key || "",
                    };
                }
                return originalAdd.call(popoverService, target, Comp, props, options);
            },
        });
        try {
            return await super.openSignItemPopup(signItem);
        } finally {
            this.popover = popoverService;
        }
    },
});
