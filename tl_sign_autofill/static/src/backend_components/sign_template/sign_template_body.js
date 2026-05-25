/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { SignTemplateBody } from "@sign/backend_components/sign_template/sign_template_body";

patch(SignTemplateBody.prototype, {

    prepareTemplateData() {

        const updatedSignItems = {};
        const Id2UpdatedItem = {};

        const items = this.iframe?.signItems ?? {};

        for (const page in items) {

            for (const id in items[page]) {

                const signItem = items[page][id].data;

                if (signItem.updated) {

                    Id2UpdatedItem[id] = signItem;

                    const responsible = signItem.responsible;

                    updatedSignItems[id] = {
                        type_id: signItem.type_id[0],
                        required: signItem.required,
                        name: signItem.placeholder || signItem.name,
                        alignment: signItem.alignment,
                        option_ids: signItem.option_ids,
                        responsible_id: responsible,
                        page: page,
                        posX: signItem.posX,
                        posY: signItem.posY,
                        width: signItem.width,
                        height: signItem.height,
                        radio_set_id: signItem.radio_set_id,

                        // CUSTOM FIELD
                        auto_fill: signItem.auto_fill ?? false,
                        by_system: signItem.by_system ?? false,
                        key: signItem.key,
                    };

                    if (id < 0) {
                        updatedSignItems[id]["transaction_id"] = id;
                    }
                }
            }
        }

        return [updatedSignItems, Id2UpdatedItem];
    },

});