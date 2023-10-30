/*
##############################################################################
#    License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#    Copyright (C) 2022 Comunitea Servicios Tecnológicos S.L. All Rights Reserved
#    Vicente Ángel Gutiérrez <vicente@comunitea.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
*/

odoo.define("pos_pms_link.db", function (require) {
    "use strict";

    var PosDB = require("point_of_sale.DB");
    var utils = require("web.utils");

    PosDB.include({
        init: function (options) {
            this._super(options);
            this.reservation_sorted = [];
            this.reservation_by_id = {};
            this.reservation_search_string = "";
            this.reservation_id = null;
        },
        get_reservation_by_id: function (id) {
            return this.reservation_by_id[id];
        },
        get_reservations_sorted: function (max_count) {
            max_count = max_count
                ? Math.min(this.reservation_sorted.length, max_count)
                : this.reservation_sorted.length;
            var reservations = [];
            for (var i = 0; i < max_count; i++) {
                reservations.push(this.reservation_by_id[this.reservation_sorted[i]]);
            }
            return reservations;
        },
        search_reservation: function (query) {
            try {
                query = query.replace(
                    /[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,
                    "."
                );
                query = query.replace(/ /g, ".+");
                var re = RegExp("([0-9]+):.*?" + utils.unaccent(query), "gi");
            } catch (e) {
                return [];
            }
            var results = [];
            for (var i = 0; i < this.limit; i++) {
                var r = re.exec(this.reservation_search_string);
                if (r) {
                    var id = Number(r[1]);
                    results.push(this.get_reservation_by_id(id));
                } else {
                    break;
                }
            }
            return results;
        },
        _reservation_search_string: function (reservation) {
            var str = reservation.name || "";
            var room_str = reservation.rooms || "";
            var partner_str = reservation.partner_name || "";
            str =
                String(reservation.id) +
                ":" +
                str.replace(":", "").replace(/\n/g, " ") +
                ":" +
                room_str.replace(":", "").replace(/\n/g, " ") +
                ":" +
                partner_str.replace(":", "").replace(/\n/g, " ") +
                "\n";
            return str;
        },
        add_reservations: function (reservations) {
            var updated_count = 0;
            var reservation;
            for (var i = 0, len = reservations.length; i < len; i++) {
                reservation = reservations[i];

                if (!this.reservation_by_id[reservation.id]) {
                    this.reservation_sorted.push(reservation.id);
                }
                this.reservation_by_id[reservation.id] = reservation;

                updated_count += 1;
            }

            if (updated_count) {
                this.reservation_search_string = "";
                this.reservation_by_barcode = {};

                for (var id in this.reservation_by_id) {
                    reservation = this.reservation_by_id[id];

                    if (reservation.barcode) {
                        this.reservation_by_barcode[reservation.barcode] = reservation;
                    }
                    this.reservation_search_string += this._reservation_search_string(
                        reservation
                    );
                }

                this.reservation_search_string = utils.unaccent(
                    this.reservation_search_string
                );
            }
            return updated_count;
        },
    });
    return PosDB;
});
