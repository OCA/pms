// Copyright 2018 Alexandre Díaz <dev@redneboa.es>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
odoo.define('hotel_calendar.MultiCalendar', function(require) {
  'use strict';

  var core = require('web.core');
  var session = require('web.session');
  var Widget = require('web.Widget');

  var MultiCalendar = Widget.extend({
    _calendars: [],
    _active_calendar: -1,
    _events: {},

    init: function(parent) {
      this._super.apply(this, arguments);
    },

    start: function() {
      this._super.apply(this, arguments);

      this._create_tabs_panel();
    },

    _create_tab: function(name, id) {
      // '+' Tab
      var $tab = $('<a/>', {
        id: name,
        href: `#${id}`,
        text: name,
      }).appendTo($('<li/>').prependTo(this.$tabs));
      $tab[0].dataset.toggle = 'tab';
      var $pane = $('<div/>', {
        id: id,
        class: 'tab-pane',
      }).appendTo(this.$tabs_content);

      return $pane;
    },

    _create_tabs_panel: function() {
      this.$el.empty();
      this.$tabs = $('<ul/>', {
        class: 'nav nav-tabs',
      }).appendTo(this.$el);
      this.$tabs_content = $('<div/>', {
        class: 'tab-content',
      }).appendTo(this.$el);

      // '+' Tab
      var $pane = this._create_tab('+', 'default');
      $('<p/>', {
        class: 'warn-message',
        text: "NO CALENDAR DEFINED!",
      }).appendTo($pane);
    },

    get_active_calendar: function() {
      return this._calendars[this._active_calendar];
    },

    recalculate_reservation_positions: function() {
      setTimeout(function(){
        for (var reserv of this.get_active_calendar._reservations) {
          var style = window.getComputedStyle(reserv._html, null);
          if (parseInt(style.width, 10) < 15 || parseInt(style.height, 10) < 15 || parseInt(style.top, 10) === 0) {
            this.get_active_calendar()._updateReservation(reserv);
          }
        }
      }.bind(this), 200);
    },

    create_calendar: function(name, options, pricelist, restrictions, base) {
      var $pane = this._create_tab(name, `calendar-pane-${name}`);
      var calendar = new HotelCalendar($pane[0], options, pricelist, restrictions, base);
      this._assign_calendar_events(calendar);
      this._calendars.push(calendar);
      this._active_calendar = this._calendars.length - 1;
    },

    on: function(event_name, callback) {
      for (var calendar of this._calendars) {
        calendar.addEventListener(event_name, callback);
      }
    },

    _assign_calendar_events: function(calendar) {

    },
  });

  return MultiCalendar;
});
