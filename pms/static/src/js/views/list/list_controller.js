odoo.define("pms.ListController", function (require) {
    "use strict";
    /*
     * Pms
     * GNU Public License
     * Alexandre Díaz <dev@redneboa.es>
     */

    var ListController = require("web.ListController");
    var Core = require("web.core");

    var _t = Core._t;

    ListController.include({
        renderButtons: function () {
            this._super.apply(this, arguments); // Sets this.$buttons
            var self = this;
            if (this.modelName === "pms.reservation") {
                this.$buttons.append(
                    "<button class='btn btn-sm oe_open_reservation_wizard oe_highlight' type='button'>" +
                        _t("Open Wizard") +
                        "</button>"
                );
                this.$buttons
                    .find(".oe_open_reservation_wizard")
                    .on("click", function () {
                        self.do_action("pms.open_wizard_reservations");
                    });
            }
        },
    });
});
