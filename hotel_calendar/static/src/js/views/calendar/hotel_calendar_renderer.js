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
    _hcalendar: null,
    _reserv_tooltips: {},
    _days_tooltips: [],
    _last_dates: [false, false],


    /** VIEW METHODS **/
    init: function(parent, state, params) {
      this._super.apply(this, arguments);
    },

    start: function () {
      return this._super().then(function() {
          this.init_calendar_view();
      }.bind(this));
    },

    on_attach_callback: function() {
      this._super();

      if (this._hcalendar && !this._is_visible) {
        // FIXME: Workaround for restore "lost" reservations (Drawn when the view is hidden)
        setTimeout(function(){
          for (var reserv of this._hcalendar._reservations) {
            var style = window.getComputedStyle(reserv._html, null);
            if (parseInt(style.width, 10) < 15 || parseInt(style.height, 10) < 15 || parseInt(style.top, 10) === 0) {
              this._hcalendar._updateReservation(reserv);
            }
          }
        }.bind(this), 300);
      }
    },

    /** CUSTOM METHODS **/
    _generate_reservation_tooltip_dict: function(tp) {
      return {
        'name': tp[0],
        'phone': tp[1],
        'arrival_hour': HotelCalendar.toMomentUTC(tp[2], HotelConstants.ODOO_DATETIME_MOMENT_FORMAT).local().format('HH:mm'),
        'num_split': tp[3],
        'amount_total': Number(tp[4]).toLocaleString()
      };
    },

    load_reservations: function(reservs) {
        this._hcalendar.setReservations(reservs);
        this._assign_extra_info();
    },

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
        if (['xs', 'md'].indexOf(this._find_bootstrap_environment()) >= 0) {
          this._view_options['days'] = 7;
        } else {
          this._view_options['days'] = (this._view_options['days'] !== 'month')?parseInt(this._view_options['days']):date_begin.daysInMonth();
        }
        var date_end = date_begin.clone().add(this._view_options['days'], 'd').endOf('day');
        var $dateTimePickerBegin = this.$el.find('#pms-search #date_begin');
        var $dateTimePickerEnd = this.$el.find('#pms-search #date_end');
        //$dateTimePickerBegin.data("ignore_onchange", true);
        $dateTimePickerBegin.data("DateTimePicker").date(date_begin);
        //$dateTimePickerEnd.data("ignore_onchange", true);
        $dateTimePickerEnd.data("DateTimePicker").date(date_end);
        this._last_dates = this.get_view_filter_dates();
    },

    destroy_calendar: function() {
        if (this._hcalendar) {
            this._hcalendar.$base.empty();
            delete this._hcalendar;
        }
    },

    create_calendar: function(containerSelector, rooms, pricelist, restrictions) {
        this.destroy_calendar();

        var options = {
            startDate: HotelCalendar.toMomentUTC(this._last_dates[0], HotelConstants.ODOO_DATETIME_MOMENT_FORMAT),
            days: this._view_options['days'] + 1,
            rooms: rooms,
            endOfWeek: parseInt(this._view_options['eday_week']) || 6,
            divideRoomsByCapacity: this._view_options['divide_rooms_by_capacity'] || false,
            allowInvalidActions: this._view_options['allow_invalid_actions'] || false,
            assistedMovement: this._view_options['assisted_movement'] || false,
            showPricelist: this._view_options['show_pricelist'] || false,
            showAvailability: this._view_options['show_availability'] || false,
            showNumRooms: this._view_options['show_num_rooms'] || 0,
            endOfWeekOffset: this._view_options['eday_week_offset'] || 0
        };

        this._hcalendar = new HotelCalendar(containerSelector, options, pricelist, restrictions, this.$el[0]);
        this._assign_hcalendar_events();
    },

    _assign_hcalendar_events: function() {
        var self = this;
        this._hcalendar.addEventListener('hcalOnSavePricelist', function(ev){
          var pricelist = self._hcalendar.getPricelist();
          var oparams = [self._hcalendar._pricelist_id, false, pricelist, {}, {}];
          self.trigger_up('onSaveChanges', oparams);
        });
        this._hcalendar.addEventListener('hcalOnMouseEnterReservation', function(ev){
          if (ev.detail.reservationObj) {
            var tp = self._reserv_tooltips[ev.detail.reservationObj.id];
            var qdict = self._generate_reservation_tooltip_dict(tp);
            $(ev.detail.reservationDiv).tooltip('destroy').tooltip({
              animation: false,
              html: true,
              placement: 'bottom',
              title: QWeb.render('HotelCalendar.TooltipReservation', qdict)
            }).tooltip('show');
          }
        });
        this._hcalendar.addEventListener('hcalOnClickReservation', function(ev){
            //var res_id = ev.detail.reservationObj.getUserData('folio_id');
            $(ev.detail.reservationDiv).tooltip('hide');
            self.do_action({
              type: 'ir.actions.act_window',
              res_model: 'hotel.reservation',
              res_id: ev.detail.reservationObj.id,
              views: [[false, 'form']]
            });
            // self._model.call('get_formview_id', [res_id, Session.user_context]).then(function(view_id){
            //     var pop = new ViewDialogs.FormViewDialog(self, {
            //         res_model: 'hotel.folio',
            //         res_id: res_id,
            //         title: _t("Open: ") + ev.detail.reservationObj.title,
            //         view_id: view_id
            //         //readonly: false
            //     }).open();
            //     pop.on('write_completed', self, function(){
            //         self.trigger('changed_value');
            //     });
            // });
        });
        this._hcalendar.addEventListener('hcalOnSwapReservations', function(ev){
          var qdict = {};
          var dialog = new Dialog(self, {
              title: _t("Confirm Reservation Swap"),
              buttons: [
                  {
                    text: _t("Yes, swap it"),
                    classes: 'btn-primary',
                    close: true,
                    click: function () {
                      if (self._hcalendar.swapReservations(ev.detail.inReservs, ev.detail.outReservs)) {
                        var fromIds = _.pluck(ev.detail.inReservs, 'id');
                        var toIds = _.pluck(ev.detail.outReservs, 'id');
                        var refFromReservDiv = ev.detail.inReservs[0]._html;
                        var refToReservDiv = ev.detail.outReservs[0]._html;

                        // Animate Movement
                        for (var nreserv of ev.detail.inReservs) {
                          $(nreserv._html).animate({'top': refToReservDiv.style.top});
                        }
                        for (var nreserv of ev.detail.outReservs) {
                          $(nreserv._html).animate({'top': refFromReservDiv.style.top});
                        }
                        self.trigger_up('onSwapReservations', {
                            'fromIds': fromIds,
                            'toIds': toIds,
                            'detail': ev.detail,
                            'refFromReservDiv': refFromReservDiv,
                            'refToReservDiv': refToReservDiv
                        });
                      } else {
                        var qdict = {};
                        var dialog = new Dialog(self, {
                          title: _t("Invalid Reservation Swap"),
                          buttons: [
                            {
                              text: _t("Oops, Ok!"),
                              classes: 'btn-primary',
                              close: true
                            }
                          ],
                          $content: QWeb.render('HotelCalendar.InvalidSwapOperation', qdict)
                        }).open();
                      }
                    }
                  },
                  {
                    text: _t("No"),
                    close: true
                  }
              ],
              $content: QWeb.render('HotelCalendar.ConfirmSwapOperation', qdict)
          }).open();
        });
        this._hcalendar.addEventListener('hcalOnCancelSwapReservations', function(ev){
          $("#btn_swap span.ntext").html(_t("START SWAP"));
          $("#btn_swap").css({
            'backgroundColor': '',
            'fontWeight': 'normal'
          });
        });
        this._hcalendar.addEventListener('hcalOnChangeReservation', function(ev){
            var newReservation = ev.detail.newReserv;
            var oldReservation = ev.detail.oldReserv;
            var oldPrice = ev.detail.oldPrice;
            var newPrice = ev.detail.newPrice;
            var folio_id = newReservation.getUserData('folio_id');

            var linkedReservs = _.find(self._hcalendar._reservations, function(item){
                return item.id !== newReservation.id && !item.unusedZone && item.getUserData('folio_id') === folio_id;
            });

            var hasChanged = false;

            var qdict = {
                ncheckin: newReservation.startDate.clone().local().format(HotelConstants.L10N_DATETIME_MOMENT_FORMAT),
                ncheckout: newReservation.endDate.clone().local().format(HotelConstants.L10N_DATETIME_MOMENT_FORMAT),
                nroom: newReservation.room.number,
                nprice: newPrice,
                ocheckin: oldReservation.startDate.clone().local().format(HotelConstants.L10N_DATETIME_MOMENT_FORMAT),
                ocheckout: oldReservation.endDate.clone().local().format(HotelConstants.L10N_DATETIME_MOMENT_FORMAT),
                oroom: oldReservation.room.number,
                oprice: oldPrice,
                hasReservsLinked: (linkedReservs && linkedReservs.length !== 0)?true:false
            };
            var dialog = new Dialog(self, {
                title: _t("Confirm Reservation Changes"),
                buttons: [
                    {
                        text: _t("Yes, change it"),
                        classes: 'btn-primary',
                        close: true,
                        disabled: !newReservation.id,
                        click: function () {
                            var roomId = newReservation.room.id;
                            if (newReservation.room.overbooking) {
                              roomId = +newReservation.room.id.substr(newReservation.room.id.indexOf('@')+1);
                            }
                            var write_values = {
                                'checkin': newReservation.startDate.format(HotelConstants.ODOO_DATETIME_MOMENT_FORMAT),
                                'checkout': newReservation.endDate.format(HotelConstants.ODOO_DATETIME_MOMENT_FORMAT),
                                'room_id': roomId,
                                'overbooking': newReservation.room.overbooking
                            };
                            self.trigger_up('onUpdateReservations', {
                                'ids': [newReservation.id],
                                'values': write_values,
                                'oldReservation': oldReservation,
                                'newReservation': newReservation
                            });
                            // Workarround for dispatch room lines regeneration
                            // new Model('hotel.reservation').call('on_change_checkin_checkout_product_id', [[newReservation.id], false]);
                            hasChanged = true;
                        }
                    },
                    {
                        text: _t("No"),
                        close: true,
                    }
                ],
                $content: QWeb.render('HotelCalendar.ConfirmReservationChanges', qdict)
            }).open();
            dialog.opened(function(e){
              if (!hasChanged) {
                self._hcalendar.replaceReservation(newReservation, oldReservation);
              }
            });
        });
        this._hcalendar.addEventListener('hcalOnUpdateSelection', function(ev){
        	for (var td of ev.detail.old_cells) {
        		$(td).tooltip('destroy');
        	}
        	if (ev.detail.cells.length > 1) {
	        	var last_cell = ev.detail.cells[ev.detail.cells.length-1];
	        	var date_cell_start = HotelCalendar.toMoment(self._hcalendar.etable.querySelector(`#${ev.detail.cells[0].dataset.hcalParentCell}`).dataset.hcalDate);
	        	var date_cell_end = HotelCalendar.toMoment(self._hcalendar.etable.querySelector(`#${last_cell.dataset.hcalParentCell}`).dataset.hcalDate);
                var parentRow = document.querySelector(`#${ev.detail.cells[0].dataset.hcalParentRow}`);
                var room = self._hcalendar.getRoom(parentRow.dataset.hcalRoomObjId);
                if (room.overbooking) {
                  return;
                }
                var nights = date_cell_end.diff(date_cell_start, 'days');
	        	var qdict = {
	        		//'total_price': Number(ev.detail.totalPrice).toLocaleString(),
	        		'nights': nights
	        	};
	        	$(last_cell).tooltip({
	                animation: false,
	                html: true,
	                placement: 'top',
	                title: QWeb.render('HotelCalendar.TooltipSelection', qdict)
	            }).tooltip('show');
        	}
        });
        this._hcalendar.addEventListener('hcalOnChangeSelection', function(ev){
            var parentRow = document.querySelector(`#${ev.detail.cellStart.dataset.hcalParentRow}`);
            var parentCellStart = document.querySelector(`#${ev.detail.cellStart.dataset.hcalParentCell}`);
            var parentCellEnd = document.querySelector(`#${ev.detail.cellEnd.dataset.hcalParentCell}`);
            var startDate = HotelCalendar.toMoment(parentCellStart.dataset.hcalDate);
            var endDate = HotelCalendar.toMoment(parentCellEnd.dataset.hcalDate);
            var room = self._hcalendar.getRoom(parentRow.dataset.hcalRoomObjId);
            if (room.overbooking) {
              return;
            }
            var numBeds = (room.shared || self._hcalendar.getOptions('divideRoomsByCapacity'))?(ev.detail.cellEnd.dataset.hcalBedNum - ev.detail.cellStart.dataset.hcalBedNum)+1:room.capacity;
            if (numBeds <= 0) {
                return;
            }

            // Normalize Dates
            if (startDate.isAfter(endDate)) {
                var tt = endDate;
                endDate = startDate;
                startDate = tt;
            }

            var def_arrival_hour = self._view_options['default_arrival_hour'].split(':');
            var def_departure_hour = self._view_options['default_departure_hour'].split(':');
            startDate.set({'hour': def_arrival_hour[0], 'minute': def_arrival_hour[1], 'second': 0});
            endDate.set({'hour': def_departure_hour[0], 'minute': def_departure_hour[1], 'second': 0});

            var popCreate = new ViewDialogs.FormViewDialog(self, {
                res_model: 'hotel.reservation',
                context: {
                  'default_checkin': startDate.utc().format(HotelConstants.ODOO_DATETIME_MOMENT_FORMAT),
                  'default_checkout': endDate.utc().format(HotelConstants.ODOO_DATETIME_MOMENT_FORMAT),
                  'default_adults': numBeds,
                  'default_children': 0,
                  'default_room_id': room.id,
                  'default_room_type_id': room.getUserData('room_type_id'),
                },
                title: _t("Create: ") + _t("Reservation"),
                initial_view: "form",
                disable_multiple_selection: true,
            }).open();
        });

        this._hcalendar.addEventListener('hcalOnDateChanged', function(ev){
          var $dateTimePickerBegin = this.$el.find('#pms-search #date_begin');
          var $dateTimePickerEnd = this.$el.find('#pms-search #date_end');
          $dateTimePickerBegin.data("ignore_onchange", true);
          $dateTimePickerEnd.data("DateTimePicker").minDate(false);
          $dateTimePickerEnd.data("DateTimePicker").maxDate(false);
          $dateTimePickerBegin.data("DateTimePicker").date(ev.detail.date_begin.local().add(1, 'd'));
          $dateTimePickerEnd.data("ignore_onchange", true);
          $dateTimePickerEnd.data("DateTimePicker").date(ev.detail.date_end.local());
          this.reload_hcalendar_reservations(false);
        }.bind(this));
    },

    _assign_extra_info: function() {
    	var self = this;
      $(this._hcalendar.etable).find('.hcal-cell-room-type-group-item.btn-hcal-3d').on("mouseenter", function(){
          var $this = $(this);
          var room = self._hcalendar.getRoom($this.parent().data("hcalRoomObjId"));
          if (room.overbooking) {
            $this.tooltip({
                animation: true,
                html: true,
                placement: 'right',
                title: QWeb.render('HotelCalendar.TooltipRoomOverbooking', {'name': room.number})
            }).tooltip('show');
          return;
        } else {
            var qdict = {
                'room_type_name': room.getUserData('room_type_name'),
                'name': room.number
            };
            $this.tooltip({
                animation: true,
                html: true,
                placement: 'right',
                title: QWeb.render('HotelCalendar.TooltipRoom', qdict)
            }).tooltip('show');
        }
      });

      $(this._hcalendar.etableHeader).find('.hcal-cell-header-day').each(function(index, elm){
        var $elm = $(elm);
        var cdate = HotelCalendar.toMoment($elm.data('hcalDate'), HotelConstants.L10N_DATE_MOMENT_FORMAT);
        var data = _.filter(self._days_tooltips, function(item) {
          var ndate = HotelCalendar.toMoment(item[2], HotelConstants.ODOO_DATE_MOMENT_FORMAT);
          return ndate.isSame(cdate, 'd');
        });
        if (data.length > 0) {
          $elm.addClass('hcal-event-day');
          $elm.prepend("<i class='fa fa-bell' style='margin-right: 0.1em'></i>");
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
        $dateTimePickerBegin.on("dp.change", function (e) {
            $dateTimePickerEnd.data("DateTimePicker").minDate(e.date.clone().add(3,'d'));
            $dateTimePickerEnd.data("DateTimePicker").maxDate(e.date.clone().add(2,'M'));
            $dateTimePickerBegin.data("DateTimePicker").hide();
            self.on_change_filter_date(true);
        });
        $dateTimePickerEnd.on("dp.change", function (e) {
            $dateTimePickerEnd.data("DateTimePicker").hide();
            self.on_change_filter_date(false);
        });

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

        this.$el.find("#btn_swap").on('click', function(ev){
          var hcalSwapMode = self._hcalendar.getSwapMode();
          if (hcalSwapMode === HotelCalendar.MODE.NONE) {
            self._hcalendar.setSwapMode(HotelCalendar.MODE.SWAP_FROM);
            $("#btn_swap span.ntext").html(_t("CONTINUE"));
            $("#btn_swap").css({
              'backgroundColor': 'rgb(145, 255, 0)',
              'fontWeight': 'bold'
            });
          } else if (self._hcalendar.getReservationAction().inReservations.length > 0 && hcalSwapMode === HotelCalendar.MODE.SWAP_FROM) {
            self._hcalendar.setSwapMode(HotelCalendar.MODE.SWAP_TO);
            $("#btn_swap span.ntext").html(_t("END"));
            $("#btn_swap").css({
              'backgroundColor': 'orange',
              'fontWeight': 'bold'
            });
          } else {
            self._hcalendar.setSwapMode(HotelCalendar.MODE.NONE);
            $("#btn_swap span.ntext").html(_t("START SWAP"));
            $("#btn_swap").css({
              'backgroundColor': '',
              'fontWeight': ''
            });
          }
        });

        return $.when(
            this.trigger_up('onLoadCalendarSettings'),
            this.trigger_up('onUpdateButtonsCounter'),
            this.trigger_up('onLoadCalendar'),
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
            this._apply_filters();
        }.bind(this));

        // Get Floors
        $list = this.$el.find('#pms-search #floor_list');
        $list.html('');
        resultsHotelFloor.forEach(function(item, index){
            $list.append(`<option value="${item.id}">${item.name}</option>`);
        });
        $list.select2();
        $list.on('change', function(ev){
            this._apply_filters();
        }.bind(this));

        // Get Amenities
        $list = this.$el.find('#pms-search #amenities_list');
        $list.html('');
        resultsHotelRoomAmenities.forEach(function(item, index){
            $list.append(`<option value="${item.id}">${item.name}</option>`);
        });
        $list.select2();
        $list.on('change', function(ev){
            this._apply_filters();
        }.bind(this));

        // Get Virtual Rooms
        $list = this.$el.find('#pms-search #virtual_list');
        $list.html('');
        resultsHotelVirtualRooms.forEach(function(item, index){
            $list.append(`<option value="${item.id}">${item.name}</option>`);
        });
        $list.select2();
        $list.on('change', function(ev){
            this._apply_filters();
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

    on_change_filter_date: function(isStartDate) {
        isStartDate = isStartDate || false;
        var $dateTimePickerBegin = this.$el.find('#pms-search #date_begin');
        var $dateTimePickerEnd = this.$el.find('#pms-search #date_end');

        // FIXME: Hackish onchange ignore (Used when change dates from code)
        if ($dateTimePickerBegin.data("ignore_onchange") || $dateTimePickerEnd.data("ignore_onchange")) {
            $dateTimePickerBegin.data("ignore_onchange", false);
            $dateTimePickerEnd.data("ignore_onchange", false)
            return true;
        }

        var date_begin = $dateTimePickerBegin.data("DateTimePicker").date().set({'hour': 0, 'minute': 0, 'second': 0}).clone().utc();

        if (this._hcalendar && date_begin) {
            if (isStartDate) {
                var ndate_end = date_begin.clone().add(this._view_options['days'], 'd');
                $dateTimePickerEnd.data("ignore_onchange", true);
                $dateTimePickerEnd.data("DateTimePicker").date(ndate_end.local());
            }

            if (!date_begin.isSame(this._last_dates[0].clone().utc(), 'd') || !date_end.isSame(this._last_dates[1].clone().utc(), 'd')) {
                var date_end = $dateTimePickerEnd.data("DateTimePicker").date().set({'hour': 23, 'minute': 59, 'second': 59}).clone().utc();
                this._hcalendar.setStartDate(date_begin, this._hcalendar.getDateDiffDays(date_begin, date_end), false, function(){
                    this.reload_hcalendar_reservations(false);
                }.bind(this));
            }
        }
    },

    reload_hcalendar_reservations: function(clearReservations) {
        var filterDates = this.get_view_filter_dates();
        // Clip dates
        var dfrom = filterDates[0].clone(),
        	dto = filterDates[1].clone();
        if (filterDates[0].isBetween(this._last_dates[0], this._last_dates[1], 'days') && filterDates[1].isAfter(this._last_dates[1], 'day')) {
        	dfrom = this._last_dates[1].clone().local().startOf('day').utc();
        } else if (this._last_dates[0].isBetween(filterDates[0], filterDates[1], 'days') && this._last_dates[1].isAfter(filterDates[0], 'day')) {
        	dto = this._last_dates[0].clone().local().endOf('day').utc();
        } else {
          clearReservations = true;
        }

        return $.when(this.trigger_up('onReloadCalendar', {
            oparams: [
                dfrom.format(HotelConstants.ODOO_DATETIME_MOMENT_FORMAT),
                dto.format(HotelConstants.ODOO_DATETIME_MOMENT_FORMAT),
                false,
            ],
            clearReservations: clearReservations,
        })).then(function(){
            this._last_dates = filterDates;
        });
    },

    _apply_filters: function() {
      var category = _.map(this.$el.find('#pms-search #type_list').val(), function(item){ return +item; });
      var floor = _.map(this.$el.find('#pms-search #floor_list').val(), function(item){ return +item; });
      var amenities = _.map(this.$el.find('#pms-search #amenities_list').val(), function(item){ return +item; });
      var virtual = _.map(this.$el.find('#pms-search #virtual_list').val(), function(item){ return +item; });
      var domain = [];
      if (category && category.length > 0) {
        domain.push(['categ_id', 'in', category]);
      }
      if (floor && floor.length > 0) {
        domain.push(['floor_id', 'in', floor]);
      }
      if (amenities && amenities.length > 0) {
        domain.push(['amenities', 'in', amenities]);
      }
      if (virtual && virtual.length > 0) {
        domain.push(['room_type_id', 'some', virtual]);
      }

      this._hcalendar.setDomain(HotelCalendar.DOMAIN.ROOMS, domain);
    },

    _merge_days_tooltips: function(new_tooltips) {
      for (var nt of new_tooltips) {
        var fnt = _.find(this._days_tooltips, function(item) { return item[0] === nt[0]});
        if (fnt) {
          fnt = nt;
        } else {
          this._days_tooltips.push(nt);
        }
      }
    },

    _find_bootstrap_environment: function() {
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
    }
});

return HotelCalendarView;

});
