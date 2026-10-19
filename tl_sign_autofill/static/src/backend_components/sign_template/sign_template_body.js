import { patch } from "@web/core/utils/patch";
import { SignTemplateBody } from "@sign/backend_components/sign_template/sign_template_body";

patch(SignTemplateBody.prototype, {
    prepareTemplateData() {
        const [updatedSignItems, Id2UpdatedItem] = super.prepareTemplateData();
        for (const id in updatedSignItems) {
            const signItem = Id2UpdatedItem[id];
            Object.assign(updatedSignItems[id], {
                auto_fill: signItem.auto_fill ?? false,
                by_system: signItem.by_system ?? false,
                key: signItem.key || false,
            });
        }
        return [updatedSignItems, Id2UpdatedItem];
    },
});
