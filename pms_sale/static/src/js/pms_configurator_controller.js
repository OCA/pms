odoo.define("pms_sale.PMSConfiguratorFormController", function (require) {
    "use strict";

    var FormController = require("web.FormController");

    /**
     * This controller is overridden to allow configuring sale_order_lines through a popup
     * window when a product with 'reservation_ok' is selected.
     *
     * This allows keeping an editable list view for sales order and remove the noise of
     * those 2 fields ('property_id' + 'reservation_id')
     */
    var PMSConfiguratorFormController = FormController.extend({

        /**
         * We let the regular process take place to allow the validation of the required fields
         * to happen.
         *
         * Then we can manually close the window, providing event information to the caller.
         *
         * @override
         */
        saveRecord: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                var state = self.renderer.state.data;
                var guest_ids = [[5, 0, 0]];
                _.each(state.guest_ids.data, function (data) {
                    if (data.data && data.data.name) {
                        if (data.data.partner_id) {
                            data.data.partner_id = data.data.partner_id.data.id;
                        }
                        guest_ids.push([0, 0, data.data]);
                    }
                });
                self.do_action({
                    type: "ir.actions.act_window_close",
                    infos: {
                        ReservationConfiguration: {
                            property_id: {id: state.property_id.data.id},
                            reservation_id: {id: state.reservation_id.data.id},
                            start: state.start,
                            stop: state.stop,
                            no_of_guests: state.no_of_guests,
                            product_uom_qty: state.duration,
                            guest_ids: guest_ids,
                        },
                    },
                });
            });
        },
    });

    return PMSConfiguratorFormController;
});
