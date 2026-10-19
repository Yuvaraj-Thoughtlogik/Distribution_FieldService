import { patch } from "@web/core/utils/patch";
import { SignablePDFIframe } from "@sign/components/sign_request/signable_PDF_iframe";

patch(SignablePDFIframe.prototype, {
    /**
     * Read-only (system filled) items are rendered as non-textarea elements:
     * fall back on their text content instead of the textarea value.
     */
    textareaApplyLineBreak(element) {
        if (typeof element.value === "undefined") {
            return element.textContent || "";
        }
        return super.textareaApplyLineBreak(element);
    },
});
