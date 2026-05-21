/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PDFIframe } from "@sign/components/sign_request/PDF_iframe";

patch(PDFIframe.prototype, {

    getContext(signItem) {

        const result = super.getContext(signItem);

        result.by_system = Boolean(signItem.by_system);

        result.readonly = result.readonly && result.by_system;

        if (result.by_system) {
            result.classes = result.classes
                .replace("o_sign_sign_item_default", "")
                .replace("o_sign_sign_item_required", "");
        }

        return result;
    },

});