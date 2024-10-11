/** @odoo-module **/

import OrderReceipt from "point_of_sale.OrderReceipt";
import Registries from "point_of_sale.Registries";

const PosPMSLinkOrderReceipt = (OrderReceipt) =>
    class extends OrderReceipt {
        get paid_on_reservation() {
            return this._receiptEnv.receipt.paid_on_reservation;
        }

        get reservation_name() {
            return (
                this.env.pos.db.get_reservation_by_id(
                    this._receiptEnv.receipt.pms_reservation_id
                ).partner_name || ""
            );
        }
    };

Registries.Component.extend(OrderReceipt, PosPMSLinkOrderReceipt);
