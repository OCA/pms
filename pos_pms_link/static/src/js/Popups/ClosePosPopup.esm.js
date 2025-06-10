/** @odoo-module **/

import ClosePosPopup from "point_of_sale.ClosePosPopup";
import Registries from "point_of_sale.Registries";

const PosPmsLinkClosePosPopup = (ClosePosPopup) =>
    class extends ClosePosPopup {
        async closeSession() {
            var context = this.env.session.user_context;
            var cashier = this.env.pos.get_cashier();
            context.cashier = cashier.name;
            this.env.session.userContext = context;
            super.closeSession();
        }
    };

Registries.Component.extend(ClosePosPopup, PosPmsLinkClosePosPopup);
