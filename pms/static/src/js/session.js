odoo.define("pms.session", function (require) {
    "use strict";

    var Session = require("web.Session");
    var utils = require("web.utils");
    var modules = odoo._modules;

    var inherited_Session = Session.extend({
        // TODO: require test and debug
        setPmsProperties: function (pms_main_property_id, pms_property_ids) {
            var hash = $.bbq.getState();
            hash.pms_pids = pms_property_ids
                .sort(function (a, b) {
                    if (a === pms_main_property_id) {
                        return -1;
                    } else if (b === pms_main_property_id) {
                        return 1;
                    }
                    return a - b;
                })
                .join(",");
            utils.set_cookie("pms_pids", hash.pms_pids || String(pms_main_property_id));
            $.bbq.pushState({pms_pids: hash.pms_pids}, 0);
            location.reload();
        },
    });

    var pms_session = new inherited_Session(undefined, undefined, {
        modules: modules,
        use_cors: false,
    });
    pms_session.is_bound = pms_session.session_bind();

    return pms_session;
});
