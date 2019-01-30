/* global odoo, $ */
// Copyright 2018 Alexandre Díaz <dev@redneboa.es>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
odoo.define('hotel_calendar_channel_connector.PMSHotelCalendarRenderer', function (require) {
  'use strict';

  var PMSCalendarRenderer = require('hotel_calendar.PMSCalendarRenderer');

  var PMSHotelCalendarRenderer = PMSCalendarRenderer.include({

    update_buttons_counter_channel_connector: function (nreservations, nissues) {
      // Cloud Reservations
      var $text = this.$el.find('#btn_channel_manager_request .cloud-text');
      if (nreservations > 0) {
          $text.parent().parent().addClass('button-highlight');
          $text.parent().addClass('incoming');
          $text.text(nreservations);
      } else {
          $text.parent().removeClass('incoming');
      }

      // Issues
      var $ninfo = this.$el.find('#pms-menu #btn_action_issues div.ninfo');
      $ninfo.text(nissues);
      if (nissues) {
        $ninfo.parent().parent().addClass('button-highlight');
      } else {
        $ninfo.parent().parent().removeClass('button-highlight');
      }
    },

    init_calendar_view: function () {
      var self = this;
      return this._super().then(function () {
        self.$el.find('#btn_channel_manager_request').on('click', function (ev) {
          self.do_action("hotel_calendar_channel_connector.hotel_reservation_action_manager_request");
        });
      });
    },

    _generate_bookings_domain: function(tsearch) {
      var domain = this._super(tsearch);
      domain.splice(0, 0, '|');
      domain.push(['external_id', 'ilike', tsearch]);
      return domain;
    }
  });

  return PMSHotelCalendarRenderer;
});
