odoo.define("pms_website_sale.pms_property", function (require) {
    "use strict";

    const publicWidget = require("web.public.widget");

    publicWidget.registry.pmsProperty = publicWidget.Widget.extend({
        selector: ".oe_property_filtter",
        jsLibs: [
            "/web/static/lib/daterangepicker/daterangepicker.js",
            "/web/static/src/js/libs/daterangepicker.js",
        ],
        cssLibs: ["/web/static/lib/daterangepicker/daterangepicker.css"],
        start: function () {
            var def = this._super.apply(this, arguments);
            console.log(
                "/////////////111111111111//////",
                $(".field_date_range_filtter")
            );
            $(".field_date_range_filtter").daterangepicker({
                autoApply: true,
                mindate: new moment(),
            });

            return def;
        },
    });
});
