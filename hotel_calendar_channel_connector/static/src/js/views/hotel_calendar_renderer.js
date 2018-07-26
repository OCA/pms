/* global odoo, $ */
// Copyright 2018 Alexandre Díaz <dev@redneboa.es>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
odoo.define('hotel_calendar_channel_connector.PMSHotelCalendarRendererChannelConnector', function (require) {
  'use strict';

  var PMSCalendarRenderer = require('hotel_calendar.PMSCalendarRenderer');

  var PMSHotelCalendarRendererChannelConnector = PMSCalendarRenderer.include({

    update_buttons_counter_channel_connector: function (nreservations, nissues) {
      // Cloud Reservations
      var $button = this.$el.find('#btn_channel_manager_request');
      var $text = this.$el.find('#btn_channel_manager_request .cloud-text');
      if (nreservations > 0) {
          $button.addClass('incoming');
          $text.text(nreservations);
          $text.show();
      } else {
          $button.removeClass('incoming');
          $text.hide();
      }

      // Issues
      var $ninfo = this.$el.find('#pms-menu #btn_action_issues div.ninfo');
      var $badge_issues = $ninfo.find('.badge');
      if (nissues > 0) {
          $badge_issues.text(nissues);
          $badge_issues.parent().show();
          $ninfo.show();
      } else {
          $ninfo.hide();
      }
    },

    init_calendar_view: function () {
      var self = this;
      return this._super().then(function () {
        self.$el.find('#btn_channel_manager_request').on('click', function (ev) {
          self.do_action("hotel_calendar_wubook.hotel_reservation_action_manager_request");
        });
      });
    },

    _generate_reservation_tooltip_dict: function(tp) {
      var qdict = this._super(tp);
      qdict['channel_name'] = tp[5];
      return qdict;
    },

    _generate_bookings_domain: function(tsearch) {
      var domain = this._super(tsearch);
      domain.splice(0, 0, '|');
      domain.push(['wrid', 'ilike', tsearch]);
      return domain;
    }
  });

  return PMSHotelCalendarRendererChannelConnector;
});
