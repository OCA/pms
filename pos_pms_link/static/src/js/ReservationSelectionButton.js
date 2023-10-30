odoo.define("pos_pms_link.ReservationSelectionButton", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const ProductScreen = require("point_of_sale.ProductScreen");
    const {useListener} = require("web.custom_hooks");
    const Registries = require("point_of_sale.Registries");
    const {Gui} = require("point_of_sale.Gui");
    var core = require("web.core");
    var QWeb = core.qweb;

    var _t = core._t;

    class ReservationSelectionButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener("click", this.onClick);
        }
        get currentOrder() {
            return this.env.pos.get_order();
        }
        async onClick() {
            const {
                confirmed,
                payload: newReservation,
            } = await this.showTempScreen("ReservationListScreen", {reservation: null});
            if (confirmed) {
                this.currentOrder.add_reservation_services(newReservation);
            }
        }
    }
    ReservationSelectionButton.template = "ReservationSelectionButton";

    ProductScreen.addControlButton({
        component: ReservationSelectionButton,
        condition: function () {
            return true;
        },
    });

    Registries.Component.add(ReservationSelectionButton);

    return ReservationSelectionButton;
});
