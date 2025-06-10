/** @odoo-module **/

import PosComponent from "point_of_sale.PosComponent";
import Registries from "point_of_sale.Registries";

class ReservationLine extends PosComponent {
    get highlight() {
        return this.props.reservation !== this.props.selectedReservation
            ? ""
            : "highlight";
    }
}

ReservationLine.template = "ReservationLine";

Registries.Component.add(ReservationLine);
