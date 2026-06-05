odoo.define("pms_website_sale.pms_website_sale_tour", function (require) {
    "use strict";

    var tour = require("web_tour.tour");

    // This tour relies on data created on the Python test.
    tour.register(
        "property_load_homepage",
        {
            test: true,
            url: "/property",
        },
        [
            {
                content: "Check Property",
                trigger: ".oe_website_sale",
            },
        ]
    );
    tour.register(
        "property_search_homepage",
        {
            test: true,
            url: "/property?date_range=04/18/2022-04/18/2022&guest_select=2",
        },
        [
            {
                content: "Check Property",
                trigger: ".oe_website_sale",
            },
        ]
    );
});
