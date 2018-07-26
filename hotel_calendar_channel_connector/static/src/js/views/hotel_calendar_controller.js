// Copyright 2018 Alexandre Díaz <dev@redneboa.es>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
odoo.define('hotel_calendar.PMSHotelCalendarControllerChannelConnector', function (require) {
"use strict";

var PMSCalendarController = require('hotel_calendar.PMSCalendarController');
var Core = require('web.core');

var QWeb = Core.qweb;

var PMSHotelCalendarControllerChannelConnector = PMSCalendarController.include({
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

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------
    _onUpdateButtonsCounter: function (ev) {
        this._super(ev);
        var self = this;
        var domain_reservations = [['to_assign', '=', true], ['to_read', '=', true]];
        var domain_issues = [['to_read', '=', true]];
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
                    if (reserv['wrid']) {
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

});

return PMSHotelCalendarControllerChannelConnector;

});
