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

odoo.define("pos_pms_link.models", function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    var utils = require("web.utils");
    var round_di = utils.round_decimals;
    var core = require("web.core");
    const {Gui} = require("point_of_sale.Gui");
    var QWeb = core.qweb;
    const session = require("web.session");

    var _t = core._t;

    var _super_order = models.Order.prototype;

    models.Order = models.Order.extend({
        initialize: function (attr, options) {
            _super_order.initialize.apply(this, arguments);
            this.paid_on_reservation = this.paid_on_reservation || null;
            this.pms_reservation_id = this.pms_reservation_id || null;
        },

        get_paid_on_reservation: function () {
            var paid_on_reservation = this.paid_on_reservation;
            return paid_on_reservation;
        },

        set_paid_on_reservation: function (value) {
            this.paid_on_reservation = value;
            this.trigger("change", this);
        },

        get_pms_reservation_id: function () {
            var pms_reservation_id = this.pms_reservation_id;
            return pms_reservation_id;
        },

        set_pms_reservation_id: function (value) {
            this.pms_reservation_id = value;
            this.trigger("change", this);
        },

        export_as_JSON: function () {
            var json = _super_order.export_as_JSON.apply(this, arguments);
            json.paid_on_reservation = this.paid_on_reservation;
            json.pms_reservation_id = this.pms_reservation_id;
            return json;
        },

        init_from_JSON: function (json) {
            _super_order.init_from_JSON.apply(this, arguments);
            this.paid_on_reservation = json.paid_on_reservation;
            this.pms_reservation_id = json.pms_reservation_id;
        },

        apply_ms_data: function (data) {
            if (typeof data.paid_on_reservation !== "undefined") {
                this.set_paid_on_reservation(data.paid_on_reservation);
            }
            if (typeof data.pms_reservation_id !== "undefined") {
                this.set_pms_reservation_id(data.pms_reservation_id);
            }
            this.trigger("change", this);
        },

        add_reservation_services: function (reservation) {
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

            var service_line_ids =
                reservation.service_ids.map((x) => x.service_line_ids) || false;
            var today_service_lines = [];
            _.each(service_line_ids, function (service_array) {
                today_service_lines.push(
                    service_array.find((x) => x.date === current_date)
                );
            });

            _.each(today_service_lines, function (service_line_id) {
                if (service_line_id) {
                    var qty = service_line_id.day_qty;
                    if (service_line_id.pos_order_line_ids.length > 0) {
                        _.each(service_line_id.pos_order_line_ids, function (
                            order_line_id
                        ) {
                            qty -= order_line_id.qty;
                        });
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
                        last_line.set_note(
                            "RESERVATION: " +
                                reservation.name +
                                " ROOMS: " +
                                reservation.rooms
                        );
                        var r_service_line_id = reservation.service_ids
                            .map((x) => x.service_line_ids)[0]
                            .find((x) => x.id == service_line_id.id);
                        if (r_service_line_id.pos_order_line_ids.length == 0) {
                            r_service_line_id.pos_order_line_ids.push({
                                id: 0,
                                qty: parseInt(qty),
                            });
                        } else if (
                            r_service_line_id.pos_order_line_ids.length == 1 &&
                            r_service_line_id.pos_order_line_ids[0].id == 0
                        ) {
                            r_service_line_id.pos_order_line_ids[0].qty = parseInt(qty);
                        } else if (
                            r_service_line_id.pos_order_line_ids.length == 1 &&
                            r_service_line_id.pos_order_line_ids[0].id != 0
                        ) {
                            r_service_line_id.pos_order_line_ids.push({
                                id: 0,
                                qty: parseInt(qty),
                            });
                        } else if (r_service_line_id.pos_order_line_ids.length > 1) {
                            var id_in_lines = false;
                            _.each(r_service_line_id.pos_order_line_ids, function (
                                pos_line_id
                            ) {
                                if (pos_line_id.id == self.id) {
                                    pos_line_id.qty = parseInt(qty);
                                    id_in_lines = true;
                                }
                            });
                            if (id_in_lines == false) {
                                r_service_line_id.pos_order_line_ids.push({
                                    id: self.id,
                                    qty: parseInt(qty),
                                });
                            }
                        }
                    }
                }
            });
        },

        add_product: function (product, options) {
            _super_order.add_product.apply(this, arguments);
            if (options.pms_service_line_id) {
                this.selected_orderline.set_pms_service_line_id(
                    options.pms_service_line_id
                );
            }
        },

        export_for_printing: function () {
            const result = _super_order.export_for_printing.apply(this, arguments);
            result.paid_on_reservation = this.paid_on_reservation;
            result.pms_reservation_id = this.pms_reservation_id;
            return result;
        },
    });

    var _super_orderline = models.Orderline.prototype;

    models.Orderline = models.Orderline.extend({
        initialize: function (attr, options) {
            _super_orderline.initialize.call(this, attr, options);
            this.server_id = this.server_id || null;
            this.pms_service_line_id = this.pms_service_line_id || null;
        },

        get_pms_service_line_id: function () {
            var pms_service_line_id = this.pms_service_line_id;
            return pms_service_line_id;
        },

        set_pms_service_line_id: function (value) {
            this.pms_service_line_id = value;
            this.trigger("change", this);
        },

        export_as_JSON: function () {
            var json = _super_orderline.export_as_JSON.apply(this, arguments);
            json.pms_service_line_id = this.pms_service_line_id;
            return json;
        },

        init_from_JSON: function (json) {
            _super_orderline.init_from_JSON.apply(this, arguments);
            this.pms_service_line_id = json.pms_service_line_id;
            this.server_id = json.server_id;
        },

        apply_ms_data: function (data) {
            if (typeof data.pms_service_line_id !== "undefined") {
                this.set_pms_service_line_id(data.pms_service_line_id);
            }
            this.trigger("change", this);
        },

        set_quantity: function (quantity, keep_price) {
            _super_orderline.set_quantity.apply(this, arguments);
            var is_real_qty = true;
            if (!quantity || quantity == "remove") {
                is_real_qty = false;
            }
            var self = this;
            if (self.pms_service_line_id) {
                this.pos.reservations.map(function (x) {
                    _.each(x.service_ids, function (service) {
                        _.each(service.service_line_ids, function (line) {
                            if (line.id == self.pms_service_line_id) {
                                if (
                                    line.pos_order_line_ids.length == 0 &&
                                    is_real_qty
                                ) {
                                    line.pos_order_line_ids.push({
                                        id: self.server_id || 0,
                                        qty: parseInt(quantity),
                                    });
                                } else if (
                                    line.pos_order_line_ids.length == 1 &&
                                    line.pos_order_line_ids[0].id == self.server_id
                                ) {
                                    if (is_real_qty) {
                                        line.pos_order_line_ids[0].qty = parseInt(
                                            quantity
                                        );
                                    } else {
                                        line.pos_order_line_ids.pop(
                                            line.pos_order_line_ids[0]
                                        );
                                    }
                                } else if (
                                    line.pos_order_line_ids.length == 1 &&
                                    line.pos_order_line_ids[0].id != self.server_id &&
                                    is_real_qty
                                ) {
                                    line.pos_order_line_ids.push({
                                        id: self.server_id || 0,
                                        qty: parseInt(quantity),
                                    });
                                } else if (line.pos_order_line_ids.length > 1) {
                                    var id_in_lines = false;
                                    _.each(line.pos_order_line_ids, function (
                                        pos_line_id
                                    ) {
                                        if (pos_line_id.id == self.server_id) {
                                            if (is_real_qty) {
                                                pos_line_id.qty = parseInt(quantity);
                                            } else {
                                                line.pos_order_line_ids.pop(
                                                    pos_line_id
                                                );
                                            }
                                            id_in_lines = true;
                                        }
                                    });
                                    _.each(line.pos_order_line_ids, function (
                                        pos_line_id
                                    ) {
                                        if (pos_line_id.id == 0) {
                                            if (is_real_qty) {
                                                pos_line_id.qty = parseInt(quantity);
                                            } else {
                                                line.pos_order_line_ids.pop(
                                                    pos_line_id
                                                );
                                            }
                                            id_in_lines = true;
                                        }
                                    });
                                    if (id_in_lines == false && is_real_qty) {
                                        line.pos_order_line_ids.push({
                                            id: self.server_id || 0,
                                            qty: parseInt(quantity),
                                        });
                                    }
                                }
                            }
                        });
                    });
                });
            }
        },
    });

    var _super_posmodel = models.PosModel.prototype;

    models.PosModel = models.PosModel.extend({
        initialize: function (attr, options) {
            _super_posmodel.initialize.apply(this, arguments);
            this.reservations = [];
        },
    });

    models.load_models({
        model: "pms.reservation",
        fields: [
            "name",
            "id",
            "state",
            "service_ids",
            "partner_name",
            "adults",
            "children",
            "checkin",
            "checkout",
            "folio_internal_comment",
            "rooms",
        ],
        context: function (self) {
            var ctx_copy = session.user_context;
            ctx_copy.pos_user_force = true;
            return ctx_copy;
        },
        domain: function (self) {
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

            var domain = [
                "|",
                ["state", "=", "onboard"],
                "&",
                ["checkout", "=", current_date],
                ["state", "!=", "cancel"],
            ];
            if (self.config_id && self.config.reservation_allowed_propertie_ids)
                domain.push([
                    "pms_property_id",
                    "in",
                    self.config.reservation_allowed_propertie_ids,
                ]);
            return domain;
        },
        loaded: function (self, reservations) {
            self.reservations = reservations;
            self.db.add_reservations(reservations);
        },
    });

    models.load_models({
        model: "pms.service",
        fields: ["name", "id", "service_line_ids", "product_id", "reservation_id"],
        context: function (self) {
            var ctx_copy = session.user_context;
            ctx_copy.pos_user_force = true;
            return ctx_copy;
        },
        domain: function (self) {
            return [["reservation_id", "in", self.reservations.map((x) => x.id)]];
        },
        loaded: function (self, services) {
            self.services = services;
            var services = [];
            _.each(self.reservations, function (reservation) {
                services = [];
                _.each(reservation.service_ids, function (service_id) {
                    services.push(self.services.find((x) => x.id === service_id));
                });
                reservation.service_ids = services;
            });
        },
    });

    models.load_models({
        model: "pms.service.line",
        fields: [
            "date",
            "service_id",
            "id",
            "product_id",
            "day_qty",
            "pos_order_line_ids",
        ],
        context: function (self) {
            var ctx_copy = session.user_context;
            ctx_copy.pos_user_force = true;
            return ctx_copy;
        },
        domain: function (self) {
            return [["service_id", "in", self.services.map((x) => x.id)]];
        },
        loaded: function (self, service_lines) {
            self.service_lines = service_lines;
            var service_lines = [];
            _.each(self.reservations, function (reservation) {
                _.each(reservation.service_ids, function (service_id) {
                    service_lines = [];
                    _.each(service_id.service_line_ids, function (line_id) {
                        service_lines.push(
                            self.service_lines.find((x) => x.id === line_id)
                        );
                    });
                    service_id.service_line_ids = service_lines;
                });
            });
        },
    });

    models.load_models({
        model: "pos.order.line",
        fields: ["qty", "id"],
        domain: function (self) {
            var order_line_ids = [];
            _.each(self.service_lines, function (service_line) {
                if (service_line.pos_order_line_ids.length > 0) {
                    _.each(service_line.pos_order_line_ids, function (line_id) {
                        order_line_ids.push(line_id);
                    });
                }
            });
            return [["id", "in", order_line_ids]];
        },
        loaded: function (self, pos_order_lines) {
            self.pos_order_lines = pos_order_lines;
            _.each(self.service_lines, function (service_line) {
                var order_lines = [];
                _.each(service_line.pos_order_line_ids, function (order_line) {
                    order_lines.push(
                        self.pos_order_lines.find((x) => x.id === order_line)
                    );
                });
                service_line.pos_order_line_ids = order_lines;
            });
        },
    });

    models.PosModel.prototype.models.some(function (model) {
        if (model.model !== "pos.config" && model.model !== "product.pricelist.item") {
            return false;
        }
        const superContext = model.context;
        model.context = function () {
            const context = {};
            if (superContext) {
                context = superContext.apply(this, arguments);
            }
            context.pos_user_force = true;
            return context;
        };
        return true;
    });
});
