/*
Copyright 2022 Comunitea.
License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/
odoo.define("mis_builder_widget_add_pms_properties", function (require) {
    "use strict";

    var core = require("web.core");
    var relational_fields = require("web.relational_fields");
    var MisBuilderWidget = require("mis_builder.widget");
    var _t = core._t;

    MisBuilderWidget.include({
        init: function () {
            this._super.apply(this, arguments);
            this.pms_property_ids_domain = [];
            this.pms_property_ids_label = _t("PMS Properties Filter");
            this.pms_property_ids_m2m = undefined;
        },

        _getFilterFields: function () {
            var fields = this._super.apply(this, arguments);
            fields.push({
                relation: "pms.property",
                type: "many2many",
                name: "filter_pms_property_ids",
                value: this._getFilterValue("pms_property_id"),
            });
            return fields;
        },

        _makeFilterFieldWidgets: function (record) {
            this._super.apply(this, arguments);
            this.pms_property_ids_m2m = new relational_fields.FieldMany2ManyTags(
                this,
                "filter_pms_property_ids",
                record,
                {
                    mode: "edit",
                    attrs: {
                        placeholder: this.pms_property_ids_label,
                        options: {
                            no_create: "True",
                            no_open: "True",
                        },
                    },
                }
            );
            this._registerWidget(
                record.id,
                this.pms_property_ids_m2m.name,
                this.pms_property_ids_m2m
            );
            this.pms_property_ids_m2m.appendTo(this.getMisBuilderFilterBox());
        },

        _beforeCreateWidgets: function (record) {
            var defs = this._super.apply(this, arguments);

            var dataPoint = record.data.filter_pms_property_ids;
            dataPoint.fieldsInfo.default.display_name = {};
            defs.push(this.model.reload(dataPoint.id));

            return defs;
        },

        _confirmChange: function () {
            var result = this._super.apply(this, arguments);

            if (this.pms_property_ids_m2m !== undefined) {
                if (
                    this.pms_property_ids_m2m.value &&
                    this.pms_property_ids_m2m.value.res_ids.length > 0
                ) {
                    this._setFilterValue(
                        "pms_property_id",
                        this.pms_property_ids_m2m.value.res_ids,
                        "in"
                    );
                } else {
                    this._setFilterValue("pms_property_id", undefined);
                }
            }
            return result;
        },
    });
});
