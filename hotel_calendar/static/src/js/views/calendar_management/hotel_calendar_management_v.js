/* global $, odoo, _, HotelCalendarManagement, moment */
// Copyright 2018 Alexandre Díaz <dev@redneboa.es>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
odoo.define('hotel_calendar.HotelCalendarManagementView', function (require) {
"use strict";

var Core = require('web.core'),
    Bus = require('bus.bus').bus,
    //Data = require('web.data'),
    Time = require('web.time'),
    Model = require('web.DataModel'),
    View = require('web.View'),
    Widgets = require('web_calendar.widgets'),
    //Common = require('web.form_common'),
    //Pyeval = require('web.pyeval'),
    ActionManager = require('web.ActionManager'),
    Utils = require('web.utils'),
    Dialog = require('web.Dialog'),
    //Ajax = require('web.ajax'),
    ControlPanel = require('web.ControlPanel'),
    //Session = require('web.session'),
    formats = require('web.formats'),

    _t = Core._t,
    _lt = Core._lt,
    QWeb = Core.qweb,
    l10n = _t.database.parameters,

    ODOO_DATETIME_MOMENT_FORMAT = "YYYY-MM-DD HH:mm:ss",
    ODOO_DATE_MOMENT_FORMAT = "YYYY-MM-DD",
    L10N_DATE_MOMENT_FORMAT = "DD/MM/YYYY", //FIXME: Time.strftime_to_moment_format(l10n.date_format);
    L10N_DATETIME_MOMENT_FORMAT = L10N_DATE_MOMENT_FORMAT + ' ' + Time.strftime_to_moment_format(l10n.time_format);


/* HIDE CONTROL PANEL */
/* FIXME: Look's like a hackish solution */
ControlPanel.include({
    update: function(status, options) {
        if (typeof options.toHide === 'undefined')
            options.toHide = false;
        var action_stack = this.getParent().action_stack;
        if (action_stack && action_stack.length) {
            var active_action = action_stack[action_stack.length-1];
            if (active_action.widget && active_action.widget.active_view &&
                    active_action.widget.active_view.type === 'mpms'){
                options.toHide = true;
            }
        }
        this._super(status, options);
        this._toggle_visibility(!options.toHide);
    }
});

var HotelCalendarManagementView = View.extend({
    /** VIEW OPTIONS **/
    template: "hotel_calendar.HotelCalendarManagementView",
    display_name: _lt('Hotel Calendar Management'),
    icon: 'fa fa-map-marker',
    //view_type: "mpms",
    searchable: false,
    searchview_hidden: true,
    quick_create_instance: Widgets.QuickCreate,
    defaults: _.extend({}, View.prototype.defaults, {
        confirm_on_delete: true,
    }),

    // Custom Options
    _model: null,
    _hcalendar: null,
    _action_manager: null,
    _last_dates: [false, false],
    _pricelist_id: null,
    _restriction_id: null,
    _days_tooltips: [],

    /** VIEW METHODS **/
    init: function(parent, dataset, fields_view, options) {
        this._super.apply(this, arguments);
        this.shown = $.Deferred();
        this.dataset = dataset;
        this.model = dataset.model;
        this.view_type = 'mpms';
        this.selected_filters = [];
        this.mutex = new Utils.Mutex();
        this._model = new Model(this.dataset.model);
        this._action_manager = this.findAncestor(function(ancestor){ return ancestor instanceof ActionManager; });

        Bus.on("notification", this, this._on_bus_signal);
    },

    start: function () {
        this.shown.done(this._do_show_init.bind(this));
        return this._super();
    },

    _do_show_init: function () {
        this.init_calendar_view().then(function() {
            $(window).trigger('resize');
        });
    },

    do_show: function() {
        if (this.$ehcal) {
          this.$ehcal.show();
          $('.o_content').css('overflow', 'hidden');
        }
        this.do_push_state({});
        this.shown.resolve();
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
    save_changes: function() {
        var self = this;
        var btn_save = this.$el.find('#btn_save_changes');
        if (!btn_save.hasClass('need-save')) {
            return;
        }

        var pricelist = this._hcalendar.getPricelist(true);
        var restrictions = this._hcalendar.getRestrictions(true);
        var availability = this._hcalendar.getAvailability(true);

        var params = this.generate_params();
        var oparams = [false, params['prices'], params['restrictions'], pricelist, restrictions, availability];
        this._model.call('save_changes', oparams).then(function(results){
            btn_save.removeClass('need-save');
            $('.hcal-management-record-changed').removeClass('hcal-management-record-changed');
            $('.hcal-management-input-changed').removeClass('hcal-management-input-changed');
        });
    },

    create_calendar: function(options) {
        var self = this;
        // CALENDAR
        if (this._hcalendar) {
            delete this._hcalendar;
        }

        this.$ehcal.empty();

        this._hcalendar = new HotelCalendarManagement('#hcal_management_widget', options, this.$el[0]);
        this._hcalendar.addEventListener('hcOnChangeDate', function(ev){
            var date_begin = moment(ev.detail.newDate);
            var days = self._hcalendar.getOptions('days')-1;
            var date_end = date_begin.clone().add(days, 'd');

            var $dateTimePickerBegin = self.$el.find('#mpms-search #date_begin');
            var $dateTimePickerEnd = self.$el.find('#mpms-search #date_end');
            $dateTimePickerBegin.data("ignore_onchange", true);
            $dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
            $dateTimePickerEnd.data("DateTimePicker").setDate(date_end);

            self.reload_hcalendar_management();
        });
        this._hcalendar.addEventListener('hcmOnInputChanged', function(ev){
            var btn_save = self.$el.find('#btn_save_changes');
            if (self._hcalendar.hasChangesToSave()) {
                btn_save.addClass('need-save');
            } else {
                btn_save.removeClass('need-save');
            }
        });

        this.$CalendarHeaderDays = this.$el.find("div.table-room_type-data-header");

        // Sticky Header Days
        this.$ehcal.scroll(this._on_scroll.bind(this));
    },

    _on_scroll: function() {
        var curScrollPos = this.$ehcal.scrollTop();
        if (curScrollPos > 0) {
            this.$CalendarHeaderDays.css({
                top: `${curScrollPos}px`,
                position: 'sticky'
            });
        } else {
            this.$CalendarHeaderDays.css({
                top: '0px',
                position: 'initial'
            });
        }
    },

    generate_hotel_calendar: function(){
        var self = this;
        debugger;
        /** DO MAGIC **/
        var params = this.generate_params();
        var oparams = [params['dates'][0], params['dates'][1], false, false, true];
        this._model.call('get_hcalendar_all_data', oparams).then(function(results){
            self._days_tooltips = results['events'];
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
            self._pricelist_id = results['pricelist_id'];
            new Model('product.pricelist').query(['id','name']).all().then(function(resultsPricelist){
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
            });

            // Get Restrictions
            self._restriction_id = results['restriction_id'];
            new Model('hotel.room.type.restriction').query(['id','name']).all().then(function(resultsRestrictions){
                var $list = self.$el.find('#mpms-search #restriction_list');
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
            });

            // Calendar Mode
            var $list = self.$el.find('#mpms-search #mode_list');
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

            self.create_calendar({
                rooms: rooms,
                days: self._view_options['days'],
                endOfWeek: parseInt(self._view_options['eday_week']) || 6,
                endOfWeekOffset: self._view_options['eday_week_offset'] || 0,
                dateFormatLong: ODOO_DATETIME_MOMENT_FORMAT,
                dateFormatShort: ODOO_DATE_MOMENT_FORMAT,
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
            });
            self._hcalendar.setData(results['prices'], results['restrictions'], results['availability'], results['count_reservations']);
            self._assign_extra_info();
        });
    },

    call_action: function(action) {
        this._action_manager.do_action(action);
    },

    init_calendar_view: function(){
        var self = this;

        this.$ehcal = this.$el.find("div#hcal_management_widget");

        /** VIEW CONTROLS INITIALIZATION **/
        // DATE TIME PICKERS
        var l10nn = _t.database.parameters
        var DTPickerOptions = {
            viewMode: 'months',
            icons : {
                time: 'fa fa-clock-o',
                date: 'fa fa-calendar',
                up: 'fa fa-chevron-up',
                down: 'fa fa-chevron-down'
               },
            language : moment.locale(),
            format : L10N_DATE_MOMENT_FORMAT,
            disabledHours: true // TODO: Odoo uses old datetimepicker version
        };
        var $dateTimePickerBegin = this.$el.find('#mpms-search #date_begin');
        var $dateTimePickerEnd = this.$el.find('#mpms-search #date_end');
        $dateTimePickerBegin.datetimepicker(DTPickerOptions);
        $dateTimePickerEnd.datetimepicker($.extend({}, DTPickerOptions, { 'useCurrent': false }));
        $dateTimePickerBegin.on("dp.change", function (e) {
            $dateTimePickerEnd.data("DateTimePicker").setMinDate(e.date.add(3,'d'));
            $dateTimePickerEnd.data("DateTimePicker").setMaxDate(e.date.add(2,'M'));
            $dateTimePickerBegin.data("DateTimePicker").hide(); // TODO: Odoo uses old datetimepicker version
            self.on_change_filter_date(e, true);
        });
        $dateTimePickerEnd.on("dp.change", function (e) {
            self.on_change_filter_date(e, false);
            $dateTimePickerEnd.data("DateTimePicker").hide(); // TODO: Odoo uses old datetimepicker version
        });

        // var date_begin = moment().startOf('day');
        // var date_end = date_begin.clone().add(this._view_options['days'], 'd').endOf('day');
        // $dateTimePickerBegin.data("ignore_onchange", true);
        // $dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
        // $dateTimePickerEnd.data("DateTimePicker").setDate(date_end);
        // this._last_dates = this.generate_params()['dates'];

        // View Events
        this.$el.find("#mpms-search #cal-pag-prev-plus").on('click', function(ev){
            // FIXME: Ugly repeated code. Change place.
            var $dateTimePickerBegin = self.$el.find('#mpms-search #date_begin');
            var $dateTimePickerEnd = self.$el.find('#mpms-search #date_end');
            //var days = moment($dateTimePickerBegin.data("DateTimePicker").getDate()).clone().local().daysInMonth();
            var date_begin = $dateTimePickerBegin.data("DateTimePicker").getDate().subtract(14, 'd');
            var date_end = $dateTimePickerEnd.data("DateTimePicker").getDate().subtract(14, 'd');
            $dateTimePickerBegin.data("ignore_onchange", true);
            $dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
            $dateTimePickerEnd.data("DateTimePicker").setDate(date_end);

            ev.preventDefault();
        });
        this.$el.find("#mpms-search #cal-pag-prev").on('click', function(ev){
            // FIXME: Ugly repeated code. Change place.
            var $dateTimePickerBegin = self.$el.find('#mpms-search #date_begin');
            var $dateTimePickerEnd = self.$el.find('#mpms-search #date_end');
            var date_begin = $dateTimePickerBegin.data("DateTimePicker").getDate().subtract(7, 'd');
            var date_end = $dateTimePickerEnd.data("DateTimePicker").getDate().subtract(7, 'd');
            $dateTimePickerBegin.data("ignore_onchange", true);
            $dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
            $dateTimePickerEnd.data("DateTimePicker").setDate(date_end);

            ev.preventDefault();
        });
        this.$el.find("#mpms-search #cal-pag-next-plus").on('click', function(ev){
            // FIXME: Ugly repeated code. Change place.
            var $dateTimePickerBegin = self.$el.find('#mpms-search #date_begin');
            var $dateTimePickerEnd = self.$el.find('#mpms-search #date_end');
            //var days = moment($dateTimePickerBegin.data("DateTimePicker").getDate()).clone().local().daysInMonth();
            var date_begin = $dateTimePickerBegin.data("DateTimePicker").getDate().add(14, 'd');
            var date_end = $dateTimePickerEnd.data("DateTimePicker").getDate().add(14, 'd');
            $dateTimePickerBegin.data("ignore_onchange", true);
            $dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
            $dateTimePickerEnd.data("DateTimePicker").setDate(date_end);

            ev.preventDefault();
        });
        this.$el.find("#mpms-search #cal-pag-next").on('click', function(ev){
            // FIXME: Ugly repeated code. Change place.
            var $dateTimePickerBegin = self.$el.find('#mpms-search #date_begin');
            var $dateTimePickerEnd = self.$el.find('#mpms-search #date_end');
            var date_begin = $dateTimePickerBegin.data("DateTimePicker").getDate().add(7, 'd');
            var date_end = $dateTimePickerEnd.data("DateTimePicker").getDate().add(7, 'd');
            $dateTimePickerBegin.data("ignore_onchange", true);
            $dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
            $dateTimePickerEnd.data("DateTimePicker").setDate(date_end);

            ev.preventDefault();
        });
        this.$el.find("#mpms-search #cal-pag-selector").on('click', function(ev){
            // FIXME: Ugly repeated code. Change place.
            var $dateTimePickerBegin = self.$el.find('#mpms-search #date_begin');
            var $dateTimePickerEnd = self.$el.find('#mpms-search #date_end');
            var date_begin = moment().startOf('day');
            var date_end = date_begin.clone().add(self._view_options['days'], 'd').endOf('day');
            $dateTimePickerBegin.data("ignore_onchange", true);
            $dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
            $dateTimePickerEnd.data("DateTimePicker").setDate(date_end);

            ev.preventDefault();
        });

        // Save Button
        this.$el.find("#btn_save_changes").on('click', function(ev){
            self.save_changes();
        });

        // Launch Massive Changes
        this.$el.find("#btn_massive_changes").on('click', function(ev){
          self.call_action("hotel.action_hotel_massive_change");
        });

        /** RENDER CALENDAR **/
        this._model.call('get_hcalendar_settings', [false]).then(function(results){
            self._view_options = results;
            var date_begin = moment().startOf('day');
            if (['xs', 'md'].indexOf(self._findBootstrapEnvironment()) >= 0) {
                self._view_options['days'] = 7;
            } else {
                self._view_options['days'] = (self._view_options['days'] !== 'month')?parseInt(self._view_options['days']):date_begin.daysInMonth();
            }
            var date_end = date_begin.clone().add(self._view_options['days'], 'd').endOf('day');
            var $dateTimePickerBegin = self.$el.find('#mpms-search #date_begin');
            var $dateTimePickerEnd = self.$el.find('#mpms-search #date_end');
            //$dateTimePickerBegin.data("ignore_onchange", true);
            $dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
            //$dateTimePickerEnd.data("ignore_onchange", true);
            $dateTimePickerEnd.data("DateTimePicker").setDate(date_end);
            self._last_dates = self.generate_params()['dates'];

            self.generate_hotel_calendar();
        });

        return $.when();
    },

    on_change_filter_date: function(ev, isStartDate) {
        var self = this;
        isStartDate = isStartDate || false;
        var $dateTimePickerBegin = this.$el.find('#mpms-search #date_begin');
        var $dateTimePickerEnd = this.$el.find('#mpms-search #date_end');

        // FIXME: Hackish onchange ignore (Used when change dates from code)
        if ($dateTimePickerBegin.data("ignore_onchange") || $dateTimePickerEnd.data("ignore_onchange")) {
            $dateTimePickerBegin.data("ignore_onchange", false);
            $dateTimePickerEnd.data("ignore_onchange", false)
            return true;
        }

        var date_begin = $dateTimePickerBegin.data("DateTimePicker").getDate().set({'hour': 0, 'minute': 0, 'second': 0}).clone();

        if (this._hcalendar && date_begin) {
            if (isStartDate) {
                var ndate_end = date_begin.clone().add(this._view_options['days'], 'd');
                $dateTimePickerEnd.data("ignore_onchange", true);
                $dateTimePickerEnd.data("DateTimePicker").setDate(ndate_end.local());
            }

            var date_end = $dateTimePickerEnd.data("DateTimePicker").getDate().set({'hour': 23, 'minute': 59, 'second': 59}).clone();

            this._check_unsaved_changes(function(){
                self._hcalendar.setStartDate(date_begin, self._hcalendar.getDateDiffDays(date_begin, date_end));
                self.reload_hcalendar_management();
            });
        }
    },

    _on_bus_signal: function(notifications) {
        if (!this._hcalendar) {
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
                        this._hcalendar.addAvailability(availability);
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
                        this._hcalendar.addPricelist(pr);
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
                        this._hcalendar.addRestrictions(rest);
                        break;
                }
            }
        }
    },

    reload_hcalendar_management: function() {
        var self = this;
        var params = this.generate_params();
        var oparams = [params['dates'][0], params['dates'][1], params['prices'], params['restrictions'], false];
        this._model.call('get_hcalendar_all_data', oparams).then(function(results){
            self._days_tooltips = results['events'];
            self._hcalendar.setData(results['prices'], results['restrictions'], results['availability'], results['count_reservations']);
            self._assign_extra_info();
        });
        this._last_dates = params['dates'];
        this.$CalendarHeaderDays = this.$el.find("div.table-room_type-data-header");
        this._on_scroll(); // FIXME: Workaround for update sticky header
    },

    generate_params: function() {
        var fullDomain = [];
        var prices = this.$el.find('#mpms-search #price_list').val();
        var restrictions = this.$el.find('#mpms-search #restriction_list').val();

        var $dateTimePickerBegin = this.$el.find('#mpms-search #date_begin');
        var $dateTimePickerEnd = this.$el.find('#mpms-search #date_end');

        var date_begin = $dateTimePickerBegin.data("DateTimePicker").getDate().set({'hour': 0, 'minute': 0, 'second': 0}).clone().utc().format(ODOO_DATE_MOMENT_FORMAT);
        var date_end = $dateTimePickerEnd.data("DateTimePicker").getDate().set({'hour': 23, 'minute': 59, 'second': 59}).clone().utc().format(ODOO_DATE_MOMENT_FORMAT);

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
                        self.save_changes();
                        fnCallback();
                    }
                },
                {
                    text: _t("No"),
                    close: true,
                    click: function() {
                        btn_save.removeClass('need-save');
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
        var cdate = HotelCalendar.toMoment($elm.data('hcalDate'), L10N_DATE_MOMENT_FORMAT);
        var data = _.filter(self._days_tooltips, function(item) {
          var ndate = HotelCalendar.toMoment(item[2], ODOO_DATE_MOMENT_FORMAT);
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

Core.view_registry.add('mpms', HotelCalendarManagementView);
return HotelCalendarManagementView;

});
