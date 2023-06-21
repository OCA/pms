odoo.define("pos_pms_link.PaymentScreen", function (require) {
    "use strict";

    const PaymentScreen = require("point_of_sale.PaymentScreen");
    const Registries = require("point_of_sale.Registries");
    const session = require("web.session");

    const PosPMSLinkPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            async selectReservation() {
                const {confirmed, payload: newReservation} = await this.showTempScreen(
                    "ReservationListScreen",
                    {
                        reservation: null,
                    }
                );
                if (confirmed) {
                    var self = this;

                    const {confirmed} = await this.showPopup("ConfirmPopup", {
                        title: this.env._t("Pay order with reservation ?"),
                        body: this.env._t(
                            "This operation will add all the products in the order to the reservation. RESERVATION: " +
                                newReservation.name +
                                " PARTNER : " +
                                newReservation.partner_name +
                                " ROOM: " +
                                newReservation.rooms
                        ),
                    });
                    if (confirmed) {
                        var payment_method = {
                            id: self.env.pos.config.pay_on_reservation_method_id[0],
                            name: self.env.pos.config.pay_on_reservation_method_id[1],
                            is_cash_count: false,
                            pos_mercury_config_id: false,
                            use_payment_terminal: false,
                        };
                        self.trigger("new-payment-line", payment_method);
                        this.currentOrder.set_paid_on_reservation(true);
                        this.currentOrder.set_pms_reservation_id(newReservation.id);
                        self.validateOrder(false);
                    }
                }
            }
        };

    Registries.Component.extend(PaymentScreen, PosPMSLinkPaymentScreen);

    return PaymentScreen;
});
