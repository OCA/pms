odoo.define("pos_pms_link.OrderReceipt", function (require) {
    "use strict";

    const OrderReceipt = require("point_of_sale.OrderReceipt");
    const Registries = require("point_of_sale.Registries");
    const session = require("web.session");

    const PosPMSLinkOrderReceipt = (OrderReceipt) =>
        class extends OrderReceipt {
            get paid_on_reservation() {
                return this.receiptEnv.receipt.paid_on_reservation;
            }
            get reservation_name() {
                return (
                    this.env.pos.db.get_reservation_by_id(
                        this.receiptEnv.receipt.pms_reservation_id
                    ).partner_name || ""
                );
            }
        };

    Registries.Component.extend(OrderReceipt, PosPMSLinkOrderReceipt);

    return OrderReceipt;
});
