odoo.define("pms.AbstractWebClient", function (require) {
    "use strict";

    var AbstractWebClient = require("web.AbstractWebClient");
    var session = require("web.session");
    var utils = require("web.utils");

    return AbstractWebClient.include({
        start: function () {
            var state = $.bbq.getState();
            var current_pms_property_id =
                session.user_pms_properties.current_pms_property[0];
            if (!state.pms_pids) {
                state.pms_pids = utils.get_cookie("pms_pids")
                    ? utils.get_cookie("pms_pids")
                    : String(current_pms_property_id);
            }
            var statePmsPropertyIDS = _.map(state.pms_pids.split(","), function (
                pms_pid
            ) {
                return parseInt(pms_pid, 10);
            });
            var userPmsPropertyIDS = _.map(
                session.user_pms_properties.allowed_pms_properties,
                function (pms_property) {
                    return pms_property[0];
                }
            );
            // Check that the user has access to all the companies
            if (!_.isEmpty(_.difference(statePmsPropertyIDS, userPmsPropertyIDS))) {
                state.pms_pids = String(current_pms_property_id);
                statePmsPropertyIDS = [current_pms_property_id];
            }
            session.user_context.allowed_pms_property_ids = statePmsPropertyIDS;

            return this._super.apply(this, arguments);
        },
    });
});
