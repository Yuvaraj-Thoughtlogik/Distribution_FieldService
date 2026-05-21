/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { shallowEqual } from "@web/core/utils/objects";
import { SignTemplateIframe } from "@sign/backend_components/sign_template/sign_template_iframe";
import { SignItemCustomPopover } from "@sign/backend_components/sign_template/sign_item_custom_popover";


patch(SignTemplateIframe.prototype, {

    updateSignItem(signItem, data) {

        if (signItem.data.type === "radio") {
            return this.updateRadioButton(signItem.data.id, data);
        }

        const changes = Object.keys(data).reduce((changes, key) => {

            if (key in signItem.data || key === "auto_fill" || key === "key" || key === "by_system") {

                if (Array.isArray(data[key])) {

                    if (!shallowEqual(signItem.data[key], data[key])) {
                        changes[key] = data[key];
                    }

                } else if (signItem.data[key] !== data[key]) {
                    changes[key] = data[key];
                }
            }

            return changes;

        }, {});
        if (Object.keys(changes).length) {
            const pageNumber = signItem.data.page;
            const page = this.getPageContainer(pageNumber);
            signItem.el.parentElement.removeChild(signItem.el);

            const newData = {
                ...signItem.data,
                ...changes,
                updated: true,
            };
            this.signItems[pageNumber][newData.id] = {
                data: newData,
                el: this.renderSignItem(newData, page),
            };

            this.refreshSignItems();
            this.currentRole = newData.responsible;
            this.saveChanges();
        }
    },

    async openSignItemPopup(signItem) {
        const shouldOpenNewPopover = !(signItem.data.id in this.closePopoverFns);
        this.closePopover();
        if (shouldOpenNewPopover) {
            if (signItem.data.id in this.negativeIds) {
                await this.negativeIds[signItem.data.id];
            }
            const header_title = signItem.data.type === "radio" ? "Radio Button" : signItem.data.type_id?.[1] || signItem.data.name;
            const closeFn = this.popover.add(
                signItem.el,
                SignItemCustomPopover,
                {
                    debug: this.env.debug,
                    responsible: signItem.data.responsible,
                    roles: this.signRolesById,
                    alignment: signItem.data.alignment,
                    required: signItem.data.required,
                    auto_fill: signItem.data.auto_fill ?? false,
                    by_system: signItem.data.by_system ?? false,
                    key: signItem.data.key,
                    header_title: header_title,
                    placeholder: signItem.data.placeholder,
                    id: signItem.data.id,
                    type: signItem.data.type,
                    option_ids: signItem.data.option_ids,
                    num_options: this.getSignItemById(signItem.data.id).data.num_options,
                    radio_set_id: signItem.data.radio_set_id,
                    onValidate: (data) => {
                        this.updateSignItem(signItem, data);
                        this.closePopover();
                    },
                    onDelete: () => {
                        this.closePopover();
                        this.deleteSignItem(signItem);
                    },
                    onClose: () => {
                        this.closePopover();
                    },
                    updateSelectionOptions: (ids) => this.updateSelectionOptions(ids),
                    updateRoles: (id) => this.updateRoles(id),
                },
                {
                    position: "right",
                    onClose: () => {
                        this.closePopoverFns = {};
                    },
                    closeOnClickAway: (target) => !target.closest(".modal"),
                    popoverClass: "sign-popover",
                }
            );
            this.closePopoverFns[signItem.data.id] = {
                close: closeFn,
                signItem,
            };
        }
    }

});