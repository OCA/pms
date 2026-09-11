/** @odoo-module */

import {ListController} from "@web/views/list/list_controller";
import {listView} from "@web/views/list/list_view";
import {registry} from "@web/core/registry";

export class InventoryRuleListController extends ListController {
    /**
     * Open the bulk change wizard.
     *
     * It lives in a button of the control panel and not in a menu of its own
     * because it belongs to this screen, and not in the header of the list
     * either: header buttons are only rendered while records are selected,
     * and creating rules in bulk needs no selection.
     */
    onClickMassiveChanges() {
        return this.actionService.doAction(
            "pms.action_wizard_massive_inventory_changes",
            {onClose: () => this.model.load()}
        );
    }
}

export const InventoryRuleListView = {
    ...listView,
    Controller: InventoryRuleListController,
    buttonTemplate: "pms.InventoryRuleListView.Buttons",
};

registry.category("views").add("pms_inventory_rule_list", InventoryRuleListView);
