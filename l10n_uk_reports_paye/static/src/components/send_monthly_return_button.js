/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

import { Component } from "@odoo/owl";

export class SendPAYEFPSReturnButton extends Component {
    static template = "l10n_uk_paye.SendPAYEFPSReturn";
    static props = { ...standardWidgetProps };

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action")
        this.title = _t("Send PAYE FPS return to HMRC")
    }

    async sendMonthlyReturn() {

        this.env.services.ui.block();

        try {
            await this.orm.call("paye_fps_return_wizard", "action_send_paye_fps_return", [
                null,
                this.props.record.data.date_from,
                this.props.record.data.date_to,
                this.props.record.data.employment_status,
                this.props.record.data.employer_verification,
                this.props.record.data.inactivity_indicator,
                this.props.record.data.hmrc_paye_password
            ]);
            this.actionService.doAction({ type: "ir.actions.act_window_close" });
        }
        finally {
            this.env.services.ui.unblock();
        }
    }
}

export const sendPAYEFPSReturnButton = {
    component: SendPAYEFPSReturnButton,
}

registry.category("view_widgets").add("send_paye_fps_return_button", sendPAYEFPSReturnButton);
