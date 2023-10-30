odoo.define("pos_pms_link.ReservationLine", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");

    class ReservationLine extends PosComponent {
        get highlight() {
            return this.props.reservation !== this.props.selectedReservation
                ? ""
                : "highlight";
        }
    }
    ReservationLine.template = "ReservationLine";

    Registries.Component.add(ReservationLine);

    return ReservationLine;
});
