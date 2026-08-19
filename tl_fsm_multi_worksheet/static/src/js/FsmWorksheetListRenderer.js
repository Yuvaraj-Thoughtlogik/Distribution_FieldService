/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";

export class FsmWorksheetListController extends ListController {
    async openRecord(record) {
        return this.actionService.doActionButton({
            type: "object",
            name: "open_fsm_worksheet",
            resModel: record.resModel,
            resId: record.resId,
            resIds: record.resIds,
            context: record.context,
            onClose: () => record.model.root.load(),
        });
    }
}

registry.category("views").add("fsm_worksheet_list", {
    ...listView,
    Controller: FsmWorksheetListController,
});