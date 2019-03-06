// Copyright 2018 Alexandre Díaz <dev@redneboa.es>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
odoo.define('hotel_calendar.MPMSCalendarModel', function (require) {
"use strict";

var AbstractModel = require('web.AbstractModel'),
    Context = require('web.Context'),
    Core = require('web.core'),
    FieldUtils = require('web.field_utils'),
    Session = require('web.session');


return AbstractModel.extend({
    init: function () {
        this._super.apply(this, arguments);
        this.end_date = null;
    },

    load: function (params) {
        this.modelName = params.modelName;
    },

    save_changes: function (params) {
        params.splice(0, 0, false); // FIXME: ID=False because first parameter its an integer
        return this._rpc({
            model: this.modelName,
            method: 'save_changes',
            args: params,
            //context: Session.user_context,
        });
    },

    get_hcalendar_data: function (params) {
        return this._rpc({
            model: this.modelName,
            method: 'get_hcalendar_all_data',
            args: params,
            context: Session.user_context,
        });
    },

    get_pricelists: function () {
        var domain = [];
        domain.push(['pricelist_type', '=', 'daily']);
        return this._rpc({
            model: 'product.pricelist',
            method: 'search_read',
            args: [domain, ['id','name']],
            context: Session.user_context,
        });
    },

    get_restrictions: function () {
        return this._rpc({
            model: 'hotel.room.type.restriction',
            method: 'search_read',
            args: [false, ['id','name']],
            context: Session.user_context,
        });
    },

    get_hcalendar_settings: function () {
        return this._rpc({
            model: this.modelName,
            method: 'get_hcalendar_settings',
            args: [false],
        });
    },
});
});
