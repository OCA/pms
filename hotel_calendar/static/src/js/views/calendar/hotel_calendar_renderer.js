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
        var $dateTimePickerBegin = this.$el.find('#pms-menu #date_begin');
        var $dateEndDays = this.$el.find('#pms-menu #date_end_days');
        var date_begin = $dateTimePickerBegin.data("DateTimePicker").date().clone();
        var days = $dateEndDays.val();
        if (days === 'month') {
          days = date_begin.daysInMonth();
        }
        var date_end = date_begin.clone().add(days, 'd');
        return [date_begin, date_end];
    },

    update_buttons_counter: function(ncheckouts, ncheckins, noverbookings, ncancelled) {
        var self = this;
         // Checkouts Button
        var $ninfo = self.$el.find('#pms-menu #btn_action_checkout span.ninfo');
        $ninfo.text(ncheckouts);

        // Checkins Button
        $ninfo = self.$el.find('#pms-menu #btn_action_checkin span.ninfo');
        $ninfo.text(ncheckins);

        // OverBookings
        $ninfo = self.$el.find('#pms-menu #btn_action_overbooking span.ninfo');
        $ninfo.text(noverbookings);
        if (noverbookings) {
            $ninfo.parent().parent().addClass('overbooking-highlight');
        } else {
            $ninfo.parent().parent().removeClass('overbooking-highlight');
        }

        // Cancelled
        $ninfo = self.$el.find('#pms-menu #btn_action_cancelled span.ninfo');
        $ninfo.text(ncancelled);
        if (ncancelled) {
            $ninfo.parent().parent().addClass('cancelled-highlight');
        } else {
            $ninfo.parent().parent().removeClass('cancelled-highlight');
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
            widgetPositioning:{
        horizontal: 'auto',
        vertical: 'bottom'
    }
        };
        var $dateTimePickerBegin = this.$el.find('#pms-menu #date_begin');
        var $dateEndDays = this.$el.find('#pms-menu #date_end_days');
        $dateTimePickerBegin.datetimepicker(DTPickerOptions);
        $dateEndDays.select2({
            data: [
                {id:7, text: '1w'},
                {id:12, text: '2w'},
                {id:21, text: '3w'},
                {id:'month', text: '1m'},
                {id:60, text: '2m'},
                {id:90, text: '3m'},
            ],
            allowClear: true,
            minimumResultsForSearch: -1
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
              $dateTimePickerBegin.data("DateTimePicker").date(date_begin);
            }
          }
        });

        /* BUTTONS */
        var $button = this.$el.find('#pms-menu #btn_action_bookings');
        $button.on('click', function(ev){ self._open_search_tree('book'); });
        $button = this.$el.find('#pms-menu #btn_action_checkins');
        $button.on('click', function(ev){ self._open_search_tree('checkin'); });
        $button = this.$el.find('#pms-menu #btn_action_invoices');
        $button.on('click', function(ev){ self._open_search_tree('invoice'); });
        $button = this.$el.find('#pms-menu #btn_action_folios');
        $button.on('click', function(ev){ self._open_search_tree('folio'); });
        // $button = this.$el.find('#pms-menu #bookings_search');
        // $button.on('keypress', function(ev){
        //   if (ev.keyCode === 13) {
        //      self._open_bookings_tree();
        //   }
        // });

        this.$el.find("button[data-action]").on('click', function(ev){
          self.do_action(this.dataset.action);
        });

        return $.when(
            this.trigger_up('onUpdateButtonsCounter'),
            this.trigger_up('onLoadViewFilters'),
        );
    },

    loadViewFilters: function(resultsHotelRoomType, resultsHotelFloor, resultsHotelRoomAmenities, resultsHotelVirtualRooms) {
        var $list = this.$el.find('#pms-menu #type_list');
        $list.html('');
        resultsHotelRoomType.forEach(function(item, index){
            $list.append(`<option value="${item.id}">${item.name}</option>`);
        });
        $list.select2();
        $list.on('change', function(ev){
            this.trigger_up('onApplyFilters');
        }.bind(this));

        // Get Floors
        $list = this.$el.find('#pms-menu #floor_list');
        $list.html('');
        resultsHotelFloor.forEach(function(item, index){
            $list.append(`<option value="${item.id}">${item.name}</option>`);
        });
        $list.select2();
        $list.on('change', function(ev){
            this.trigger_up('onApplyFilters');
        }.bind(this));

        // Get Amenities
        $list = this.$el.find('#pms-menu #amenities_list');
        $list.html('');
        resultsHotelRoomAmenities.forEach(function(item, index){
            $list.append(`<option value="${item.id}">${item.name}</option>`);
        });
        $list.select2();
        $list.on('change', function(ev){
            this.trigger_up('onApplyFilters');
        }.bind(this));

        // Get Virtual Rooms
        $list = this.$el.find('#pms-menu #virtual_list');
        $list.html('');
        resultsHotelVirtualRooms.forEach(function(item, index){
            $list.append(`<option value="${item.id}">${item.name}</option>`);
        });
        $list.select2();
        $list.on('change', function(ev){
            this.trigger_up('onApplyFilters');
        }.bind(this));
    },

    _generate_search_domain: function(tsearch, type) {
      var domain = [];
      domain.push('|', '|', '|', '|',
                  ['partner_id.name', 'ilike', tsearch],
                  ['partner_id.mobile', 'ilike', tsearch],
                  ['partner_id.vat', 'ilike', tsearch],
                  ['partner_id.email', 'ilike', tsearch],
                  ['partner_id.phone', 'ilike', tsearch]);
      if (type === 'invoice') {
        domain.splice(0, 0, '|');
        domain.push(['number', 'ilike', tsearch]);
      }
      return domain;
    },

    _generate_search_res_model: function(type) {
      var model = '';
      var title = '';
      if (type === 'book') {
        model = 'hotel.reservation';
        title = _t('Reservations');
      } else if (type === 'checkin') {
        model = 'hotel.checkin.partner';
        title = _t('Checkins');
      } else if (type === 'invoice') {
        model = 'account.invoice';
        title = _t('Invoices');
      } else if (type === 'folio') {
        model = 'hotel.folio'
        title = _t('Folios');
      }
      return [model, title];
    },

    _open_search_tree: function(type) {
      var $elm = this.$el.find('#pms-menu #bookings_search');
      var searchQuery = $elm.val();
      var domain = false;
      if (searchQuery) {
        domain = this._generate_search_domain(searchQuery, type);
      } else {
        domain = [];
      }

      var [model, title] = this._generate_search_res_model(type);

      this.do_action({
        type: 'ir.actions.act_window',
        view_mode: 'form',
        view_type: 'tree,form',
        res_model: model,
        views: [[false, 'list'], [false, 'form']],
        domain: domain,
        name: searchQuery?`${title} for ${searchQuery}`:`All ${title}`
      });

      $elm.val('');
    },
});

return HotelCalendarView;

});
