// Copyright 2019 Alexandre Díaz <dev@redneboa.es>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
odoo.define('hotel_calendar_channel_connector.MPMSCalendarController', function (require) {
"use strict";

var MPMSCalendarController = require('hotel_calendar.MPMSCalendarController');
var HotelConstants = require('hotel_calendar.Constants');
var Core = require('web.core');

var QWeb = Core.qweb;


var MPMSCalendarController = MPMSCalendarController.include({

    _onBusNotification: function (notifications) {
        this._super.apply(this, arguments);
        if (!this.renderer._hcalendar) { return; }

        for (var notif of notifications) {
            if (notif[0][1] === 'hotel.reservation') {
                switch (notif[1]['type']) {
                    case 'availability':
                        var avail = notif[1]['availability'];
                        var room_type = Object.keys(avail)[0];
                        var day = Object.keys(avail[room_type])[0];
                        var dt = HotelCalendarManagement.toMoment(day);
                        var availability = {};
                        availability[room_type] = [{
                            'date': dt.format(HotelConstants.ODOO_DATE_MOMENT_FORMAT),
                            'quota': avail[room_type][day]['quota'],
                            'max_avail': avail[room_type][day]['max_avail'],
                            'no_ota': avail[room_type][day]['no_ota'],
                            'id': avail[room_type][day]['id'],
                            'channel_avail': avail[room_type][day]['channel_avail']
                        }];
                        this.renderer._hcalendar.addAvailability(availability);
                        break;
                }
            }
        }
    },

});

return MPMSCalendarController;

});
