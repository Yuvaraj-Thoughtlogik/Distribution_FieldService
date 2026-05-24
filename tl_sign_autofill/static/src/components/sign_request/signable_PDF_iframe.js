/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { SignablePDFIframe } from "@sign/components/sign_request/signable_PDF_iframe";

patch(SignablePDFIframe.prototype, {

    textareaApplyLineBreak(element) {

        console.log("element", element);

        if (typeof element.value === "undefined") {
            return element.textContent || "";
        }

        element.setAttribute("wrap", "off");

        const strRawValue = element.value || "";

        element.value = "";

        const nEmptyWidth = element.scrollWidth;
        let nLastWrappingIndex = -1;

        strRawValue.split("").forEach((curChar, i) => {

            element.value += curChar;

            if (
                curChar === " " ||
                curChar === "-" ||
                curChar === "+"
            ) {
                nLastWrappingIndex = i;
            }

            if (element.scrollWidth > nEmptyWidth) {

                let buffer = "";

                if (nLastWrappingIndex >= 0) {

                    for (
                        let j = nLastWrappingIndex + 1;
                        j < i;
                        j++
                    ) {
                        buffer += strRawValue.charAt(j);
                    }

                    nLastWrappingIndex = -1;
                }

                buffer += curChar;

                element.value = element.value.substr(
                    0,
                    element.value.length - buffer.length
                );

                element.value += "\n" + buffer;
            }
        });

        element.setAttribute("wrap", "");

        return element.value;
    },
});