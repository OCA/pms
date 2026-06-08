// Copyright (c) 2021 Gray Matter Logic
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import {registry} from "@web/core/registry";

registry.category("web_tour.tours").add("property_load_homepage", {
    url: "/property",
    test: true,
    steps: () => [
        {
            content: "Check Property",
            trigger: ".oe_website_sale",
        },
    ],
});

registry.category("web_tour.tours").add("property_search_homepage", {
    url: "/property?date_range=04/18/2022-04/18/2022&guest_select=2",
    test: true,
    steps: () => [
        {
            content: "Check Property",
            trigger: ".oe_website_sale",
        },
    ],
});
