/** @odoo-module **/

import PosComponent from "point_of_sale.PosComponent";
import Registries from "point_of_sale.Registries";

class ReservationDetailsEdit extends PosComponent {
    setup() {
        super.setup();
        const reservation = this.props.reservation;
        // onMounted(() => {
        //     this.env.bus.on("save-reservation", this, this.saveChanges);
        // });
        // onWillUnmount(() => {
        //     this.env.bus.off("save-reservation", this);
        // });
    }
}

ReservationDetailsEdit.template = "ReservationDetailsEdit";

Registries.Component.add(ReservationDetailsEdit);
