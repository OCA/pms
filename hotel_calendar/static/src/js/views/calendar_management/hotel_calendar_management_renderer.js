/* global $, odoo, _, HotelCalendar, moment */
// Copyright 2018 Alexandre Díaz <dev@redneboa.es>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
odoo.define('hotel_calendar.MPMSCalendarRenderer', function (require) {
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

var HotelCalendarManagementView = AbstractRenderer.extend({
    /** VIEW OPTIONS **/
    template: "hotel_calendar.HotelCalendarManagementView",
    display_name: _lt('Hotel Calendar Management'),
    icon: 'fa fa-map-marker',
    searchable: false,
    searchview_hidden: true,

    // Custom Options
    _view_options: {},
    _hcalendar: null,
    _last_dates: [false, false],
    _pricelist_id: null,
    _restriction_id: null,
    _days_tooltips: [],


    /** VIEW METHODS **/
    init: function(parent, state, params) {
      this._super.apply(this, arguments);

      this.model = params.model;
    },

    start: function () {
      var self = this;
      return this._super().then(function() {
          self.init_calendar_view();
          $(window).trigger('resize');
      });
    },

    do_show: function() {
        if (this.$ehcal) {
          this.$ehcal.show();
          $('.o_content').css('overflow', 'hidden');
        }
        this.do_push_state({});
        return this._super();
    },
    do_hide: function () {
        if (this.$ehcal) {
            this.$ehcal.hide();
            $('.o_content').css('overflow', '');
        }
        return this._super();
    },

    destroy: function () {
        return this._super.apply(this, arguments);
    },

    /** CUSTOM METHODS **/
    get_values_to_save: function() {
        var btn_save = this.$el.find('#btn_save_changes');
        if (!btn_save.hasClass('need-save')) {
            return false;
        }

        var pricelist = this._hcalendar.getPricelist(true);
        var restrictions = this._hcalendar.getRestrictions(true);

        var params = this.generate_params();
        return [params['prices'], params['restrictions'], pricelist, restrictions];
    },

    save_changes: function() {
        var oparams = this.get_values_to_save();
        if (oparams) {
            this.trigger_up('onSaveChanges', oparams);
         }
    },

    resetSaveState: function() {
        this.$el.find('#btn_save_changes').removeClass('need-save');
        $('.hcal-management-record-changed').removeClass('hcal-management-record-changed');
        $('.hcal-management-input-changed').removeClass('hcal-management-input-changed');
    },

    create_calendar: function(rooms) {
        var self = this;
        // CALENDAR
        if (this._hcalendar) {
            delete this._hcalendar;
        }
        this.$ehcal.empty();

        var options = {
            rooms: rooms,
            days: self._view_options['days'],
            endOfWeek: parseInt(self._view_options['eday_week']) || 6,
            endOfWeekOffset: self._view_options['eday_week_offset'] || 0,
            dateFormatLong: HotelConstants.ODOO_DATETIME_MOMENT_FORMAT,
            dateFormatShort: HotelConstants.ODOO_DATE_MOMENT_FORMAT,
            translations: {
                'Open': _t('Open'),
                'Closed': _t('Closed'),
                'C. Departure': _t('C. Departure'),
                'C. Arrival': _t('C. Arrival'),
                'Price': _t('Price'),
                'Availability': _t('Availability'),
                'Min. Stay': _t('Min. Stay'),
                'Max. Stay': _t('Max. Stay'),
                'Min. Stay Arrival': _t('Min. Stay Arrival'),
                'Max. Stay Arrival': _t('Max. Stay Arrival'),
                'Clousure': _t('Clousure'),
                'Free Rooms': _t('Free Rooms'),
                'No OTA': _t('No OTA'),
                'Options': _t('Options'),
                'Reset': _t('Reset'),
                'Copy': _t('Copy'),
                'Paste': _t('Paste'),
                'Clone': _t('Clone'),
                'Cancel': _t('Cancel')
            }
        };

        this._hcalendar = new HotelCalendarManagement('#hcal_management_widget', options, this.$el[0]);
        this._assignHCalendarEvents();

        this.$CalendarHeaderDays = this.$el.find("div.table-room_type-data-header");

        // Sticky Header Days
        $('.o_content').scroll(this._on_scroll.bind(this));

        // Initialize Save Button state to disable
        document.getElementById("btn_save_changes").disabled = true;
    },

    setCalendarData: function (prices, restrictions, availability, count_reservations) {
        this._hcalendar.setData(prices, restrictions, availability, count_reservations);
        this._assign_extra_info();
    },

    _assignHCalendarEvents: function () {
        var self = this;
        this._hcalendar.addEventListener('hcOnChangeDate', function(ev){
            var date_begin = moment(ev.detail.newDate);
            var $dateTimePickerBegin = self.$el.find('#mpms-search #date_begin');
            $dateTimePickerBegin.data("ignore_onchange", true);
            $dateTimePickerBegin.data("DateTimePicker").date(date_begin);
            self.reload_hcalendar_management();
        });
        this._hcalendar.addEventListener('hcmOnInputChanged', function(ev){
            var btn_save = self.$el.find('#btn_save_changes');
            if (self._hcalendar.hasChangesToSave()) {
                btn_save.addClass('need-save');
                document.getElementById("btn_save_changes").disabled = false;
            } else {
                btn_save.removeClass('need-save');
                document.getElementById("btn_save_changes").disabled = true;
            }
        });
    },

    _on_scroll: function() {
        var curScrollPos = $('.o_content').scrollTop();
        if (curScrollPos > 0) {
            this.$CalendarHeaderDays.css({
                top: `${curScrollPos-this.$ehcal.position().top}px`,
                position: 'sticky'
            });
        } else {
            this.$CalendarHeaderDays.css({
                top: '0px',
                position: 'initial'
            });
        }
    },

    loadViewFilters: function (resultsPricelist, resultsRestrictions) {
        var self = this;

        var $list = self.$el.find('#mpms-search #price_list');
        $list.html('');
        resultsPricelist.forEach(function(item, index){
            $list.append(`<option value="${item.id}" ${item.id==self._pricelist_id?'selected':''}>${item.name}</option>`);
        });
        $list.select2();
        $list.on('change', function(ev){
            self._check_unsaved_changes(function(){
                self.reload_hcalendar_management();
            });
        });

        $list = self.$el.find('#mpms-search #restriction_list');
        $list.html('');
        resultsRestrictions.forEach(function(item, index){
            $list.append(`<option value="${item.id}" ${item.id==self._restriction_id?'selected':''}>${item.name}</option>`);
        });
        $list.select2();
        $list.on('change', function(ev){
            self._check_unsaved_changes(function(){
                self.reload_hcalendar_management();
            });
        });

        $list = self.$el.find('#mpms-search #mode_list');
        $list.select2({
            minimumResultsForSearch: -1
        });
        $list.on('change', function(ev){
            var mode = HotelCalendarManagement.MODE.ALL;
            if (this.value === 'low') {
                mode = HotelCalendarManagement.MODE.LOW;
            } else if (this.value === 'medium') {
                mode = HotelCalendarManagement.MODE.MEDIUM;
            }
            self._hcalendar.setMode(mode);
        });
    },

    call_action: function(action) {
        this.do_action(action);
    },

    init_calendar_view: function(){
        var self = this;

        this.$ehcal = this.$el.find("div#hcal_management_widget");

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
            locale : moment.locale(),
            format : HotelConstants.L10N_DATE_MOMENT_FORMAT,
            //disabledHours: [0, 1, 2, 3, 4, 5, 6, 7, 8, 18, 19, 20, 21, 22, 23]
        };

        var $dateTimePickerBegin = this.$el.find('#mpms-search #date_begin');
        $dateTimePickerBegin.datetimepicker(DTPickerOptions);
        $dateTimePickerBegin.on("dp.change", function (e) {
            $dateTimePickerBegin.data("DateTimePicker").hide(); // TODO: Odoo uses old datetimepicker version
            self.on_change_filter_date(e, true);
        });

        var $dateEndDays = this.$el.find('#mpms-search #date_end_days');
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

        $dateEndDays.on("change", function (e) {
            self.on_change_filter_date();
        });

        // View Events
        this.$el.find("#mpms-search #cal-pag-prev-plus").on('click', function(ev){
            // FIXME: Ugly repeated code. Change place.
            var $dateTimePickerBegin = self.$el.find('#mpms-search #date_begin');
            var date_begin = $dateTimePickerBegin.data("DateTimePicker").date().subtract(14, 'd');
            $dateTimePickerBegin.data("ignore_onchange", true);
            $dateTimePickerBegin.data("DateTimePicker").date(date_begin);
            self.on_change_filter_date(ev, true);
            ev.preventDefault();
        });
        this.$el.find("#mpms-search #cal-pag-prev").on('click', function(ev){
            // FIXME: Ugly repeated code. Change place.
            var $dateTimePickerBegin = self.$el.find('#mpms-search #date_begin');
            var date_begin = $dateTimePickerBegin.data("DateTimePicker").date().subtract(7, 'd');
            $dateTimePickerBegin.data("ignore_onchange", true);
            $dateTimePickerBegin.data("DateTimePicker").date(date_begin);
            self.on_change_filter_date(ev, true);
            ev.preventDefault();
        });
        this.$el.find("#mpms-search #cal-pag-next-plus").on('click', function(ev){
            // FIXME: Ugly repeated code. Change place.
            var $dateTimePickerBegin = self.$el.find('#mpms-search #date_begin');
            var date_begin = $dateTimePickerBegin.data("DateTimePicker").date().add(14, 'd');
            $dateTimePickerBegin.data("ignore_onchange", true);
            $dateTimePickerBegin.data("DateTimePicker").date(date_begin);
            self.on_change_filter_date(ev, true);
            ev.preventDefault();
        });
        this.$el.find("#mpms-search #cal-pag-next").on('click', function(ev){
            // FIXME: Ugly repeated code. Change place.
            var $dateTimePickerBegin = self.$el.find('#mpms-search #date_begin');
            var date_begin = $dateTimePickerBegin.data("DateTimePicker").date().add(7, 'd');
            $dateTimePickerBegin.data("ignore_onchange", true);
            $dateTimePickerBegin.data("DateTimePicker").date(date_begin);
            self.on_change_filter_date(ev, true);
            ev.preventDefault();
        });
        this.$el.find("#mpms-search #cal-pag-selector").on('click', function(ev){
            // FIXME: Ugly repeated code. Change place.
            var $dateTimePickerBegin = self.$el.find('#mpms-search #date_begin');
            var date_begin = moment().startOf('day');
            $dateTimePickerBegin.data("ignore_onchange", true);
            $dateTimePickerBegin.data("DateTimePicker").date(date_begin);
            self.on_change_filter_date(ev, true);
            ev.preventDefault();
        });

        // Save Button
        this.$el.find("#btn_save_changes").on('click', function(ev) {
            document.getElementById(this.id).disabled = true;
            self.save_changes();
        });

        // Launch Massive Changes
        this.$el.find("#btn_massive_changes").on('click', function(ev){
          self.call_action("hotel.action_hotel_massive_change");
        });

        /** RENDER CALENDAR **/
        this.trigger_up('onLoadCalendarSettings');
    },

    setHCalendarSettings: function (results) {
        this._view_options = results;
        var date_begin = moment().startOf('day');
        if (['xs', 'md'].indexOf(this._findBootstrapEnvironment()) >= 0) {
            this._view_options['days'] = 7;
        } else {
            this._view_options['days'] = (this._view_options['days'] !== 'month')?parseInt(this._view_options['days']):date_begin.daysInMonth();
        }

        var $dateTimePickerBegin = this.$el.find('#mpms-search #date_begin');
        $dateTimePickerBegin.data("DateTimePicker").date(date_begin);

        var $dateEndDays = this.$el.find('#mpms-search #date_end_days');
        $dateEndDays.val('month');
        $dateEndDays.trigger('change');

        this._last_dates = this.generate_params()['dates'];
        this.trigger_up('onLoadCalendar');
    },

    on_change_filter_date: function(ev, isStartDate) {
        var self = this;
        isStartDate = isStartDate || false;
        var $dateTimePickerBegin = this.$el.find('#mpms-search #date_begin');
        var $dateEndDays = this.$el.find('#mpms-search #date_end_days');

        // FIXME: Hackish onchange ignore (Used when change dates from code)
        if ($dateTimePickerBegin.data("ignore_onchange") || $dateEndDays.data("ignore_onchange")) {
            $dateTimePickerBegin.data("ignore_onchange", false);
            $dateEndDays.data("ignore_onchange", false);
            return true;
        }

        var date_begin = $dateTimePickerBegin.data("DateTimePicker").date().set({'hour': 0, 'minute': 0, 'second': 0}).clone();

        if (this._hcalendar && date_begin) {
            var days = $dateEndDays.val();
            if (days === 'month') {
                days = date_begin.daysInMonth();
            }
            var date_end = date_begin.set({'hour': 23, 'minute': 59, 'second': 59}).clone().add(days, 'd');

            this._check_unsaved_changes(function(){
                self._hcalendar.setStartDate(date_begin, self._hcalendar.getDateDiffDays(date_begin, date_end));
                self.reload_hcalendar_management();
            });
        }
    },

    reload_hcalendar_management: function() {
        this.trigger_up('onLoadNewContentCalendar');
    },

    generate_params: function() {
        var fullDomain = [];
        var prices = this.$el.find('#mpms-search #price_list').val();
        var restrictions = this.$el.find('#mpms-search #restriction_list').val();

        var $dateTimePickerBegin = this.$el.find('#mpms-search #date_begin');
        var $dateEndDays = this.$el.find('#mpms-search #date_end_days');

        var date_begin = $dateTimePickerBegin.data("DateTimePicker").date().set({'hour': 0, 'minute': 0, 'second': 0}).clone();

        var days = $dateEndDays.val();
        if (days === 'month') {
          days = date_begin.daysInMonth();
        }
        var date_end = date_begin.set({'hour': 23, 'minute': 59, 'second': 59}).clone().add(days, 'd');
        return {
            'dates': [date_begin, date_end],
            'prices': prices,
            'restrictions': restrictions
        };
    },

    _check_unsaved_changes: function(fnCallback) {
        var self = this;
        var btn_save = this.$el.find("#btn_save_changes");
        if (!btn_save.hasClass('need-save')) {
            btn_save.removeClass('need-save');
            document.getElementById("btn_save_changes").disabled = true;
            fnCallback();
            return;
        }

        new Dialog(self, {
            title: _t("Unsaved Changes!"),
            buttons: [
                {
                    text: _t("Yes, save it"),
                    classes: 'btn-primary',
                    close: true,
                    click: function() {
                        document.getElementById("btn_save_changes").disabled = true;
                        self.save_changes();
                        fnCallback();
                    }
                },
                {
                    text: _t("No"),
                    close: true,
                    click: function() {
                        btn_save.removeClass('need-save');
                        document.getElementById("btn_save_changes").disabled = true;
                        fnCallback();
                    }
                }
            ],
            $content: QWeb.render('HotelCalendarManagement.UnsavedChanges', {})
        }).open();
    },

    _findBootstrapEnvironment: function() {
        var envs = ['xs', 'sm', 'md', 'lg'];

        var $el = $('<div>');
        $el.appendTo($('body'));

        for (var i = envs.length - 1; i >= 0; i--) {
            var env = envs[i];

            $el.addClass('hidden-'+env);
            if ($el.is(':hidden')) {
                $el.remove();
                return env;
            }
        }
    },

    _assign_extra_info: function() {
      var self = this;

      $(this._hcalendar.etableHeader).find('.hcal-cell-header-day').each(function(index, elm){
        var $elm = $(elm);
        var cdate = HotelCalendarManagement.toMoment($elm.data('hcalDate'), HotelConstants.L10N_DATE_MOMENT_FORMAT);
        var data = _.filter(self._days_tooltips, function(item) {
          var ndate = HotelCalendarManagement.toMoment(item[2], HotelConstants.ODOO_DATE_MOMENT_FORMAT);
          return ndate.isSame(cdate, 'd');
        });
        if (data.length > 0) {
          $elm.addClass('hcal-event-day');
          $elm.on("mouseenter", function(data){
            var $this = $(this);
            if (data.length > 0) {
              var qdict = {
                'date': $this.data('hcalDate'),
                'events': _.map(data, function(item){
                  return {
                    'name': item[1],
                    'date': item[2],
                    'location': item[3]
                  };
                })
              };
              $this.attr('title', '');
              $this.tooltip({
                  animation: true,
                  html: true,
                  placement: 'bottom',
                  title: QWeb.render('HotelCalendar.TooltipEvent', qdict)
              }).tooltip('show');
            }
          }.bind(elm, data));
        }
      });
    },
});

return HotelCalendarManagementView;

});
