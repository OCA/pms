odoo.define("web.SwitchPmsMenu", function (require) {
    "use strict";

    /**
     * When Odoo is configured in multi-property mode, users should obviously be able
     * to switch their interface from one property to the other.  This is the purpose
     * of this widget, by displaying a dropdown menu in the systray.
     */

    const {_t} = require("web.core");
    var config = require("web.config");
    var session = require("web.session");
    var SystrayMenu = require("web.SystrayMenu");
    var Widget = require("web.Widget");
    var utils = require("web.utils");

    var SwitchPmsMenu = Widget.extend({
        template: "SwitchPmsMenu",
        events: {
            "click .dropdown-item[data-menu] div.pms_log_into":
                "_onSwitchPmsPropertyClick",
            "keydown .dropdown-item[data-menu] div.pms_log_into":
                "_onSwitchPmsPropertyClick",
            "click .dropdown-item[data-menu] div.pms_toggle_property":
                "_onTogglePmsPropertyClick",
            "keydown .dropdown-item[data-menu] div.pms_toggle_property":
                "_onTogglePmsPropertyClick",
        },
        /**
         * @override
         */
        init: function () {
            this._super.apply(this, arguments);
            this.isMobile = config.device.isMobile;
            this._onSwitchPmsPropertyClick = _.debounce(
                this._onSwitchPmsPropertyClick,
                1500,
                true
            );
        },

        /**
         * @override
         */
        willStart: function () {
            var self = this;
            this.allowed_company_ids = String(session.user_context.allowed_company_ids)
                .split(",")
                .map(function (id) {
                    return parseInt(id);
                });
            this.allowed_pms_property_ids = String(
                session.user_context.allowed_pms_property_ids
            )
                .split(",")
                .map(function (id) {
                    return parseInt(id, 10);
                });
            this.user_pms_properties =
                session.user_pms_properties.allowed_pms_properties;

            // Clean not allowed company
            var display_properties = [];
            var pms_propertyID = [];
            var alowed_properties = this.allowed_pms_property_ids.filter((val, ind) => {
                return this.allowed_pms_property_ids.indexOf(val) === ind;
            });

            this.user_pms_properties.forEach((element) => {
                if (this.allowed_company_ids.includes(element[2])) {
                    display_properties.push(element);
                    pms_propertyID.push(element[0]);
                } else if (alowed_properties.indexOf(element[0]) >= 0) {
                    alowed_properties.splice(alowed_properties.indexOf(element[0]), 1);
                }
            });

            this.user_pms_properties = display_properties;
            this.user_pms_properties.sort(function (a, b) {
                return a[1] > b[1] ? 1 : a[1] < b[1] ? -1 : 0;
            });

            // set permanent data
            session.user_context.allowed_pms_property_ids = alowed_properties;
            utils.set_cookie("pms_pids", alowed_properties);

            this.allowed_pms_property_ids = alowed_properties;
            if (
                this.user_pms_properties.length != this.allowed_pms_property_ids.length
            ) {
                this.user_pms_properties.unshift([0, _t("All propertys")]);
            }

            this.current_pms_property = this.allowed_pms_property_ids[0];
            this.current_pms_property_name = _.find(
                session.user_pms_properties.allowed_pms_properties,
                function (pms_property) {
                    return pms_property[0] === self.current_pms_property;
                }
            )[1];
            // this.alowed_properties = alowed_properties.toString();

            return this._super.apply(this, arguments);
        },

        // --------------------------------------------------------------------------
        // Handlers
        // --------------------------------------------------------------------------

        /**
         * @private
         * @param {MouseEvent|KeyEvent} ev
         */
        _onSwitchPmsPropertyClick: function (ev) {
            if (
                ev.type === "keydown" &&
                ev.which !== $.ui.keyCode.ENTER &&
                ev.which !== $.ui.keyCode.SPACE
            ) {
                return;
            }
            ev.preventDefault();
            ev.stopPropagation();
            var dropdownItem = $(ev.currentTarget).parent();
            var dropdownMenu = dropdownItem.parent();
            var pms_propertyID = dropdownItem.data("pms_property-id");
            var allowed_pms_property_ids = this.allowed_pms_property_ids;
            if (pms_propertyID === 0) {
                for (let i = 1; i < this.user_pms_properties.length; i++) {
                    allowed_pms_property_ids.push(this.user_pms_properties[i][0]);
                }
            } else {
                if (dropdownItem.find(".fa-square-o").length) {
                    // 1 enabled pms_property: Stay in single pms proeprty mode
                    if (this.allowed_pms_property_ids.length === 1) {
                        if (this.isMobile) {
                            dropdownMenu = dropdownMenu.parent();
                        }
                        dropdownMenu
                            .find(".fa-check-square")
                            .removeClass("fa-check-square")
                            .addClass("fa-square-o");
                        dropdownItem
                            .find(".fa-square-o")
                            .removeClass("fa-square-o")
                            .addClass("fa-check-square");
                        allowed_pms_property_ids = [pms_propertyID];
                    } else {
                        // Multi pms proeprty mode
                        allowed_pms_property_ids.push(pms_propertyID);
                        dropdownItem
                            .find(".fa-square-o")
                            .removeClass("fa-square-o")
                            .addClass("fa-check-square");
                    }
                }
            }
            $(ev.currentTarget).attr("aria-pressed", "true");
            session.setPmsProperties(pms_propertyID, allowed_pms_property_ids);
        },

        // --------------------------------------------------------------------------
        // Handlers
        // --------------------------------------------------------------------------

        /**
         * @private
         * @param {MouseEvent|KeyEvent} ev
         */
        _onTogglePmsPropertyClick: function (ev) {
            if (
                ev.type === "keydown" &&
                ev.which !== $.ui.keyCode.ENTER &&
                ev.which !== $.ui.keyCode.SPACE
            ) {
                return;
            }
            ev.preventDefault();
            ev.stopPropagation();
            var dropdownItem = $(ev.currentTarget).parent();
            var pms_propertyID = dropdownItem.data("pms_property-id");
            var allowed_pms_property_ids = this.allowed_pms_property_ids;
            var current_pms_property_id = allowed_pms_property_ids[0];
            if (pms_propertyID === 0) {
                for (let i = 1; i < this.user_pms_properties.length; i++) {
                    allowed_pms_property_ids.push(this.user_pms_properties[i][0]);
                }
            } else {
                if (dropdownItem.find(".fa-square-o").length) {
                    allowed_pms_property_ids.push(pms_propertyID);
                    dropdownItem
                        .find(".fa-square-o")
                        .removeClass("fa-square-o")
                        .addClass("fa-check-square");
                    $(ev.currentTarget).attr("aria-checked", "true");
                } else {
                    allowed_pms_property_ids.splice(
                        allowed_pms_property_ids.indexOf(pms_propertyID),
                        1
                    );
                    dropdownItem
                        .find(".fa-check-square")
                        .addClass("fa-square-o")
                        .removeClass("fa-check-square");
                    $(ev.currentTarget).attr("aria-checked", "false");
                }
            }
            session.setPmsProperties(current_pms_property_id, allowed_pms_property_ids);
        },
    });

    if (session.display_switch_pms_property_menu) {
        SystrayMenu.Items.push(SwitchPmsMenu);
    }

    return SwitchPmsMenu;
});
