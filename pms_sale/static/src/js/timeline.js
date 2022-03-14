odoo.define("pms_sale.timeline", function (require) {
    "use strict";

    const core = require("web.core");
    const time = require("web.time");
    const TimelineRenderer = require("web_timeline.TimelineRenderer");
    const TimelineView = require("web_timeline.TimelineView");

    const _t = core._t;
    TimelineView.prototype.jsLibs.push(
        "/web/static/lib/daterangepicker/daterangepicker.js"
    );
    TimelineView.prototype.jsLibs.push("/web/static/src/js/libs/daterangepicker.js");
    TimelineView.prototype.cssLibs.push(
        "/web/static/lib/daterangepicker/daterangepicker.css"
    );
    TimelineRenderer.include({
        willStart: function () {
            this.city = [];
            this.values = {};
            return Promise.all([
                this._super.apply(this, arguments),
                this.get_selections(),
            ]);
        },
        get_selections: function () {
            var self = this;
            return this._rpc({
                model: "pms.reservation",
                method: "get_selections",
                args: [],
            }).then(function (rec) {
                self.values = rec;
                self.city = rec.city;
            });
        },
        init: function (parent, state, params) {
            var self = this;
            this._super.apply(this, arguments);
            this.modelName = params.model;
            this.date_start = params.date_start;
            this.date_stop = params.date_stop;
            this.view = params.view;
            this.city_value = false;
            this.$filter_reservation = false;
            this.datepicker_value = false;
            this.bedrooms_value = false;
            // Find their matches
            if (this.modelName === "pms.reservation") {
                // Find custom color if mentioned
                if (params.arch.attrs.custom_color === "true") {
                    this._rpc({
                        model: "pms.stage",
                        method: "get_color_information",
                        args: [[]],
                    }).then(function (result) {
                        self.colors = result;
                    });
                }
            }
        },
        start: function () {
            var self = this;
            this._super.apply(this, arguments);
            if (this.modelName === "pms.reservation") {
                const $filter_reservation = $(
                    core.qweb.render("TimelineReservationFilter")
                );
                self.$filter_reservation = $filter_reservation;
                _.each(this.city, function (city) {
                    const newOption = new Option(city, city);
                    $filter_reservation
                        .find(".oe_timeline_select_city")
                        .append(newOption, undefined);
                });
                this.$el.find(".oe_timeline_buttons").append($filter_reservation);
                $filter_reservation
                    .find(".oe_timeline_text_datepicker")
                    .daterangepicker({
                        autoApply: true,
                    });
                $filter_reservation
                    .find(".oe_timeline_button_search")
                    .click(function () {
                        self._onsearchbutton();
                    });
            }
        },
        _onsearchbutton: function () {
            if (this.$el.find(".oe_timeline_select_city").val() !== "Select City") {
                this.city_value = this.$el.find(".oe_timeline_select_city").val();
            } else {
                this.city_value = false;
            }
            if (this.$el.find(".oe_timeline_text_datepicker").val()) {
                this.datepicker_value = this.$el
                    .find(".oe_timeline_text_datepicker")
                    .val();
            } else {
                this.datepicker_value = false;
            }
            if (this.$el.find(".oe_timeline_text_bedrooms").val()) {
                this.bedrooms_value = this.$el.find(".oe_timeline_text_bedrooms").val();
            } else {
                this.bedrooms_value = false;
            }
            this.on_data_loaded(this.view.model.data.data, this.last_group_bys);
        },
        split_groups: function (events, group_bys) {
            if (group_bys.length === 0) {
                return events;
            }
            const groups = [];
            for (const evt of events) {
                const group_name = evt[_.first(group_bys)];
                if (group_name) {
                    if (group_name instanceof Array) {
                        const group = _.find(
                            groups,
                            (existing_group) => existing_group.id === group_name[0]
                        );
                        if (_.isUndefined(group)) {
                            groups.push({
                                id: group_name[0],
                                content: group_name[1],
                            });
                        }
                    }
                }
            }
            return groups;
        },
        get_vals: function () {
            return {
                city_value: this.city_value,
                datepicker_value: this.datepicker_value,
                bedrooms_value: this.bedrooms_value,
            };
        },
        on_data_loaded_2: function (events, group_bys) {
            var self = this;
            if (this.modelName === "pms.reservation") {
                var data = [];
                var groups = [];
                this.grouped_by = group_bys;
                _.each(events, function (event) {
                    if (event[self.date_start]) {
                        data.push(self.event_data_transform(event));
                    }
                });
                groups = self.split_groups(events, group_bys);
                if (group_bys[0] === "property_id") {
                    var groups_user_ids = [];
                    for (var g in groups) {
                        groups_user_ids.push(groups[g].id);
                    }
                    self._rpc({
                        model: "pms.property",
                        method: "get_property_information",
                        args: [this.get_vals()],
                    }).then(function (result) {
                        self.property_ids = [];
                        self.properties = [];
                        self.properties.push(result);
                        for (var r in result) {
                            self.property_ids.push(result[r].id);
                        }
                        var res_user_groups = [];
                        var res_user_groups_ids = [];

                        for (var u in self.property_ids) {
                            if (
                                !(self.property_ids[u] in groups_user_ids) ||
                                self.property_ids[u] !== -1
                            ) {
                                // Get User Name
                                var user_name = "-";
                                for (var n in self.properties[0]) {
                                    if (
                                        self.properties[0][n].id ===
                                        self.property_ids[u]
                                    ) {
                                        user_name =
                                            self.properties[0][n].ref ||
                                            self.properties[0][n].name;
                                    }
                                }
                                var is_available = false;
                                for (var i in groups) {
                                    if (groups[i].id === self.property_ids[u]) {
                                        if (
                                            !res_user_groups_ids.includes(
                                                self.property_ids[u]
                                            )
                                        ) {
                                            res_user_groups.push({
                                                id: self.property_ids[u],
                                                content: _t(user_name),
                                            });
                                            res_user_groups_ids.push(
                                                self.property_ids[u]
                                            );
                                        }
                                    }
                                }
                                if (!is_available) {
                                    if (
                                        !res_user_groups_ids.includes(
                                            self.property_ids[u]
                                        )
                                    ) {
                                        res_user_groups.push({
                                            id: self.property_ids[u],
                                            content: _t(user_name),
                                        });
                                        res_user_groups_ids.push(self.property_ids[u]);
                                    }
                                }
                            }
                        }
                        self.timeline.setGroups(res_user_groups);
                        self.timeline.setItems(data);
                        self.timeline.setOptions({
                            orientation: "top",
                        });
                        if (self.datepicker_value) {
                            var value = self.datepicker_value.split("-");
                            const date_value = new moment(value[0], "MM/DD/YYYY");
                            self.timeline.moveTo(date_value);
                        }
                    });
                }
            }
            return this._super.apply(this, arguments);
        },
        event_data_transform: function (evt) {
            if (this.modelName === "pms.reservation") {
                var self = this;
                var date_start = new moment();
                var date_stop = null;
                date_start = time.auto_str_to_date(evt[this.date_start]);
                date_stop = this.date_stop
                    ? time.auto_str_to_date(evt[this.date_stop])
                    : null;
                var group = evt[self.last_group_bys[0]];
                if (group && group instanceof Array) {
                    group = _.first(group);
                } else {
                    group = -1;
                }
                _.each(self.colors, function (color) {
                    if (
                        Function(
                            '"use strict";return\'' +
                                evt[color.field] +
                                "' " +
                                color.opt +
                                " '" +
                                color.value +
                                "'"
                        )()
                    ) {
                        self.color = color.color;
                    } else if (
                        Function(
                            '"use strict";return\'' +
                                evt[color.field][1] +
                                "' " +
                                color.opt +
                                " '" +
                                color.value +
                                "'"
                        )
                    ) {
                        self.color = color.color;
                    }
                });
                var content = _.isUndefined(evt.__name) ? evt.display_name : evt.__name;
                if (this.arch.children.length) {
                    content = this.render_timeline_item(evt);
                }
                var r = {
                    start: date_start,
                    content: content,
                    id: evt.id,
                    group: group,
                    evt: evt,
                    style: "background-color: " + self.color + ";",
                };

                if (date_stop && !moment(date_start).isSame(date_stop)) {
                    r.end = date_stop;
                }
                self.color = null;
                return r;
            }
            return this._super.apply(this, arguments);
        },
    });
});
