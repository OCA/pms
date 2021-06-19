odoo.define("booking.engine.tree", function (require) {
    "use strict";
    var ListController = require("web.ListController");
    var ListView = require("web.ListView");
    var viewRegistry = require("web.view_registry");

    function renderBookingEngineButton() {
        if (this.$buttons) {
            var self = this;
            this.$buttons.on("click", ".o_button_booking_engine", function () {
                self.do_action({
                    name: "Booking Engine",
                    type: "ir.actions.act_window",
                    res_model: "pms.booking.engine",
                    target: "new",
                    views: [[false, "form"]],
                    context: {is_modal: true},
                });
            });
        }
    }

    var BookingEngineRequestListController = ListController.extend({
        start: function () {
            return this._super.apply(this, arguments);
        },
        buttons_template: "BookingEngineRequestListView.buttons",
        renderButtons: function () {
            this._super.apply(this, arguments);
            renderBookingEngineButton.apply(this, arguments);
        },
    });

    var BookingEngineRequestListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: BookingEngineRequestListController,
        }),
    });

    viewRegistry.add("pms_booking_engine_request_tree", BookingEngineRequestListView);
});
