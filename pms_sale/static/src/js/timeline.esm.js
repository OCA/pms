/** @odoo-module **/
// Copyright (c) 2021 Gray Matter Logic
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import {TimelineRenderer} from "@web_timeline/views/timeline/timeline_renderer.esm";
import {onWillStart, useState} from "@odoo/owl";
import {patch} from "@web/core/utils/patch";
import {useDateTimePicker} from "@web/core/datetime/datetime_picker_hook";

patch(TimelineRenderer.prototype, {
    setup() {
        super.setup(...arguments);
        if (this.params.resModel === "pms.reservation") {
            const pmsFilter = useState({
                city: "",
                range: [false, false],
                bedrooms: "",
                cities: [],
            });
            this.pmsFilter = pmsFilter;
            useDateTimePicker({
                startDateRefName: "pms-date-from",
                endDateRefName: "pms-date-to",
                get pickerProps() {
                    return {type: "date", range: true, value: pmsFilter.range};
                },
                onApply: (value) => {
                    pmsFilter.range = value;
                },
            });
            onWillStart(() => this._loadPmsSelections());
        }
    },

    async _loadPmsSelections() {
        const result = await this.orm.call("pms.reservation", "get_selections", []);
        this.pmsFilter.cities = result?.city || [];
    },

    _onPmsSearchClicked() {
        this.on_data_loaded(this.model.data);
    },

    async on_data_loaded(records, adjust_window) {
        if (this.params.resModel === "pms.reservation" && this.pmsFilter) {
            const [dateFrom, dateTo] = this.pmsFilter.range;
            const hasFilter =
                this.pmsFilter.city || dateFrom || dateTo || this.pmsFilter.bedrooms;
            if (hasFilter) {
                const propertyInfo = await this.orm.call(
                    "pms.property",
                    "get_property_information",
                    [
                        {
                            city_value: this.pmsFilter.city || false,
                            date_from: dateFrom ? dateFrom.toISODate() : false,
                            date_to: dateTo ? dateTo.toISODate() : false,
                            bedrooms_value: this.pmsFilter.bedrooms || false,
                        },
                    ]
                );
                const propertyIds = new Set(propertyInfo.map((p) => p.id));
                records = records.filter((r) => {
                    const prop = r.property_id;
                    return Array.isArray(prop) && propertyIds.has(prop[0]);
                });
            }
        }
        return super.on_data_loaded(records, adjust_window);
    },
});
