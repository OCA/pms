odoo.define("pos_pms_link.ReservationDetailsEdit", function (require) {
    "use strict";

    const {_t} = require("web.core");
    const {getDataURLFromFile} = require("web.utils");
    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");

    class ReservationDetailsEdit extends PosComponent {
        constructor() {
            super(...arguments);
            const reservation = this.props.reservation;
        }
        mounted() {
            this.env.bus.on("save-reservation", this, this.saveChanges);
        }
        willUnmount() {
            this.env.bus.off("save-reservation", this);
        }
        /**
         * Save to field `changes` all input changes from the form fields.
         */
        captureChange(event) {
            this.changes[event.target.name] = event.target.value;
        }
        saveChanges() {
            const processedChanges = {};
            for (const [key, value] of Object.entries(this.changes)) {
                if (this.intFields.includes(key)) {
                    processedChanges[key] = parseInt(value) || false;
                } else {
                    processedChanges[key] = value;
                }
            }
            if (
                (!this.props.reservation.name && !processedChanges.name) ||
                processedChanges.name === ""
            ) {
                return this.showPopup("ErrorPopup", {
                    title: _t("A Customer Name Is Required"),
                });
            }
            processedChanges.id = this.props.reservation.id || false;
            this.trigger("save-changes", {processedChanges});
        }
    }
    ReservationDetailsEdit.template = "ReservationDetailsEdit";

    Registries.Component.add(ReservationDetailsEdit);

    return ReservationDetailsEdit;
});
