// Copyright (c) 2021 Gray Matter Logic
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
(function () {
    "use strict";

    function init() {
        var addGuestBtn = document.getElementById("pms_add_guest");
        if (!addGuestBtn) {
            return;
        }

        var bookingModal = document.getElementById("pmsBookingModal");
        var propertyId = bookingModal && bookingModal.dataset.propertyId;
        var guestList = document.getElementById("pms_guest_list");
        var startInput = document.getElementById("date_start");
        var endInput = document.getElementById("date_end");
        var availStatus = document.getElementById("pms_availability_status");
        var addToCartBtn = document.getElementById("pmsAddToCart");

        // Set minimum date to today
        var today = new Date().toISOString().split("T")[0];
        if (startInput) {
            startInput.min = today;
        }
        if (endInput) {
            endInput.min = today;
        }

        function jsonRpc(url, params) {
            return fetch(url, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({jsonrpc: "2.0", method: "call", params: params}),
            })
                .then(function (r) {
                    return r.json();
                })
                .then(function (data) {
                    return data.result;
                });
        }

        function checkAvailability() {
            var start = startInput && startInput.value;
            var end = endInput && endInput.value;
            if (!start || !end || !propertyId || !availStatus) {
                return;
            }
            if (start >= end) {
                availStatus.innerHTML =
                    '<span class="text-danger">Check-out must be after check-in</span>';
                return;
            }
            availStatus.innerHTML = '<span class="text-muted">Checking…</span>';
            jsonRpc("/property/" + propertyId + "/check_availability", {
                date_start: start,
                date_end: end,
            })
                .then(function (result) {
                    if (result && result.available) {
                        availStatus.innerHTML =
                            '<span class="text-success">' +
                            '<i class="fa fa-check-circle"></i> Available</span>';
                    } else {
                        availStatus.innerHTML =
                            '<span class="text-danger">' +
                            '<i class="fa fa-times-circle"></i> Not available</span>';
                    }
                })
                .catch(function () {
                    availStatus.innerHTML =
                        '<span class="text-muted">Could not check availability</span>';
                });
        }

        if (startInput) {
            startInput.addEventListener("change", function () {
                if (endInput && endInput.value && endInput.value <= startInput.value) {
                    endInput.value = "";
                }
                if (endInput) {
                    endInput.min = startInput.value;
                }
                checkAvailability();
            });
        }
        if (endInput) {
            endInput.addEventListener("change", checkAvailability);
        }

        function reindexGuests() {
            var rows = guestList.querySelectorAll(".pms-guest-row");
            rows.forEach(function (row, i) {
                var nameInput = row.querySelector("input[data-guest-field='name']");
                var phoneInput = row.querySelector("input[data-guest-field='phone']");
                var emailInput = row.querySelector("input[data-guest-field='email']");
                if (nameInput) {
                    nameInput.name = "guest_name_" + i;
                }
                if (phoneInput) {
                    phoneInput.name = "guest_phone_" + i;
                }
                if (emailInput) {
                    emailInput.name = "guest_email_" + i;
                }
            });
        }

        function collectGuests() {
            var guests = [];
            guestList.querySelectorAll(".pms-guest-row").forEach(function (row) {
                var nameInput = row.querySelector("input[data-guest-field='name']");
                var phoneInput = row.querySelector("input[data-guest-field='phone']");
                var emailInput = row.querySelector("input[data-guest-field='email']");
                var name = (nameInput && nameInput.value.trim()) || "";
                if (name) {
                    guests.push({
                        name: name,
                        phone: (phoneInput && phoneInput.value.trim()) || "",
                        email: (emailInput && emailInput.value.trim()) || "",
                    });
                }
            });
            return guests;
        }

        if (addGuestBtn && guestList) {
            addGuestBtn.addEventListener("click", function () {
                var maxGuests = parseInt(addGuestBtn.dataset.max || "0", 10);
                var currentRows = guestList.querySelectorAll(".pms-guest-row").length;
                if (maxGuests > 0 && currentRows >= maxGuests) {
                    window.alert(
                        "This property accepts a maximum of " + maxGuests + " guest(s)."
                    );
                    return;
                }
                var idx = currentRows;
                var row = document.createElement("div");
                row.className = "pms-guest-row row mb-2 align-items-center";
                row.innerHTML =
                    '<div class="col-md-4">' +
                    '<input type="text" class="form-control"' +
                    ' name="guest_name_' +
                    idx +
                    '" data-guest-field="name" placeholder="Full Name" required />' +
                    "</div>" +
                    '<div class="col-md-3">' +
                    '<input type="tel" class="form-control"' +
                    ' name="guest_phone_' +
                    idx +
                    '" data-guest-field="phone" placeholder="Phone" />' +
                    "</div>" +
                    '<div class="col-md-4">' +
                    '<input type="email" class="form-control"' +
                    ' name="guest_email_' +
                    idx +
                    '" data-guest-field="email" placeholder="Email" />' +
                    "</div>" +
                    '<div class="col-md-1">' +
                    '<button type="button" class="btn btn-outline-danger btn-sm pms-remove-guest"' +
                    ' title="Remove guest">' +
                    '<i class="fa fa-times"></i>' +
                    "</button>" +
                    "</div>";
                row.querySelector(".pms-remove-guest").addEventListener(
                    "click",
                    function () {
                        row.remove();
                        reindexGuests();
                    }
                );
                guestList.appendChild(row);
            });
        }

        if (addToCartBtn && propertyId) {
            addToCartBtn.addEventListener("click", function () {
                var form = document.getElementById("pmsBookingForm");
                if (form && !form.reportValidity()) {
                    return;
                }
                var reservationTypeEl = document.getElementById("reservation_type_id");
                var guests = collectGuests();
                if (!guests.length) {
                    window.alert("Please add at least one guest.");
                    return;
                }
                addToCartBtn.disabled = true;
                jsonRpc("/property/" + propertyId + "/add_to_cart", {
                    date_start: startInput && startInput.value,
                    date_end: endInput && endInput.value,
                    reservation_type_id:
                        reservationTypeEl && parseInt(reservationTypeEl.value, 10),
                    guests: guests,
                })
                    .then(function (result) {
                        if (result && result.redirect) {
                            window.location.href = result.redirect;
                        } else {
                            window.alert(
                                (result && result.error) || "An error occurred."
                            );
                            addToCartBtn.disabled = false;
                        }
                    })
                    .catch(function () {
                        window.alert("Could not add to cart. Please try again.");
                        addToCartBtn.disabled = false;
                    });
            });
        }
    }

    // Execute init whether DOM is still loading or already ready
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
