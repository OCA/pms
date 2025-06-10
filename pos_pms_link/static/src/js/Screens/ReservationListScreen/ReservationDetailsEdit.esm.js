/** @odoo-module **/

import PosComponent from "point_of_sale.PosComponent";
import Registries from "point_of_sale.Registries";

class ReservationDetailsEdit extends PosComponent {}

ReservationDetailsEdit.template = "ReservationDetailsEdit";

Registries.Component.add(ReservationDetailsEdit);
