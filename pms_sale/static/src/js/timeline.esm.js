/** @odoo-module **/
// Copyright (c) 2021 Gray Matter Logic
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import {TimelineRenderer} from "@web_timeline/views/timeline/timeline_renderer.esm";
import {onMounted, useState} from "@odoo/owl";
import {patch} from "@web/core/utils/patch";

patch(TimelineRenderer.prototype, {
    setup() {
        super.setup(...arguments);
        if (this.params.resModel === "pms.reservation") {
            this.pmsFilter = useState({
                city: "",
                datepicker: "",
                bedrooms: "",
                cities: [],
            });
            onMounted(() => {
                this._injectPmsFilterBar();
                this._loadPmsSelections();
            });
        }
    },

    async _loadPmsSelections() {
        const result = await this.orm.call("pms.reservation", "get_selections", []);
        if (!result) return;
        this.pmsFilter.cities = result.city || [];
        const select = this.rootRef.el?.querySelector(
            ".pms-timeline-filters .pms-city-select"
        );
        if (!select) return;
        while (select.options.length > 1) {
            select.remove(1);
        }
        for (const city of this.pmsFilter.cities) {
            select.appendChild(new Option(city, city));
        }
    },

    _injectPmsFilterBar() {
        const buttonsEl = this.rootRef.el?.querySelector(".oe_timeline_buttons");
        if (!buttonsEl || buttonsEl.querySelector(".pms-timeline-filters")) return;

        const filterDiv = document.createElement("div");
        filterDiv.className = "btn-group btn-sm pms-timeline-filters";

        const citySelect = document.createElement("select");
        citySelect.className = "btn btn-default btn-sm pms-city-select";
        citySelect.style.cssText =
            "width:20%;border-bottom:1px solid;margin-right:10px;";
        citySelect.appendChild(new Option("Select City", ""));

        const dateInput = document.createElement("input");
        dateInput.className = "btn btn-default btn-sm";
        dateInput.placeholder = "Date...";
        dateInput.style.cssText = "border-bottom:1px solid;margin-right:10px;";

        const bedroomsInput = document.createElement("input");
        bedroomsInput.type = "number";
        bedroomsInput.className = "btn btn-default btn-sm";
        bedroomsInput.placeholder = "Bedrooms...";
        bedroomsInput.style.cssText =
            "width:20%;border-bottom:1px solid;margin-right:10px;";

        const searchBtn = document.createElement("button");
        searchBtn.className = "btn btn-default";
        searchBtn.textContent = "Search";
        searchBtn.addEventListener("click", () => {
            this.pmsFilter.city = citySelect.value;
            this.pmsFilter.datepicker = dateInput.value;
            this.pmsFilter.bedrooms = bedroomsInput.value;
            this.on_data_loaded(this.model.data);
        });

        filterDiv.append(citySelect, dateInput, bedroomsInput, searchBtn);
        buttonsEl.appendChild(filterDiv);
    },

    async on_data_loaded(records, adjust_window) {
        if (this.params.resModel === "pms.reservation" && this.pmsFilter) {
            const hasFilter =
                this.pmsFilter.city ||
                this.pmsFilter.datepicker ||
                this.pmsFilter.bedrooms;
            if (hasFilter) {
                const propertyInfo = await this.orm.call(
                    "pms.property",
                    "get_property_information",
                    [
                        {
                            city_value: this.pmsFilter.city || false,
                            datepicker_value: this.pmsFilter.datepicker || false,
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
