// Copyright 2018 Alexandre Díaz <dev@redneboa.es>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
odoo.define('hotel_calendar_channel_connector.PMSHotelCalendarController', function (require) {
"use strict";

var PMSCalendarController = require('hotel_calendar.PMSCalendarController');
var Core = require('web.core');

var QWeb = Core.qweb;

var PMSHotelCalendarController = PMSCalendarController.include({
    _sounds: [],
    SOUNDS: { NONE: 0, BOOK_NEW:1, BOOK_CANCELLED:2 },

    init: function (parent, model, renderer, params) {
        this._super.apply(this, arguments);

        this._sounds[this.SOUNDS.BOOK_NEW] = new Audio('hotel_calendar_channel_connector/static/sfx/book_new.mp3');
        this._sounds[this.SOUNDS.BOOK_CANCELLED] = new Audio('hotel_calendar_channel_connector/static/sfx/book_cancelled.mp3');
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------


    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------
    _play_sound: function(/*int*/SoundID) {
      this._sounds[SoundID].play();
    },

    _generate_reservation_tooltip_dict: function(tp) {
      var qdict = this._super(tp);
      qdict['ota_name'] = tp['ota_name'];
      qdict['ota_reservation_id'] = tp['ota_reservation_id'];
      qdict['external_id'] = tp['external_id'];
      return qdict;
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------
    _update_buttons_counter: function (ev) {
        this._super(ev);
        var self = this;
        var domain_reservations = [['to_assign', '=', true]];
        // FIXME: invalid domain search. Issues are in hotel_channel_connector_issue;
        // var domain_issues = [['to_assign', '=', true]];
        var domain_issues = [];
        $.when(
            this.model.search_count(domain_reservations),
            this.model.search_count(domain_issues),
        ).then(function(a1, a2){
            self.renderer.update_buttons_counter_channel_connector(a1, a2);
        });
    },

    _onBusNotification: function(notifications) {
        for (var notif of notifications) {
            if (notif[0][1] === 'hotel.reservation') {
                if (notif[1]['type'] === 'issue') {
                    if (notif[1]['userid'] === this.dataset.context.uid) {
                        continue;
                    }

                    var issue = notif[1]['issue'];
                    var qdict = issue;
                    var msg = QWeb.render('HotelCalendarChannelConnector.NotificationIssue', qdict);
                    if (notif[1]['subtype'] === 'notify') {
                        this.do_notify(notif[1]['title'], msg, true);
                    } else if (notif[1]['subtype'] === 'warn') {
                        this.do_warn(notif[1]['title'], msg, true);
                    }
                }
                else if (notif[1]['type'] === 'reservation') {
                    var reserv = notif[1]['reservation'];
                    if (reserv['channel_type'] == 'web') {
                        if (notif[1]['action'] === 'create') {
                            this._play_sound(this.SOUNDS.BOOK_NEW);
                        } else if (notif[1]['action'] !== 'unlink' && reserv['state'] === 'cancelled') {
                            this._play_sound(this.SOUNDS.BOOK_CANCELLED);
                        }
                    }
                }
            }
        }
        this._super(notifications);
    },

    _refresh_view_options: function(active_index) {
      /* btn_channel_manager_request */
      this._super(active_index);

    },

});

return PMSHotelCalendarController;

});
