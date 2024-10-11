/** @odoo-module **/

import Registries from "point_of_sale.Registries";
import PosComponent from "point_of_sale.PosComponent";
import ProductScreen from "point_of_sale.ProductScreen";
import {_t} from "web.core";

class ReservationSelectionButton extends PosComponent {
    get currentOrder() {
        return this.env.pos.get_order();
    }

    async onClick() {
        const {confirmed, payload: newReservation} = await this.showTempScreen(
            "ReservationListScreen",
            {reservation: null}
        );
        if (confirmed) {
            this.currentOrder.add_reservation_services(newReservation);
            console.log(newReservation);
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
