/** @odoo-module **/
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

import PosDB from "point_of_sale.DB";
import {patch, unaccent} from "web.utils";

patch(PosDB.prototype, "pos_pms_link.PosDB", {
    init(options) {
        this._super(options);
        this.reservation_sorted = [];
        this.reservation_by_id = {};
        // This.reservation_search_string = "";
        this.reservation_search_strings = {};
        this.reservation_id = null;
    },
    get_reservation_by_id(id) {
        return this.reservation_by_id[id];
    },
    get_reservations_sorted(max_count) {
        max_count = max_count
            ? Math.min(this.reservation_sorted.length, max_count)
            : this.reservation_sorted.length;
        var reservations = [];
        for (var i = 0; i < max_count; i++) {
            reservations.push(this.reservation_by_id[this.reservation_sorted[i]]);
        }
        return reservations;
    },
    search_reservation(query) {
        try {
            query = query.replace(
                /[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,
                "."
            );
            query = query.replace(/ /g, ".+");
            var re = RegExp("([0-9]+):.*?" + unaccent(query), "gi");
        } catch (e) {
            return [];
        }
        var results = [];
        const searchStrings = Object.values(this.reservation_search_strings).reverse();
        let searchString = searchStrings.pop();
        while (searchString && results.length < this.limit) {
            var r = re.exec(searchString);
            if (r) {
                var id = Number(r[1]);
                var res = this.get_reservation_by_id(id);
                if (res) {
                    results.push(res);
                }
            } else {
                searchString = searchStrings.pop();
            }
        }
        return results;
    },
    _reservation_search_string(reservation) {
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
    add_reservations(reservations) {
        var updated = {};
        var reservation = null;
        for (var i = 0, len = reservations.length; i < len; i++) {
            reservation = reservations[i];

            if (!this.reservation_by_id[reservation.id]) {
                this.reservation_sorted.push(reservation.id);
            }
            updated[reservation.id] = reservation;
            this.reservation_by_id[reservation.id] = reservation;
        }

        const updatedChunks = new Set();
        const CHUNK_SIZE = 100;
        for (const id in updated) {
            const chunkId = Math.floor(id / CHUNK_SIZE);
            if (updatedChunks.has(chunkId)) {
                // Another reservation in this chunk was updated and we already rebuild the chunk
                continue;
            }
            updatedChunks.add(chunkId);
            // If there were updates, we need to rebuild the search string for this chunk
            let searchString = "";

            for (let id = chunkId * CHUNK_SIZE; id < (chunkId + 1) * CHUNK_SIZE; id++) {
                if (!(id in this.reservation_by_id)) {
                    continue;
                }
                const reservation = this.reservation_by_id[id];
                searchString += this._reservation_search_string(reservation);
            }

            this.reservation_search_strings[chunkId] = unaccent(searchString);
        }
        return Object.keys(updated).length;
    },
});
