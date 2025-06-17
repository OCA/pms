/** @odoo-module **/
import CashMoveButton from "point_of_sale.CashMoveButton";
import Registries from "point_of_sale.Registries";
import {renderToString} from "@web/core/utils/render";

const PosPmsLinkCashMoveButton = (CashMoveButton) =>
    class extends CashMoveButton {
        async onClick() {
            const {confirmed, payload} = await this.showPopup("CashMovePopup");
            if (!confirmed) return;
            const {type, amount, reason, partner} = payload;
            const translatedType = this.env._t(type);
            const formattedAmount = this.env.pos.format_currency(amount);
            if (!amount) {
                return this.showNotification(
                    _.str.sprintf(
                        this.env._t("Cash in/out of %s is ignored."),
                        formattedAmount
                    ),
                    3000
                );
            }
            const cashier = this.env.pos.get_cashier();
            var context = this.env.session.user_context;
            // Pasar el nombre del cajero y el id del partner al método try_cash_in_out del modelo pos.session
            context.cashier = cashier.name;
            context.partner_id = partner ? partner.id : false;
            const extras = {formattedAmount, translatedType};
            await this.rpc({
                model: "pos.session",
                method: "try_cash_in_out",
                args: [this.env.pos.pos_session.id, type, amount, reason, extras],
                context: context,
            });
            if (this.env.proxy.printer) {
                const renderedReceipt = renderToString(
                    "point_of_sale.CashMoveReceipt",
                    {
                        _receipt: this._getReceiptInfo({
                            ...payload,
                            translatedType,
                            formattedAmount,
                        }),
                    }
                );
                const printResult = await this.env.proxy.printer.print_receipt(
                    renderedReceipt
                );
                if (!printResult.successful) {
                    this.showPopup("ErrorPopup", {
                        title: printResult.message.title,
                        body: printResult.message.body,
                    });
                }
            }
            this.showNotification(
                _.str.sprintf(
                    this.env._t("Successfully made a cash %s of %s."),
                    type,
                    formattedAmount
                ),
                3000
            );
        }
    };

Registries.Component.extend(CashMoveButton, PosPmsLinkCashMoveButton);
