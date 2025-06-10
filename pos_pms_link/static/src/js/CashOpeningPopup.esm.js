/** @odoo-module **/

import AbstractAwaitablePopup from "point_of_sale.AbstractAwaitablePopup";
import CashOpeningPopup from "point_of_sale.CashOpeningPopup";
import Registries from "point_of_sale.Registries";

const PosPmsLinkCashOpeningPopup = (CashOpeningPopup) =>
    class extends CashOpeningPopup {
        async confirm() {
            this.env.pos.pos_session.cash_register_balance_start =
                this.state.openingCash;
            this.env.pos.pos_session.state = "opened";
            var context = this.env.session.user_context;
            var chasier = this.env.pos.get_cashier();
            context.cashier = chasier.name;
            this.rpc({
                model: "pos.session",
                method: "set_cashbox_pos",
                args: [
                    this.env.pos.pos_session.id,
                    this.state.openingCash,
                    this.state.notes,
                ],
                context: context,
            });
            AbstractAwaitablePopup.prototype.confirm.apply(this, arguments);
        }
    };

Registries.Component.extend(CashOpeningPopup, PosPmsLinkCashOpeningPopup);
