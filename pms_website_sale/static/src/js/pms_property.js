// Copyright (c) 2021 Gray Matter Logic
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
(function () {
    "use strict";

    function initPropertyFilter() {
        const dateInput = document.querySelector(".field_date_range_filtter");
        if (!dateInput) {
            return;
        }
        if (
            window.jQuery &&
            window.jQuery.fn &&
            window.jQuery.fn.daterangepicker &&
            window.moment
        ) {
            window.jQuery(dateInput).daterangepicker({
                autoApply: true,
                minDate: window.moment(),
            });
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initPropertyFilter);
    } else {
        initPropertyFilter();
    }
})();
