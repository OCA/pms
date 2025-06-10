/** @odoo-module **/
import Chrome from "point_of_sale.Chrome";
import Registries from "point_of_sale.Registries";

const PosPmsLinkChrome = (Chrome) =>
    class extends Chrome {
        get headerButtonIsShown() {
            var showButton = super.headerButtonIsShown;
            var close_session_allowed = this.env.pos.config.close_session_allowed;
            return close_session_allowed ? close_session_allowed : showButton;
        }
        showCashMoveButton() {
            var showButton = super.showCashMoveButton();
            var cash_in_out_allowed =
                this.env.pos &&
                this.env.pos.config &&
                this.env.pos.config.cash_control &&
                this.env.pos.config.cash_in_out_allowed;
            return cash_in_out_allowed ? cash_in_out_allowed : showButton;
        }
    };

Registries.Component.extend(Chrome, PosPmsLinkChrome);
