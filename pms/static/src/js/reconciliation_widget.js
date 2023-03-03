/*
Copyright 2022 Comunitea.
License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/
odoo.define("account_reconciliation_widget_inherit", function (require) {
    "use strict";

    var core = require("web.core");
    var relational_fields = require("web.relational_fields");
    var ReconciliationRenderer = require("account.ReconciliationRenderer");
    var ReconciliationModel = require("account.ReconciliationModel");
    var _t = core._t;

    ReconciliationModel.StatementModel.include({
        init: function (parent, options) {
            this._super(parent, options);
            this.extra_field_names = ["pms_property_id"];
            this.extra_fields = [
                {
                    relation: "pms.property",
                    type: "many2one",
                    name: "pms_property_id",
                },
            ];
            this.extra_fieldInfo = {
                pms_property_id: {string: _t("Property")},
            };
            this.quickCreateFields = this.quickCreateFields.concat(
                this.extra_field_names
            );
        },

        makeRecord: function (model, fields, fieldInfo) {
            if (model === "account.bank.statement.line") {
                var fields = fields.concat(this.extra_fields);
                _.extend(fieldInfo, this.extra_fieldInfo);
            }
            return this._super(model, fields, fieldInfo);
        },

        _formatToProcessReconciliation: function (line, prop) {
            var result = this._super(line, prop);
            if (prop.pms_property_id) result.pms_property_id = prop.pms_property_id.id;
            return result;
        },

        _formatQuickCreate: function (line, values) {
            var prop = this._super(line, values);
            prop.pms_property_id = "";
            return prop;
        },
    });

    ReconciliationRenderer.LineRenderer.include({
        _renderCreate: function (state) {
            return Promise.all([this._super(state), this._makePmsPropertyRecord()]);
        },

        _makePmsPropertyRecord: function () {
            const field = {
                type: "many2one",
                name: "pms_property_id",
                relation: "pms.property",
            };
            return this.model
                .makeRecord("account.bank.statement.line", [field], {
                    pms_property_id: {},
                })
                .then((recordID) => {
                    this.fields.pms_property_id = new relational_fields.FieldMany2One(
                        this,
                        "pms_property_id",
                        this.model.get(recordID),
                        {
                            mode: "edit",
                        }
                    );
                    this.fields.pms_property_id.appendTo(
                        this.$(".create_pms_property_id .o_td_field")
                    );
                });
        },
    });
});
