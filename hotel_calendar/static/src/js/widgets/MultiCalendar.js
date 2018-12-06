// Copyright 2018 Alexandre Díaz <dev@redneboa.es>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
odoo.define('hotel_calendar.MultiCalendar', function(require) {
  'use strict';

  var core = require('web.core');
  var session = require('web.session');
  var Widget = require('web.Widget');

  var MultiCalendar = Widget.extend({
    _calendars: null,
    _active_calendar: -1,

    init: function(parent) {
      this._super.apply(this, arguments);
    },

    start: function() {
      this._super.apply(this, arguments);

      this.$el.html("<p>NO CALENDAR DEFINED!</p>");
    },

    get_active_calendar: function() {
      return this._calendars[this._active_calendar];
    }

    recalculate_reservation_positions: function() {
      setTimeout(function(){
        for (var reserv of this._hcalendar._reservations) {
          var style = window.getComputedStyle(reserv._html, null);
          if (parseInt(style.width, 10) < 15 || parseInt(style.height, 10) < 15 || parseInt(style.top, 10) === 0) {
            this.get_active_calendar()._updateReservation(reserv);
          }
        }
      }.bind(this), 200);
    },

    create_calendar: function() {

    },
  });

  return MultiCalendar;
});
