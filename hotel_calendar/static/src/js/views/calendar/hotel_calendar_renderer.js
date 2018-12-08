/* global $, odoo, _, HotelCalendar, moment */
// Copyright 2018 Alexandre Díaz <dev@redneboa.es>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
odoo.define('hotel_calendar.PMSCalendarRenderer', function (require) {
"use strict";

var Core = require('web.core'),
    ViewDialogs = require('web.view_dialogs'),
    Dialog = require('web.Dialog'),
    Session = require('web.session'),
    AbstractRenderer = require('web.AbstractRenderer'),
    HotelConstants = require('hotel_calendar.Constants'),
    //Formats = require('web.formats'),

    _t = Core._t,
    _lt = Core._lt,
    QWeb = Core.qweb;

var HotelCalendarView = AbstractRenderer.extend({
    /** VIEW OPTIONS **/
    template: "hotel_calendar.HotelCalendarView",
    display_name: _lt('Hotel Calendar'),
    icon: 'fa fa-map-marker',
    searchable: false,
    searchview_hidden: true,

    // Custom Options
    _view_options: {},
    _reserv_tooltips: {},
    _days_tooltips: [],
    _last_dates: [false, false],


    /** VIEW METHODS **/
    init: function(parent, state, params) {
      this._super.apply(this, arguments);
    },

    start: function () {
      this.init_calendar_view();
      return this._super();
    },

    on_attach_callback: function() {
      this._super();

      if (!this._is_visible) {
        // FIXME: Workaround for restore "lost" reservations (Drawn when the view is hidden)
        this.trigger_up('onViewAttached');
      }
    },

    /** CUSTOM METHODS **/
    get_view_filter_dates: function () {
        var $dateTimePickerBegin = this.$el.find('#pms-search #date_begin');
        var $dateTimePickerEnd = this.$el.find('#pms-search #date_end');
        var date_begin = $dateTimePickerBegin.data("DateTimePicker").date().set({'hour': 0, 'minute': 0, 'second': 0}).clone().utc();
        var date_end = $dateTimePickerEnd.data("DateTimePicker").date().set({'hour': 23, 'minute': 59, 'second': 59}).clone().utc();

        return [date_begin, date_end];
    },

    load_hcalendar_options: function(options) {
        // View Options
        this._view_options = options;
        var date_begin = moment().startOf('day');
        var date_end = date_begin.clone().add(this._view_options['days'], 'd').endOf('day');
        var $dateTimePickerBegin = this.$el.find('#pms-search #date_begin');
        var $dateTimePickerEnd = this.$el.find('#pms-search #date_end');
        //$dateTimePickerBegin.data("ignore_onchange", true);
        $dateTimePickerBegin.data("DateTimePicker").date(date_begin);
        //$dateTimePickerEnd.data("ignore_onchange", true);
        $dateTimePickerEnd.data("DateTimePicker").date(date_end);
        this._last_dates = this.get_view_filter_dates();
    },

    update_buttons_counter: function(ncheckouts, ncheckins, noverbookings) {
        var self = this;
         // Checkouts Button
        var $ninfo = self.$el.find('#pms-menu #btn_action_checkout div.ninfo');
        var $badge_checkout = $ninfo.find('.badge');
        if (ncheckouts > 0) {
            $badge_checkout.text(ncheckouts);
            $badge_checkout.parent().show();
            $ninfo.show();
        } else {
            $ninfo.hide();
        }

        // Checkins Button
        $ninfo = self.$el.find('#pms-menu #btn_action_checkin div.ninfo');
        var $badge_checkin = $ninfo.find('.badge');
        if (ncheckins > 0) {
            $badge_checkin.text(ncheckins);
            $badge_checkin.parent().show();
            $ninfo.show();
        } else {
            $ninfo.hide();
        }

        // OverBookings
        $ninfo = self.$el.find('#pms-menu #btn_swap div.ninfo');
        var $badge_swap = $ninfo.find('.badge');
        if (noverbookings > 0) {
            $badge_swap.text(noverbookings);
            $badge_swap.parent().show();
            $ninfo.show();
        } else {
            $ninfo.hide();
        }
    },

    init_calendar_view: function(){
        var self = this;

        /** VIEW CONTROLS INITIALIZATION **/
        // DATE TIME PICKERS
        var DTPickerOptions = {
            viewMode: 'months',
            icons : {
                time: 'fa fa-clock-o',
                date: 'fa fa-calendar',
                up: 'fa fa-chevron-up',
                down: 'fa fa-chevron-down'
               },
            //language : moment.locale(),
            locale : moment.locale(),
            format : HotelConstants.L10N_DATE_MOMENT_FORMAT,
        };
        var $dateTimePickerBegin = this.$el.find('#pms-search #date_begin');
        var $dateTimePickerEnd = this.$el.find('#pms-search #date_end');
        $dateTimePickerBegin.datetimepicker(DTPickerOptions);
        $dateTimePickerEnd.datetimepicker($.extend({}, DTPickerOptions, { 'useCurrent': false }));

        var date_begin = moment().startOf('day');
        var days = date_begin.daysInMonth();
        var date_end = date_begin.clone().add(days, 'd').endOf('day');
        $dateTimePickerBegin.data("ignore_onchange", true);
        $dateTimePickerBegin.data("DateTimePicker").date(date_begin);
        $dateTimePickerEnd.data("DateTimePicker").date(date_end);
        this._last_dates = this.get_view_filter_dates();

        // Initial State
        var $pms_search = this.$el.find('#pms-search');
        $pms_search.css({
          'top': `-100%`,
          'opacity': 0.0,
        });
        // Show search (Alt+S)
        $(document).keydown(function(ev){
          if (ev.altKey){
            if (ev.key == 'x' || ev.key == 'X'){
              self.toggle_pms_search();
            }
          }
        });

        /* TOUCH EVENTS */
        this.$el.on('touchstart', function(ev){
          var orgEvent = ev.originalEvent;
          this._mouseEventStartPos = [orgEvent.touches[0].screenX, orgEvent.touches[0].screenY];
        });
        this.$el.on('touchend', function(ev){
          var orgEvent = ev.originalEvent;
          if (orgEvent.changedTouches.length > 2) {
            var mousePos = [orgEvent.changedTouches[0].screenX, orgEvent.changedTouches[0].screenY];
            var mouseDiffX = mousePos[0] - this._mouseEventStartPos[0];
            var moveLength = 40;
            var date_begin = false;
            var days = orgEvent.changedTouches.length == 3 && 7 || 1;
            if (mouseDiffX < -moveLength) {
              date_begin = $dateTimePickerBegin.data("DateTimePicker").date().set({'hour': 0, 'minute': 0, 'second': 0}).clone().add(days, 'd');
            }
            else if (mouseDiffX > moveLength) {
              date_begin = $dateTimePickerBegin.data("DateTimePicker").date().set({'hour': 0, 'minute': 0, 'second': 0}).clone().subtract(days, 'd');
            }
            if (date_begin) {
              var date_end = date_begin.clone().add(self._view_options['days'], 'd').endOf('day');
              $dateTimePickerEnd.data("ignore_onchange", true);
              $dateTimePickerEnd.data("DateTimePicker").date(date_end);
              $dateTimePickerBegin.data("DateTimePicker").date(date_begin);
            }
          }
        });

        /* BUTTONS */
        var $button = this.$el.find('#pms-menu #btn_action_bookings');
        $button.on('click', function(ev){ self._open_bookings_tree(); });
        var $btnInput = this.$el.find('#pms-menu #bookings_search');
        $btnInput.on('keypress', function(ev){
          if (ev.keyCode === 13) {
             self._open_bookings_tree();
          }
        });

        this.$el.find("button[data-action]").on('click', function(ev){
          self.do_action(this.dataset.action);
        });

        return $.when(
            this.trigger_up('onLoadCalendarSettings'),
            this.trigger_up('onUpdateButtonsCounter'),
            this.trigger_up('onLoadViewFilters'),
        );
    },

    loadViewFilters: function(resultsHotelRoomType, resultsHotelFloor, resultsHotelRoomAmenities, resultsHotelVirtualRooms) {
        var $list = this.$el.find('#pms-search #type_list');
        $list.html('');
        resultsHotelRoomType.forEach(function(item, index){
            $list.append(`<option value="${item.id}">${item.name}</option>`);
        });
        $list.select2({
          theme: "classic"
        });
        $list.on('change', function(ev){
            this.trigger_up('onApplyFilters');
        }.bind(this));

        // Get Floors
        $list = this.$el.find('#pms-search #floor_list');
        $list.html('');
        resultsHotelFloor.forEach(function(item, index){
            $list.append(`<option value="${item.id}">${item.name}</option>`);
        });
        $list.select2();
        $list.on('change', function(ev){
            this.trigger_up('onApplyFilters');
        }.bind(this));

        // Get Amenities
        $list = this.$el.find('#pms-search #amenities_list');
        $list.html('');
        resultsHotelRoomAmenities.forEach(function(item, index){
            $list.append(`<option value="${item.id}">${item.name}</option>`);
        });
        $list.select2();
        $list.on('change', function(ev){
            this.trigger_up('onApplyFilters');
        }.bind(this));

        // Get Virtual Rooms
        $list = this.$el.find('#pms-search #virtual_list');
        $list.html('');
        resultsHotelVirtualRooms.forEach(function(item, index){
            $list.append(`<option value="${item.id}">${item.name}</option>`);
        });
        $list.select2();
        $list.on('change', function(ev){
            this.trigger_up('onApplyFilters');
        }.bind(this));
    },

    toggle_pms_search: function() {
      var $pms_search = this.$el.find('#pms-search');
      if ($pms_search.position().top < 0)
      {
        var $navbar = $('.navbar');
        var toPos = $navbar.height() + parseInt($navbar.css('border-top-width'), 10) + parseInt($navbar.css('border-bottom-width'), 10);
        $pms_search.animate({
          'top': `${toPos}px`,
          'opacity': 1.0,
        }, 'fast');
      } else {
        $pms_search.animate({
          'top': `-${$pms_search.height()}px`,
          'opacity': 0.0,
        }, 'slow');
      }
    },

    _generate_bookings_domain: function(tsearch) {
      var domain = [];
      domain.push('|', '|', '|', '|',
                  ['partner_id.name', 'ilike', tsearch],
                  ['partner_id.mobile', 'ilike', tsearch],
                  ['partner_id.vat', 'ilike', tsearch],
                  ['partner_id.email', 'ilike', tsearch],
                  ['partner_id.phone', 'ilike', tsearch]);
      return domain;
    },

    _open_bookings_tree: function() {
      var $elm = this.$el.find('#pms-menu #bookings_search');
      var searchQuery = $elm.val();
      var domain = false;
      if (searchQuery) {
        domain = this._generate_bookings_domain(searchQuery);
      }

      this.do_action({
        type: 'ir.actions.act_window',
        view_mode: 'form',
        view_type: 'tree,form',
        res_model: 'hotel.reservation',
        views: [[false, 'list'], [false, 'form']],
        domain: domain,
        name: searchQuery?'Reservations for ' + searchQuery:'All Reservations'
      });

      $elm.val('');
    },
});

return HotelCalendarView;

});
