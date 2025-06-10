/** @odoo-module **/

import CashMovePopup from "point_of_sale.CashMovePopup";
import Registries from "point_of_sale.Registries";

const PosPmsLinkCashMovePopup = (CashMovePopup) =>
    class extends CashMovePopup {
        setup() {
            super.setup();
            this.state.partner = null;
            this.state.no_partner_cash_move = false;
        }

        showPartnerButton() {
            var cash_move_partner =
                this.env.pos &&
                this.env.pos.config &&
                this.env.pos.config.cash_control &&
                this.env.pos.config.cash_move_partner;
            return cash_move_partner;
        }

        async onClickPartner() {
            // IMPROVEMENT: This code snippet is very similar to selectPartner of PaymentScreen.
            const currentPartner = this.state.partner;
            const {confirmed, payload: newPartner} = await this.showPopup(
                "PartnerListPopup",
                {partner: currentPartner}
            );
            if (confirmed) {
                this.state.partner = newPartner;
            }
        }

        get isLongName() {
            return this.state.partner && this.state.partner.name.length > 10;
        }

        getPayload() {
            var res = super.getPayload();
            res.partner = this.state.partner;
            return res;
        }

        confirm() {
            if (this.showPartnerButton()) {
                if (this.state.no_partner_cash_move) {
                    if (!this.state.inputReason) {
                        this.state.inputHasError = true;
                        this.errorMessage = this.env._t("Please enter a reason.");
                        return;
                    }
                } else if (!this.state.partner) {
                    this.state.inputHasError = true;
                    this.errorMessage = this.env._t(
                        "Select a partner before confirming."
                    );
                    return;
                }
            }
            return super.confirm();
        }
        onClickNoPartnerCashMove() {
            this.state.no_partner_cash_move = !this.state.no_partner_cash_move;
            var $button = $("#cash-partner");
            if (this.state.no_partner_cash_move) {
                this.state.partner = null;
                if ($button) {
                    $button.css("display", "none");
                }
            } else if ($button) {
                $button.css("display", "block");
            }
            this.state.inputHasError = false;
        }
    };

Registries.Component.extend(CashMovePopup, PosPmsLinkCashMovePopup);
