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

import Registries from "point_of_sale.Registries";
import {Order, Orderline, PosGlobalState} from "point_of_sale.models";

const PosPmsGlobalState = (PosGlobalState) =>
    class extends PosGlobalState {
        constructor(obj) {
            super(obj);
        }

        // @override
        async _processData(loadedData) {
            await super._processData(...arguments);
            if (this.config.pay_on_reservation) {
                this.reservations = loadedData["pms.reservation"];
                this.loadPmsReservation();
                this.addReservations(this.reservations);
            }
        }

        loadPmsReservation() {
            if (this.config.pay_on_reservation) {
                this.reservations_by_id = {};
                this.services_by_id = {};
                for (const reservation of this.reservations) {
                    this.reservations_by_id[reservation.id] = reservation;
                    for (const service of reservation.services) {
                        this.services_by_id[service.id] = service;
                        service.reservation = reservation;
                    }
                }
            }
        }

        async _loadReservations(reservartionIds) {
            if (reservartionIds.lenght > 0) {
                var domain = [["id", "in", reservartionIds]];
                const fetchedReservations = await this.env.services.rpc(
                    {
                        model: "pos.session",
                        method: "get_pos_ui_pms_reservation_by_params",
                        args: [[odoo.pos_session_id], {domain}],
                    },
                    {
                        timeout: 3000,
                        shadow: true,
                    }
                );
                this.addReservations(fetchedReservations);
            }
        }

        addReservations(reservations) {
            return this.db.add_reservations(reservations);
        }
    };

Registries.Model.extend(PosGlobalState, PosPmsGlobalState);

const PosPmsOrder = (Order) =>
    class extends Order {
        constructor(obj, options) {
            super(obj, options);
            this.paid_on_reservation = this.paid_on_reservation || null;
            this.pms_reservation_id = this.pms_reservation_id || null;
        }

        get_paid_on_reservation() {
            return this.paid_on_reservation;
        }

        set_paid_on_reservation(value) {
            this.paid_on_reservation = value;
        }

        get_pms_reservation_id() {
            return this.pms_reservation_id;
        }

        set_pms_reservation_id(value) {
            this.pms_reservation_id = value;
        }

        export_as_JSON() {
            var json = super.export_as_JSON();
            json.paid_on_reservation = this.paid_on_reservation;
            json.pms_reservation_id = this.pms_reservation_id;
            return json;
        }

        init_from_JSON(json) {
            super.init_from_JSON(json);
            this.paid_on_reservation = json.paid_on_reservation;
            this.pms_reservation_id = json.pms_reservation_id;
        }

        apply_ms_data(data) {
            if (typeof data.paid_on_reservation !== "undefined") {
                this.set_paid_on_reservation(data.paid_on_reservation);
            }
            if (typeof data.pms_reservation_id !== "undefined") {
                this.set_pms_reservation_id(data.pms_reservation_id);
            }
            this.trigger("change", this);
        }

        add_reservation_services(reservation) {
            var self = this;
            var d = new Date();
            var month = d.getMonth() + 1;
            var day = d.getDate();

            var current_date =
                d.getFullYear() +
                "-" +
                (month < 10 ? "0" : "") +
                month +
                "-" +
                (day < 10 ? "0" : "") +
                day;

            var service_lines =
                reservation.services.map((x) => x.service_lines) || false;
            var today_service_lines = [];
            _.each(service_lines, function (service_array) {
                today_service_lines.push(
                    service_array.find((x) => x.date === current_date)
                );
            });

            _.each(today_service_lines, function (service_line_id) {
                if (service_line_id) {
                    var qty = service_line_id.day_qty;
                    if (service_line_id.pos_order_lines.length > 0) {
                        _.each(
                            service_line_id.pos_order_lines,
                            function (order_line_id) {
                                qty -= order_line_id.qty;
                            }
                        );
                    }
                    if (qty > 0) {
                        var options = {
                            quantity: qty,
                            pms_service_line_id: service_line_id.id,
                            price: 0.0,
                        };
                        var service_product = self.pos.db.get_product_by_id(
                            service_line_id.product_id[0]
                        );
                        self.pos.get_order().add_product(service_product, options);
                        var last_line = self.pos.get_order().get_last_orderline();
                        if (last_line) {
                            last_line.set_note(
                                "RESERVATION: " +
                                    reservation.name +
                                    " ROOMS: " +
                                    reservation.rooms
                            );
                        }
                        var r_service_line_id = reservation.services
                            .map((x) => x.service_lines)[0]
                            .find((x) => x.id === service_line_id.id);
                        if (
                            r_service_line_id &&
                            r_service_line_id.pos_order_lines.length === 0
                        ) {
                            r_service_line_id.pos_order_lines.push({
                                id: 0,
                                qty: parseInt(qty),
                            });
                        } else if (
                            r_service_line_id &&
                            r_service_line_id.pos_order_lines.length === 1 &&
                            r_service_line_id.pos_order_lines[0].id === 0
                        ) {
                            r_service_line_id.pos_order_lines[0].qty = parseInt(qty);
                        } else if (
                            r_service_line_id &&
                            r_service_line_id.pos_order_lines.length === 1 &&
                            r_service_line_id.pos_order_lines[0].id != 0
                        ) {
                            r_service_line_id.pos_order_lines.push({
                                id: 0,
                                qty: parseInt(qty),
                            });
                        } else if (
                            r_service_line_id &&
                            r_service_line_id.pos_order_lines.length > 1
                        ) {
                            var id_in_lines = false;
                            _.each(
                                r_service_line_id.pos_order_lines,
                                function (pos_line_id) {
                                    if (pos_line_id.id == self.id) {
                                        pos_line_id.qty = parseInt(qty);
                                        id_in_lines = true;
                                    }
                                }
                            );
                            if (id_in_lines == false) {
                                r_service_line_id.pos_order_lines.push({
                                    id: self.id,
                                    qty: parseInt(qty),
                                });
                            }
                        }
                    }
                }
            });
        }

        add_product(product, options) {
            super.add_product(...arguments);
            if (options.pms_service_line_id) {
                this.selected_orderline.set_pms_service_line_id(
                    options.pms_service_line_id
                );
            }
        }

        export_for_printing() {
            var res = super.export_for_printing();
            res.paid_on_reservation = this.paid_on_reservation;
            res.pms_reservation_id = this.pms_reservation_id;
            return res;
        }
    };

Registries.Model.extend(Order, PosPmsOrder);

const PosPmsOrderline = (Orderline) =>
    class extends Orderline {
        constructor(obj, options) {
            super(obj, options);
            this.server_id = this.server_id || null;
            this.pms_service_line_id = this.pms_service_line_id || null;
        }

        get_pms_service_line_id() {
            return this.pms_service_line_id;
        }

        set_pms_service_line_id(value) {
            this.pms_service_line_id = value;
        }

        export_as_JSON() {
            var json = super.export_as_JSON();
            json.pms_service_line_id = this.pms_service_line_id;
            return json;
        }

        init_from_JSON(json) {
            super.init_from_JSON(json);
            this.pms_service_line_id = json.pms_service_line_id;
            this.server_id = json.server_id;
        }

        apply_ms_data(data) {
            if (typeof data.pms_service_line_id !== "undefined") {
                this.set_pms_service_line_id(data.pms_service_line_id);
            }
            this.trigger("change", this);
        }

        set_quantity(quantity, keep_price) {
            var res = super.set_quantity(quantity, keep_price);
            var is_real_qty = true;
            if (!quantity || quantity == "remove") {
                is_real_qty = false;
            }
            var self = this;
            if (self.pms_service_line_id) {
                this.pos.reservations.map(function (x) {
                    _.each(x.services, function (service) {
                        _.each(service.service_lines, function (line) {
                            if (line.id == self.pms_service_line_id) {
                                // Si no hay líneas de pedido y la cantidad es real, agregamos una nueva
                                if (line.pos_order_lines.length == 0 && is_real_qty) {
                                    line.pos_order_lines.push({
                                        id: self.server_id || 0,
                                        qty: parseInt(quantity),
                                    });
                                }
                                // Si ya existe una línea de pedido con el mismo ID
                                else if (
                                    line.pos_order_lines.length == 1 &&
                                    line.pos_order_lines[0].id == self.server_id
                                ) {
                                    if (is_real_qty) {
                                        // Actualizamos la cantidad
                                        line.pos_order_lines[0].qty =
                                            parseInt(quantity);
                                    } else {
                                        // Eliminamos la línea con splice() en lugar de pop()
                                        line.pos_order_lines.splice(0, 1);
                                    }
                                }
                                // Si hay varias líneas, buscamos por ID y eliminamos correctamente
                                else if (line.pos_order_lines.length > 1) {
                                    var index_to_remove = -1;
                                    _.each(
                                        line.pos_order_lines,
                                        function (pos_line_id, index) {
                                            if (pos_line_id.id == self.server_id) {
                                                if (is_real_qty) {
                                                    pos_line_id.qty =
                                                        parseInt(quantity);
                                                } else {
                                                    index_to_remove = index;
                                                }
                                            }
                                        }
                                    );
                                    if (index_to_remove !== -1) {
                                        line.pos_order_lines.splice(index_to_remove, 1);
                                    }
                                }
                            }
                        });
                    });
                });
            }
            return res;
        }
    };

Registries.Model.extend(Orderline, PosPmsOrderline);
