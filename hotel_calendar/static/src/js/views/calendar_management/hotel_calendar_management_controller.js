// Copyright 2018 Alexandre Díaz <dev@redneboa.es>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
odoo.define('hotel_calendar.MPMSCalendarController', function (require) {
"use strict";

var AbstractController = require('web.AbstractController'),
    Core = require('web.core'),
    Bus = require('bus.bus').bus,
    HotelConstants = require('hotel_calendar.Constants'),

    _t = Core._t,
    QWeb = Core.qweb;

var MPMSCalendarController = AbstractController.extend({
    custom_events: _.extend({}, AbstractController.prototype.custom_events, {
        viewUpdated: '_onViewUpdated',
        onSaveChanges: '_onSaveChanges',
        onLoadCalendar: '_onLoadCalendar',
        onLoadCalendarSettings: '_onLoadCalendarSettings',
    }),
    /**
     * @override
     * @param {Widget} parent
     * @param {AbstractModel} model
     * @param {AbstractRenderer} renderer
     * @param {Object} params
     */
    init: function (parent, model, renderer, params) {
        this._super.apply(this, arguments);
        this.displayName = params.displayName;
        this.formViewId = params.formViewId;
        this.context = params.context;

        Bus.on("notification", this, this._onBusNotification);
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------


    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @param {Object} record
     * @param {integer} record.id
     * @returns {Deferred}
     */
    _updateRecord: function (record) {
        return this.model.updateRecord(record).then(this.reload.bind(this));
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------
    _onSaveChanges: function (ev) {
        this.model.save_changes(ev.data).then(function(results){
            this.renderer.resetSaveState();
        });
    },

    _onLoadCalendar: function (ev) {
        var self = this;

        /** DO MAGIC **/
        var params = this.renderer.generate_params();
        var oparams = [params['dates'][0], params['dates'][1], false, false, true];
        this.model.get_hcalendar_data(oparams).then(function(results){
            self.renderer._days_tooltips = results['events'];
            var rooms = [];
            for (var r of results['rooms']) {
                var nroom = new HRoomType(
                    r[0], // Id
                    r[1], // Name
                    r[2], // Capacity
                    r[3], // Price
                );
                rooms.push(nroom);
            }

            // Get Pricelists
            self.renderer._pricelist_id = results['pricelist_id'];
            self.renderer._restriction_id = results['restriction_id'];
            $.when(
                self.model.get_pricelists(),
                self.model.get_restrictions(),
            ).then(function(a1, a2){
                self.renderer.loadViewFilters(a1, a2);
            })

            self.renderer.create_calendar(rooms);
            console.log(results);
            self.renderer.setCalendarData(results['prices'], results['restrictions'], results['availability'], results['count_reservations']);
        });
    },

    _onLoadCalendarSettings: function (ev) {
        var self = this;
        this.model.get_hcalendar_settings().then(function(results){
            self.renderer.setHCalendarSettings(results);
        });
    },

    _onBusNotification: function () {
        if (!this.renderer._hcalendar) {
            return;
        }
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
                            'date': dt.format(ODOO_DATE_MOMENT_FORMAT),
                            'avail': avail[room_type][day][0],
                            'no_ota': avail[room_type][day][1],
                            'id': avail[room_type][day][2]
                        }];
                        this.renderer._hcalendar.addAvailability(availability);
                        break;
                    case 'pricelist':
                        var prices = notif[1]['price'];
                        var pricelist_id = Object.keys(prices)[0];
                        var pr = {};
                        for (var price of prices[pricelist_id]) {
                            pr[price['room']] = [];
                            var days = Object.keys(price['days']);
                            for (var day of days) {
                                var dt = HotelCalendarManagement.toMoment(day);
                                pr[price['room']].push({
                                    'date': dt.format(ODOO_DATE_MOMENT_FORMAT),
                                    'price':  price['days'][day],
                                    'id': price['id']
                                });
                            }
                        }
                        this.renderer._hcalendar.addPricelist(pr);
                        break;
                    case 'restriction':
                        // FIXME: Expected one day and one room_type
                        var restriction = notif[1]['restriction'];
                        var room_type = Object.keys(restriction)[0];
                        var day = Object.keys(restriction[room_type])[0];
                        var dt = HotelCalendarManagement.toMoment(day);
                        var rest = {};
                        rest[room_type] = [{
                            'date': dt.format(ODOO_DATE_MOMENT_FORMAT),
                            'min_stay': restriction[room_type][day][0],
                            'min_stay_arrival': restriction[room_type][day][1],
                            'max_stay': restriction[room_type][day][2],
                            'max_stay_arrival': restriction[room_type][day][3],
                            'closed': restriction[room_type][day][4],
                            'closed_arrival': restriction[room_type][day][5],
                            'closed_departure': restriction[room_type][day][6],
                            'id': restriction[room_type][day][7]
                        }];
                        this.renderer._hcalendar.addRestrictions(rest);
                        break;
                }
            }
        }
    },

});

return MPMSCalendarController;

});
