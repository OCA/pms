odoo.define("pms.group.reservation.wizard", function (require) {
    "use strict";

    var core = require("web.core");
    var _t = core._t;

    var qweb = core.qweb;

    var ReservationWizard = {
        start: function () {
            // Define a unique uploadId and a callback method
            this.fileUploadID = _.uniqueId("account_bill_file_upload");
            $(window).on(this.fileUploadID, this._onFileUploaded.bind(this));
            return this._super.apply(this, arguments);
        },

        _onNewReservationGroup: function (event) {
            var self = this;

            return this.do_action("pms.pms_reservation_view_tree", {
                on_close: function () {
                    self.reload();
                },
            });
        },
    };
    return ReservationWizard;
});

odoo.define("pms.reservation.group", function (require) {
    "use strict";
    var core = require("web.core");
    var ListController = require("web.ListController");
    var ListView = require("web.ListView");
    var viewRegistry = require("web.view_registry");

    var ReservationGroupRequestListController = ListController.extend(
        ReservationWizard,
        {
            buttons_template: "ReservationGroupList.buttons",
            events: _.extend({}, ListController.prototype.events, {
                "click .o_button_wizard_resevation": "_onNewReservationGroup",
            }),
        }
    );

    var ReservationGroupRequestListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: ReservationGroupRequestListController,
        }),
    });

    viewRegistry.add("reservation_group", ReservationGroupRequestListView);
});
