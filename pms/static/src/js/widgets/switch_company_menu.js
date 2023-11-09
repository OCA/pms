odoo.define('web.SwitchCompanyMenuPMS', function(require) {
"use strict";

    var session = require('web.session');
    var SwitchMenu = require('web.SwitchCompanyMenu');
    var utils = require("web.utils");

    SwitchMenu.include({
        /**
         * @override
         */
        willStart: function () {
            var self = this;
            this.allowed_company_ids = String(session.user_context.allowed_company_ids)
                                        .split(',')
                                        .map(function (id) {return parseInt(id);});
            this.user_companies = session.user_companies.allowed_companies;
            this.current_company = this.allowed_company_ids[0];
            this.current_company_name = _.find(session.user_companies.allowed_companies, function (company) {
                return company[0] === self.current_company;
            })[1];
            // Work for property menu
            this.allowed_pms_property_ids = String(
                session.user_context.allowed_pms_property_ids).split(",").map(function (id) {
                        return parseInt(id, 10);});
            this.user_pms_properties = session.user_pms_properties.allowed_pms_properties;
            var alowed_properties = []
            this.allowed_pms_property_ids.forEach(element => {
                if (this.allowed_company_ids.find((company) => company === this.user_pms_properties[element-1][2])){
                    alowed_properties.push(this.user_pms_properties[element-1][0])
                };
            });
            if (alowed_properties.length === 0){
                self._firstProperty();
                alowed_properties = this.allowed_pms_property_ids;
            }
            session.user_context.allowed_pms_property_ids = alowed_properties;
            utils.set_cookie("pms_pids", alowed_properties);

            return this._super.apply(this, arguments);
        },

        /**
         * @private
         * @param {MouseEvent|KeyEvent} ev
         */
        _onSwitchCompanyClick: function (ev) {
            if (ev.type == 'keydown' && ev.which != $.ui.keyCode.ENTER && ev.which != $.ui.keyCode.SPACE) {
                return;
            }
            ev.preventDefault();
            ev.stopPropagation();
            var dropdownItem = $(ev.currentTarget).parent();
            var dropdownMenu = dropdownItem.parent();
            var companyID = dropdownItem.data('company-id');
            var allowed_company_ids = this.allowed_company_ids;
            if (dropdownItem.find('.fa-square-o').length) {
                // 1 enabled company: Stay in single company mode
                if (this.allowed_company_ids.length === 1) {
                    if (this.isMobile) {
                        dropdownMenu = dropdownMenu.parent();
                    }
                    dropdownMenu.find('.fa-check-square').removeClass('fa-check-square').addClass('fa-square-o');
                    dropdownItem.find('.fa-square-o').removeClass('fa-square-o').addClass('fa-check-square');
                    allowed_company_ids = [companyID];
                } else { // Multi company mode
                    allowed_company_ids.push(companyID);
                    dropdownItem.find('.fa-square-o').removeClass('fa-square-o').addClass('fa-check-square');
                }
            }
            $(ev.currentTarget).attr('aria-pressed', 'true');
            session.setCompanies(companyID, allowed_company_ids);
            utils.set_cookie("pms_pids", this.allowed_pms_property_ids);
            },

        /**
         * @private
         * @param {MouseEvent|KeyEvent} ev
         */
        _onToggleCompanyClick: function (ev) {
            if (ev.type == 'keydown' && ev.which != $.ui.keyCode.ENTER && ev.which != $.ui.keyCode.SPACE) {
                return;
            }
            ev.preventDefault();
            ev.stopPropagation();
            var dropdownItem = $(ev.currentTarget).parent();
            var companyID = dropdownItem.data('company-id');
            var allowed_company_ids = this.allowed_company_ids;
            var current_company_id = allowed_company_ids[0];
            if (dropdownItem.find('.fa-square-o').length) {
                allowed_company_ids.push(companyID);
                dropdownItem.find('.fa-square-o').removeClass('fa-square-o').addClass('fa-check-square');
                $(ev.currentTarget).attr('aria-checked', 'true');
            } else {
                allowed_company_ids.splice(allowed_company_ids.indexOf(companyID), 1);
                dropdownItem.find('.fa-check-square').addClass('fa-square-o').removeClass('fa-check-square');
                $(ev.currentTarget).attr('aria-checked', 'false');
            }
            session.setCompanies(current_company_id, allowed_company_ids);
            utils.set_cookie("pms_pids", this.allowed_pms_property_ids);
            },

        _firstProperty: function (){
            for (let i = 0; i<this.user_pms_properties.length; i++){
                if (this.user_pms_properties[i][2] === this.allowed_company_ids[0]) {
                    this.allowed_pms_property_ids = [this.user_pms_properties[i][0]];
                    break;
                }
            }
            console.log('There is no valid Property in the company')
            // TODO
        },

    })
});

