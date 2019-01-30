// Copyright 2019 Alexandre Díaz <dev@redneboa.es>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
odoo.define('hotel_calendar_channel_connector.MPMSCalendarRenderer', function (require) {
"use strict";

var MPMSCalendarRenderer = require('hotel_calendar.MPMSCalendarRenderer');
var Core = require('web.core');

var QWeb = Core.qweb;


var MPMSCalendarRenderer = MPMSCalendarRenderer.include({

    /** CUSTOM METHODS **/
    get_values_to_save: function() {
        var values = this._super.apply(this, arguments);
        if (values) {
            var availability = this._hcalendar.getAvailability(true);
            values.push(availability);
        }
        return values;
    },

});

return MPMSCalendarRenderer;

});
