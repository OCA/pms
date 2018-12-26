// Copyright 2018 Alexandre Díaz <dev@redneboa.es>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
odoo.define('hotel_calendar.PMSCalendarController', function (require) {
"use strict";

var AbstractController = require('web.AbstractController'),
    ViewDialogs = require('web.view_dialogs'),
    Dialog = require('web.Dialog'),
    Core = require('web.core'),
    Bus = require('bus.bus').bus,
    HotelConstants = require('hotel_calendar.Constants'),
    MultiCalendar = require('hotel_calendar.MultiCalendar'),

    _t = Core._t,
    QWeb = Core.qweb;

var PMSCalendarController = AbstractController.extend({
    custom_events: _.extend({}, AbstractController.prototype.custom_events, {
      onLoadViewFilters: '_onLoadViewFilters',
      onUpdateButtonsCounter: '_onUpdateButtonsCounter',
      onViewAttached: '_onViewAttached',
      onApplyFilters: '_onApplyFilters',
    }),

    _last_dates: [],

    init: function (parent, model, renderer, params) {
      this._super.apply(this, arguments);
      this.displayName = params.displayName;
      this.formViewId = params.formViewId;
      this.context = params.context;

      this._multi_calendar = new MultiCalendar(this);

      Bus.on("notification", this, this._onBusNotification);
    },

    start: function() {
      this._super.apply(this, arguments);
      var self = this;

      this._multi_calendar.setElement(this.renderer.$el.find('#hcal_widget'));
      this._multi_calendar.reset();
      this._multi_calendar.start();

      this._assign_multi_calendar_events();
      this._load_calendar_settings();
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------
    savePricelist: function (calendar, pricelist_id, pricelist) {
      var self = this;
      var oparams = [pricelist_id, false, pricelist, {}, {}];
      this.model.save_changes(oparams).then(function(results){
        $(calendar.btnSaveChanges).removeClass('need-save');
        $(calendar.edtable).find('.hcal-input-changed').removeClass('hcal-input-changed');
      });
    },

    updateReservations: function (calendar, ids, values, oldReserv, newReserv) {
      var self = this;
      return this.model.update_records(ids, values).then(function(result){
        // Remove OB Room Row?
        if ((oldReserv.room.overbooking && !newReserv.room.overbooking) || (oldReserv.room.cancelled && !newReserv.room.cancelled)) {
           self._multi_calendar.remove_extra_room_row(oldReserv, true);
        }
      }).fail(function(err, errev){
        calendar.replaceReservation(newReserv, oldReserv);
      });
    },

    swapReservations: function (fromIds, toIds, detail, refFromReservDiv, refToReservDiv) {
      var self = this;
      return this.model.swap_reservations(fromIds, toIds).then(function(results){
        var allReservs = detail.inReservs.concat(detail.outReservs);
        for (var nreserv of allReservs) {
          self.renderer.$el.find(nreserv._html).stop(true);
        }
      }).fail(function(err, errev){
        for (var nreserv of detail.inReservs) {
          self.renderer.$el.find(nreserv._html).animate({'top': refFromReservDiv.style.top}, 'fast');
        }
        for (var nreserv of detail.outReservs) {
          self.renderer.$el.find(nreserv._html).animate({'top': refToReservDiv.style.top}, 'fast');
        }

        self._multi_calendar.swap_reservations(detail.outReservs, detail.inReservs);
      });
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    _updateRecord: function (record) {
      return this.model.updateRecord(record).then(this.reload.bind(this));
    },

    _load_calendars: function (ev) {
      var self = this;

      /** DO MAGIC **/
      var hcal_dates = this.renderer.get_view_filter_dates();
      var oparams = [
        hcal_dates[0].format(HotelConstants.ODOO_DATETIME_MOMENT_FORMAT),
        hcal_dates[1].format(HotelConstants.ODOO_DATETIME_MOMENT_FORMAT)
      ];
      this.model.get_calendar_data(oparams).then(function(results){
        self._multi_calendar._days_tooltips = results['events'];
        self._multi_calendar._reserv_tooltips = results['tooltips'];
        var rooms = [];
        for (var r of results['rooms']) {
          var nroom = new HRoom(
            r['id'],
            r['name'],
            r['capacity'],
            r['class_name'],
            r['shared'],
            r['price']
          );
          nroom.addUserData({
            'room_type_name': r['room_type_name'],
            'room_type_id': r['room_type_id'],
            'floor_id': r['floor_id'],
            'amenities': r['amenity_ids'],
            'class_id': r['class_id'],
          });
          rooms.push(nroom);
        }

        var reservs = [];
        for (var r of results['reservations']) {
          var nreserv = self._create_reservation_obj(r);
          reservs.push(nreserv);
        }

        var options = {
          startDate: HotelCalendar.toMomentUTC(self._last_dates[0], HotelConstants.ODOO_DATETIME_MOMENT_FORMAT),
          days: self._view_options['days'],
          rooms: rooms,
          endOfWeek: parseInt(self._view_options['eday_week']) || 6,
          divideRoomsByCapacity: self._view_options['divide_rooms_by_capacity'] || false,
          allowInvalidActions: self._view_options['allow_invalid_actions'] || false,
          assistedMovement: self._view_options['assisted_movement'] || false,
          showPricelist: self._view_options['show_pricelist'] || false,
          showAvailability: self._view_options['show_availability'] || false,
          showNumRooms: self._view_options['show_num_rooms'] || 0,
          endOfWeekOffset: self._view_options['eday_week_offset'] || 0
        };

        self._multi_calendar.set_options(options);
        self._multi_calendar.set_datasets(results['pricelist'], results['restrictions'], reservs);
        self._multi_calendar.set_base_element(self.renderer.$el[0]);

        for (var calendar_record of results['calendars']) {
          var calendar_index = self._multi_calendar.create_calendar(calendar_record);
          var domain = self._generate_calendar_filters_domain(calendar_record);
          var calendar = self._multi_calendar.get_calendar(calendar_index+1);
          calendar.setDomain(HotelCalendar.DOMAIN.ROOMS, domain);
        }

        self._multi_calendar.set_active_calendar(self._multi_calendar._calendars.length-1);
      });
    },

    _generate_calendar_filters_domain: function(calendar) {
      var domain = [];
      if (calendar['segmentation_ids'] && calendar['segmentation_ids'].length > 0) {
        domain.push(['class_id', 'in', calendar['segmentation_ids']]);
      }
      if (calendar['location_ids'] && calendar['location_ids'].length > 0) {
        domain.push(['floor_id', 'in', calendar['location_ids']]);
      }
      if (calendar['amenity_ids'] && calendar['amenity_ids'].length > 0) {
        domain.push(['amenities', 'in', calendar['amenity_ids']]);
      }
      if (calendar['room_type_ids'] && calendar['room_type_ids'].length > 0) {
        domain.push(['room_type_id', 'some', calendar['room_type_ids']]);
      }
      return domain;
    },

    _load_calendar_settings: function (ev) {
      var self = this;
      return this.model.get_hcalendar_settings().then(function(options){
        self._view_options = options;

        if (['xs', 'md'].indexOf(self._find_bootstrap_environment()) >= 0) {
          self._view_options['days'] = 7;
        }

        var date_begin = moment().startOf('day');
        var days = self._view_options['days'];
        if (self._view_options['days'] === 'month') {
            days = date_begin.daysInMonth();
        }
        self._last_dates[0] = date_begin.clone();
        self._last_dates[1] = date_begin.clone().add(days, 'd');

        var $dateTimePickerBegin = self.renderer.$el.find('#pms-menu #date_begin');
        var $dateEndDays = self.renderer.$el.find('#pms-menu #date_end_days');
        $dateTimePickerBegin.data("ignore_onchange", true);
        $dateTimePickerBegin.data("DateTimePicker").date(date_begin);
        $dateEndDays.val(self._view_options['days']);

        //self.renderer.init_calendar_view();
        self._load_calendars();
        self._assign_view_events();
      });
    },

    _reload_active_calendar: function() {
      var self = this;
      var filterDates = this.renderer.get_view_filter_dates();
      var active_calendar = this._multi_calendar.get_active_calendar();
      // Clip dates
      var dfrom = filterDates[0].clone(),
        dto = filterDates[1].clone();

      if (filterDates[0].isBetween(this._last_dates[0], this._last_dates[1], 'days') && filterDates[1].isAfter(this._last_dates[1], 'day')) {
        dfrom = this._last_dates[1].clone().local().startOf('day').utc();
      } else if (this._last_dates[0].isBetween(filterDates[0], filterDates[1], 'days') && this._last_dates[1].isAfter(filterDates[0], 'day')) {
        dto = this._last_dates[0].clone().local().endOf('day').utc();
      }

      var oparams = [
        dfrom.format(HotelConstants.ODOO_DATETIME_MOMENT_FORMAT),
        dto.format(HotelConstants.ODOO_DATETIME_MOMENT_FORMAT),
        false
      ];
      this.model.get_calendar_data(oparams).then(function(results){
        var reservs = [];
        for (var r of results['reservations']) {
          var nreserv = self._create_reservation_obj(r);
          reservs.push(nreserv);
        }

        self._multi_calendar._reserv_tooltips = _.extend(this._multi_calendar._reserv_tooltips, results['tooltips']);
        self._multi_calendar.merge_days_tooltips(results['events']);
        self._multi_calendar.merge_pricelist(results['pricelist'], active_calendar);
        self._multi_calendar.merge_restrictions(results['restrictions'], active_calendar);
        self._multi_calendar.merge_reservations(reservs, active_calendar);

        self._multi_calendar._assign_extra_info(active_calendar);
      }.bind(this)).then(function(){
        self._last_dates = filterDates;
      });
    },

    _assign_view_events: function() {
      var self = this;
      var $dateTimePickerBegin = this.renderer.$el.find('#pms-menu #date_begin');
      var $dateEndDays = this.renderer.$el.find('#pms-menu #date_end_days');
      $dateTimePickerBegin.on("dp.change", function (e) {
        $dateTimePickerBegin.data("DateTimePicker").hide();
        self._on_change_filter_date(true);
      });
      $dateEndDays.on("change", function (e) {
        self._on_change_filter_date(false);
      });

      this.renderer.$el.find("#btn_swap button").on('click', function(ev){
        var active_calendar = self._multi_calendar.get_active_calendar();
        var hcalSwapMode = active_calendar.getSwapMode();
        var $led = $(this).find('.led');
        if (hcalSwapMode === HotelCalendar.MODE.NONE) {
          active_calendar.setSwapMode(HotelCalendar.MODE.SWAP_FROM);
          $("#btn_swap span.ntext").html(_t("Continue"));
          $led.removeClass('led-disabled');
          $led.addClass('led-green');
        } else if (active_calendar.getReservationAction().inReservations.length > 0 && hcalSwapMode === HotelCalendar.MODE.SWAP_FROM) {
          active_calendar.setSwapMode(HotelCalendar.MODE.SWAP_TO);
          $("#btn_swap span.ntext").html(_t("End"));
          $led.removeClass('led-green');
          $led.addClass('led-blue');
        } else {
          active_calendar.setSwapMode(HotelCalendar.MODE.NONE);
          $("#btn_swap span.ntext").html(_t("Start Swap"));
          $led.removeClass('led-blue');
          $led.addClass('led-disabled');
        }
      });

      this.renderer.$el.find('#pms-menu #btn_action_overbooking button').on('click', function(ev){
        var active_calendar = self._multi_calendar.get_active_calendar();
        active_calendar.toggleOverbookingsVisibility();
        active_calendar.addReservations(self._multi_calendar._dataset['reservations']);
        if (active_calendar.options.showOverbookings) {
          $(this).find('.led').removeClass('led-disabled');
          $(this).find('.led').addClass('led-enabled');
        } else {
          $(this).find('.led').addClass('led-disabled');
          $(this).find('.led').removeClass('led-enabled');
        }
      });

      this.renderer.$el.find('#pms-menu #btn_action_cancelled button').on('click', function(ev){
          var active_calendar = self._multi_calendar.get_active_calendar();
          active_calendar.toggleCancelledVisibility();
          active_calendar.addReservations(self._multi_calendar._dataset['reservations']);
          if (active_calendar.options.showCancelled) {
            $(this).find('.led').removeClass('led-disabled');
            $(this).find('.led').addClass('led-enabled');
          } else {
            $(this).find('.led').addClass('led-disabled');
            $(this).find('.led').removeClass('led-enabled');
          }
      });

      this.renderer.$el.find('#pms-menu #btn_action_divide button').on('click', function(ev){
        var active_calendar = self._multi_calendar.get_active_calendar();
        var cur_mode = active_calendar.getSelectionMode();
        active_calendar.setSelectionMode(cur_mode===HotelCalendar.ACTION.DIVIDE?HotelCalendar.MODE.NONE:HotelCalendar.ACTION.DIVIDE);
      });

      this.renderer.$el.find('#pms-menu #btn_action_unify button').on('click', function(ev){
        var active_calendar = self._multi_calendar.get_active_calendar();
        var cur_mode = active_calendar.getSelectionMode();
        active_calendar.setSelectionMode(cur_mode===HotelCalendar.ACTION.UNIFY?HotelCalendar.MODE.NONE:HotelCalendar.ACTION.UNIFY);
      });

      this.renderer.$el.find('#pms-menu #btn_save_calendar_record').on('click', function(ev){
        var active_calendar_record = self._multi_calendar.get_calendar_record(self._multi_calendar.get_active_index());

        var name = self.renderer.$el.find('#pms-menu #calendar_name').val();
        var category = _.map(self.renderer.$el.find('#pms-menu #type_list').val(), function(item){ return +item; });
        var floor = _.map(self.renderer.$el.find('#pms-menu #floor_list').val(), function(item){ return +item; });
        var amenities = _.map(self.renderer.$el.find('#pms-menu #amenities_list').val(), function(item){ return +item; });
        var types = _.map(self.renderer.$el.find('#pms-menu #virtual_list').val(), function(item){ return +item; });
        var oparams = {
          'name': name,
          'segmentation_ids': [[6, false, category]],
          'location_ids': [[6, false, floor]],
          'amenity_ids': [[6, false, amenities]],
          'room_type_ids': [[6, false, types]],
        }

        self._multi_calendar.update_active_tab_name(name);
        self.model.update_or_create_calendar_record(active_calendar_record['id'], oparams).then(function(){
          active_calendar_record.name = name;
          active_calendar_record.segmentation_ids = category;
          active_calendar_record.location_ids = floor;
          active_calendar_record.amenity_ids = amenities;
          active_calendar_record.room_type_ids = types;
        }).fail(function(){
          self._multi_calendar.update_active_tab_name(active_calendar_record.name);
        });
      });

      this.renderer.$el.find('#pms-menu #btn_reload_calendar_filters').on('click', function(ev){
          var active_calendar_record = self._multi_calendar.get_calendar_record(self._multi_calendar.get_active_index());
          self._multi_calendar.update_active_tab_name(active_calendar_record.name);
          var $calendar_name = this.renderer.$el.find('#pms-menu .menu-filter-box #calendar_name');
          $calendar_name.val(active_calendar_record.name);
          self._refresh_filters({
              'class_id': active_calendar_record['segmentation_ids'],
              'floor_id': active_calendar_record['location_ids'],
              'amenities': active_calendar_record['amenity_ids'],
              'room_type_id': active_calendar_record['room_type_ids'],
          });
      });

      this._multi_calendar.on('tab_changed', function(ev, active_index){
        if (active_index) {
          self._refresh_view_options(active_index);
        }
      });
    },

    _assign_multi_calendar_events: function() {
        var self = this;
        this._multi_calendar.on_calendar('hcalOnSavePricelist', function(ev){
          self.savePricelist(ev.detail.calendar_obj, ev.detail.pricelist_id, ev.detail.pricelist);
        });
        $('.hcal-reservation noselect').popover();
        this._multi_calendar.on_calendar('hcalOnClickReservation', function(ev){
          if (ev.detail.reservationObj) {
            var tp = self._multi_calendar._reserv_tooltips[ev.detail.reservationObj.id];
            var qdict = self._generate_reservation_tooltip_dict(tp);
            $(".marked-as-having-a-popover").popover('destroy');
            $(ev.detail.reservationDiv).addClass('marked-as-having-a-popover');
            $(ev.detail.reservationDiv).popover({
              trigger: 'manual',
              container: 'body',
              animation: false,
              html: true,
              placement: 'bottom',
              /* title: "Come'n popovers!", */
              content: QWeb.render('HotelCalendar.TooltipReservation', qdict)
            }).popover('show');
          }
        });
        this._multi_calendar.on_calendar('hcalOnSplitReservation', function(ev){
          var qdict = {};
          var dialog = new Dialog(self, {
            title: _t("Confirm Split Reservation"),
            buttons: [
                {
                  text: _t("Yes, split it"),
                  classes: 'btn-primary',
                  close: true,
                  click: function () {
                    self.model.split_reservation(ev.detail.obj_id, ev.detail.nights);
                  }
                },
                {
                  text: _t("No"),
                  close: true
                }
            ],
            $content: QWeb.render('HotelCalendar.ConfirmSplitOperation', qdict)
          }).open();
        });
        this._multi_calendar.on_calendar('hcalOnDblClickReservation', function(ev){
          //var res_id = ev.detail.reservationObj.getUserData('folio_id');
          $(ev.detail.reservationDiv).tooltip('destroy');
          self.do_action({
            type: 'ir.actions.act_window',
            res_model: 'hotel.reservation',
            res_id: ev.detail.reservationObj.id,
            views: [[false, 'form']]
          });
        });
        this._multi_calendar.on_calendar('hcalOnUnifyReservations', function(ev){
          var qdict = {};
          var dialog = new Dialog(self, {
            title: _t("Confirm Unify Reservations"),
            buttons: [
                {
                  text: _t("Yes, unify it"),
                  classes: 'btn-primary',
                  close: true,
                  click: function () {
                    self.model.unify_reservations(_.map(ev.detail.toUnify, 'id'));
                  }
                },
                {
                  text: _t("No"),
                  close: true
                }
            ],
            $content: QWeb.render('HotelCalendar.ConfirmUnifyOperation', qdict)
          }).open();
        });
        this._multi_calendar.on_calendar('hcalOnSwapReservations', function(ev){
          var qdict = {};
          var dialog = new Dialog(self, {
            title: _t("Confirm Reservation Swap"),
            buttons: [
                {
                  text: _t("Yes, swap it"),
                  classes: 'btn-primary',
                  close: true,
                  click: function () {
                    if (ev.detail.calendar_obj.swapReservations(ev.detail.inReservs, ev.detail.outReservs)) {
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
                      self.swapReservations(fromIds, toIds, ev.detail, refFromReservDiv, refToReservDiv);
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
        this._multi_calendar.on_calendar('hcalOnCancelSwapReservations', function(ev){
          $("#btn_swap span.ntext").html(_t("Start Swap"));
          var $led = $("#btn_swap").find('.led');
          $led.removeClass('led-blue').removeClass('led-green').addClass('led-disabled');
        });
        this._multi_calendar.on_calendar('hcalOnChangeReservation', function(ev){
          var newReservation = ev.detail.newReserv;
          var oldReservation = ev.detail.oldReserv;
          var oldPrice = ev.detail.oldPrice;
          var newPrice = ev.detail.newPrice;
          var folio_id = newReservation.getUserData('folio_id');

          var linkedReservs = _.find(ev.detail.calendar_obj._reservations, function(item){
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
                  if (newReservation.room.overbooking || newReservation.room.cancelled) {
                    roomId = +newReservation.room.id.substr(newReservation.room.id.indexOf('@')+1);
                  }
                  var write_values = {
                    'checkin': newReservation.startDate.format(HotelConstants.ODOO_DATETIME_MOMENT_FORMAT),
                    'checkout': newReservation.endDate.format(HotelConstants.ODOO_DATETIME_MOMENT_FORMAT),
                    'room_id': roomId,
                    'overbooking': newReservation.room.overbooking
                  };
                  if (newReservation.room.cancelled) {
                      write_values['state'] = 'cancelled';
                  } else if (!newReservation.room.cancelled && oldReservation.cancelled) {
                      write_values['state'] = 'draft';
                  }
                  self.updateReservations(ev.detail.calendar_obj, [newReservation.id],
                                          write_values, oldReservation, newReservation);
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
          dialog.on('closed', this, function(e){
            if (!hasChanged) {
              ev.detail.calendar_obj.replaceReservation(newReservation, oldReservation);
            }
          });
        });
        this._multi_calendar.on_calendar('hcalOnUpdateSelection', function(ev){
          for (var td of ev.detail.old_cells) {
            $(td).tooltip('destroy');
          }
          if (ev.detail.cells.length) {
            var last_cell = ev.detail.cells[ev.detail.cells.length-1];
            var date_cell_start = HotelCalendar.toMoment(ev.detail.calendar_obj.etable.querySelector(`#${ev.detail.cells[0].dataset.hcalParentCell}`).dataset.hcalDate);
            var date_cell_end = HotelCalendar.toMoment(ev.detail.calendar_obj.etable.querySelector(`#${last_cell.dataset.hcalParentCell}`).dataset.hcalDate).add(1, 'd');
            var parentRow = document.querySelector(`#${ev.detail.cells[0].dataset.hcalParentRow}`);
            var room = ev.detail.calendar_obj.getRoom(parentRow.dataset.hcalRoomObjId);
            if (room.overbooking || room.cancelled) {
              return;
            }
            var nights = date_cell_end.diff(date_cell_start, 'days');
            var qdict = {
              'total_price': Number(ev.detail.totalPrice).toLocaleString(),
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
        this._multi_calendar.on_calendar('hcalOnChangeSelectionMode', function(ev){
            var $ledDivide = this.renderer.$el.find('#pms-menu #btn_action_divide button .led');
            var $ledUnify = this.renderer.$el.find('#pms-menu #btn_action_unify button .led');
            if (ev.detail.newMode === HotelCalendar.ACTION.DIVIDE) {
                $ledDivide.removeClass('led-disabled').addClass('led-enabled');
            } else {
                $ledDivide.removeClass('led-enabled').addClass('led-disabled');
            }
            if (ev.detail.newMode === HotelCalendar.ACTION.UNIFY) {
                $ledUnify.removeClass('led-disabled').addClass('led-enabled');
            } else {
                $ledUnify.removeClass('led-enabled').addClass('led-disabled');
            }
        }.bind(this));
        this._multi_calendar.on_calendar('hcalOnChangeSelection', function(ev){
          var parentRow = document.querySelector(`#${ev.detail.cellStart.dataset.hcalParentRow}`);
          var parentCellStart = document.querySelector(`#${ev.detail.cellStart.dataset.hcalParentCell}`);
          var parentCellEnd = document.querySelector(`#${ev.detail.cellEnd.dataset.hcalParentCell}`);
          var startDate = HotelCalendar.toMoment(parentCellStart.dataset.hcalDate);
          var endDate = HotelCalendar.toMoment(parentCellEnd.dataset.hcalDate).add(1, 'd');
          var room = ev.detail.calendar_obj.getRoom(parentRow.dataset.hcalRoomObjId);
          if (room.overbooking || room.cancelled) {
            return;
          }
          var numBeds = (room.shared || ev.detail.calendar_obj.getOptions('divideRoomsByCapacity'))?(ev.detail.cellEnd.dataset.hcalBedNum - ev.detail.cellStart.dataset.hcalBedNum)+1:room.capacity;
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

        this._multi_calendar.on_calendar('hcalOnDateChanged', function(ev){
          var $dateTimePickerBegin = this.renderer.$el.find('#pms-menu #date_begin');
          $dateTimePickerBegin.data("ignore_onchange", true);
          $dateTimePickerBegin.data("DateTimePicker").date(ev.detail.date_begin.local());
          this._reload_active_calendar();
        }.bind(this));
    },

    _create_reservation_obj: function(json_reserv) {
      var nreserv = new HReservation({
        'id': json_reserv['id'],
        'room_id': json_reserv['room_id'],
        'title': json_reserv['name'],
        'adults': json_reserv['adults'],
        'childrens': json_reserv['childrens'],
        'startDate': HotelCalendar.toMoment(json_reserv['checkin'], HotelConstants.ODOO_DATETIME_MOMENT_FORMAT),
        'endDate': HotelCalendar.toMoment(json_reserv['checkout'], HotelConstants.ODOO_DATETIME_MOMENT_FORMAT),
        'color': json_reserv['bgcolor'],
        'colorText': json_reserv['color'],
        'splitted': json_reserv['splitted'] || false,
        'readOnly': json_reserv['read_only'] || false,
        'fixDays': json_reserv['fix_days'] || false,
        'fixRooms': json_reserv['fix_room'],
        'unusedZone': false,
        'linkedId': false,
        'overbooking': json_reserv['overbooking'],
        'cancelled': json_reserv['state'] === 'cancelled'
      });
      nreserv.addUserData({
        'folio_id': json_reserv['folio_id'],
        'parent_reservation': json_reserv['parent_reservation'],
        'realDates': [
            HotelCalendar.toMoment(json_reserv['real_dates'][0], HotelConstants.ODOO_DATETIME_MOMENT_FORMAT),
            HotelCalendar.toMoment(json_reserv['real_dates'][1], HotelConstants.ODOO_DATETIME_MOMENT_FORMAT)
        ]
      });

      return nreserv;
    },

    _generate_reservation_tooltip_dict: function(tp) {
      return {
        'folio_name': tp['folio_name'],
        'name': tp['name'],
        'phone': tp['phone'],
        'email': tp['email'],
        'room_type_name': tp['room_type_name'],
        'adults': tp['adults'],
        'children': tp['children'],
        'checkin': HotelCalendar.toMomentUTC(tp['checkin'], '').format("DD MMMM"),
        'checkin_day_of_week': HotelCalendar.toMomentUTC(tp['checkin'], '').format("dddd"),
        'checkout': HotelCalendar.toMomentUTC(tp['checkout'], '').format("DD MMMM"),
        'checkout_day_of_week': HotelCalendar.toMomentUTC(tp['checkout'], '').format("dddd"),
        'arrival_hour': tp['arrival_hour'],
        'departure_hour': tp['departure_hour'],
        'num_split': tp['num_split'],
        'amount_total': Number(tp['amount_total']).toLocaleString(),
        'pending_amount': Number(tp['pending_amount']).toLocaleString(),
        'amount_paid': Number(tp['amount_paid']).toLocaleString(),
        'reservation_type': tp['type'],
        'out_service_description': tp['out_service_description']
      };
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------
    _onViewAttached: function (ev) {
      this._multi_calendar.recalculate_reservation_positions();
    },

    _onUpdateButtonsCounter: function (ev) {
      var self = this;
      var domain_checkouts = [['checkout', '=', moment().format(HotelConstants.ODOO_DATETIME_MOMENT_FORMAT)]];
      var domain_checkins = [['checkin', '=', moment().format(HotelConstants.ODOO_DATETIME_MOMENT_FORMAT)]];
      var domain_overbookings = [['overbooking', '=', true], ['state', 'not in', ['cancelled']]];
      var domain_cancelled = [['state', '=', 'cancelled']];
      $.when(
        this.model.search_count(domain_checkouts),
        this.model.search_count(domain_checkins),
        this.model.search_count(domain_overbookings),
        this.model.search_count(domain_cancelled),
      ).then(function(a1, a2, a3, a4){
        self.renderer.update_buttons_counter(a1, a2, a3, a4);
      });
    },

    _onLoadViewFilters: function (ev) {
      var self = this;
      $.when(
        this.model.get_room_type_class(),
        this.model.get_floors(),
        this.model.get_amenities(),
        this.model.get_room_types()
      ).then(function(a1, a2, a3, a4){
        self.renderer.loadViewFilters(a1, a2, a3, a4);
      });
    },

    _onBusNotification: function(notifications) {
      var need_reload_pricelists = false;
      var need_update_counters = false;
      var nreservs = []
      for (var notif of notifications) {
        if (notif[0][1] === 'hotel.reservation') {
          switch (notif[1]['type']) {
            case 'reservation':
              var reserv = notif[1]['reservation'];
              // Only show notifications of other users
              // if (notif[1]['subtype'] !== 'noshow' && this._view_options['show_notifications'] && notif[1]['userid'] != this.dataset.context.uid) {
              //   var qdict = _.clone(reserv);
              //   qdict = _.extend(qdict, {
              //     'checkin': HotelCalendar.toMomentUTC(qdict['checkin'], HotelConstants.ODOO_DATETIME_MOMENT_FORMAT).clone().local().format(HotelConstants.L10N_DATETIME_MOMENT_FORMAT), // UTC -> Local
              //     'checkout': HotelCalendar.toMomentUTC(qdict['checkout'], HotelConstants.ODOO_DATETIME_MOMENT_FORMAT).clone().local().format(HotelConstants.L10N_DATETIME_MOMENT_FORMAT), // UTC -> Local
              //     'username': notif[1]['username'],
              //     'userid': notif[1]['userid']
              //   });
              //   var msg = QWeb.render('HotelCalendar.Notification', qdict);
              //   if (notif[1]['subtype'] === "notify") {
              //       this.do_notify(notif[1]['title'], msg, true);
              //   } else if (notif[1]['subtype'] === "warn") {
              //       this.do_warn(notif[1]['title'], msg, true);
              //   }
              // }

              // Create/Update/Delete reservation
              if (notif[1]['action'] === 'unlink') {
                this._multi_calendar.remove_reservation(reserv['id']);
                this._multi_calendar._reserv_tooltips = _.pick(this._multi_calendar._reserv_tooltips, function(value, key, obj){ return key != reserv['id']; });
                nreservs = _.reject(nreservs, function(item){ return item.id == reserv['id']; });
              } else {
                nreservs = _.reject(nreservs, {'id': reserv['id']}); // Only like last changes
                var nreserv = this._create_reservation_obj(reserv);
                this._multi_calendar._reserv_tooltips[reserv['id']] = notif[1]['tooltip'];
                nreservs.push(nreserv);
              }
              need_update_counters = true;
              break;
            case 'pricelist':
              this._multi_calendar.merge_pricelist(notif[1]['price']);
              break;
            case 'restriction':
              this._multi_calendar.merge_restrictions(notif[1]['restriction']);
              break;
            default:
              // Do Nothing
          }
        }
      }
      if (nreservs.length > 0) {
        this._multi_calendar.merge_reservations(nreservs);
      }
      if (need_update_counters) {
        this._onUpdateButtonsCounter();
      }
    },

    _onApplyFilters: function() {
      var category = _.map(this.renderer.$el.find('#pms-menu #type_list').val(), function(item){ return +item; });
      var floor = _.map(this.renderer.$el.find('#pms-menu #floor_list').val(), function(item){ return +item; });
      var amenities = _.map(this.renderer.$el.find('#pms-menu #amenities_list').val(), function(item){ return +item; });
      var virtual = _.map(this.renderer.$el.find('#pms-menu #virtual_list').val(), function(item){ return +item; });
      var domain = [];
      if (category && category.length > 0) {
        domain.push(['class_id', 'in', category]);
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
      this._multi_calendar.get_active_calendar().setDomain(HotelCalendar.DOMAIN.ROOMS, domain);
    },

    _on_change_filter_date: function(isStartDate) {
        isStartDate = isStartDate || false;
        var $dateTimePickerBegin = this.renderer.$el.find('#pms-menu #date_begin');
        var $dateEndDays = this.renderer.$el.find('#pms-menu #date_end_days');

        // FIXME: Hackish onchange ignore (Used when change dates from code)
        if ($dateTimePickerBegin.data("ignore_onchange") || $dateEndDays.data("ignore_onchange")) {
            $dateTimePickerBegin.data("ignore_onchange", false);
            $dateEndDays.data("ignore_onchange", false)
            return true;
        }

        var date_begin = $dateTimePickerBegin.data("DateTimePicker").date().set({'hour': 0, 'minute': 0, 'second': 0}).clone().utc();

        var active_calendar = this._multi_calendar.get_active_calendar();
        if (active_calendar && date_begin) {
            var days = $dateEndDays.val();
            if (days === 'month') {
                days = date_begin.daysInMonth();
            }
            var date_end = date_begin.clone().add(days, 'd');
            if (!date_begin.isSame(this._last_dates[0].clone().utc(), 'd') || !date_end.isSame(this._last_dates[1].clone().utc(), 'd')) {
                active_calendar.setStartDate(date_begin, $dateEndDays.val(), false, function(){
                    this._reload_active_calendar();
                }.bind(this));
            }
        }
    },

    _refresh_view_options: function(active_index) {
      var active_calendar = this._multi_calendar.get_calendar(active_index);

      /* Dates */
      var $dateTimePickerBegin = this.renderer.$el.find('#pms-menu #date_begin');
      var $dateEndDays = this.renderer.$el.find('#pms-menu #date_end_days');

      var start_date = active_calendar.getOptions('startDate');
      start_date = start_date.clone().add(1, 'd');

      $dateTimePickerBegin.data("ignore_onchange", true);
      $dateTimePickerBegin.data("DateTimePicker").date(start_date.local());
      $dateEndDays.data("ignore_onchange", true);
      $dateEndDays.val(active_calendar.getOptions('orig_days'));
      $dateEndDays.trigger('change');

      /* Overbooking Led */
      var $led = this.renderer.$el.find('#pms-menu #btn_action_overbooking button .led');
      if (active_calendar.options.showOverbookings) {
        $led.removeClass('led-disabled').addClass('led-enabled');
      } else {
        $led.removeClass('led-enabled').addClass('led-disabled');
      }

      /* Cancelled Led */
      $led = this.renderer.$el.find('#pms-menu #btn_action_cancelled button .led');
      if (active_calendar.options.showCancelled) {
        $led.removeClass('led-disabled').addClass('led-enabled');
      } else {
        $led.removeClass('led-enabled').addClass('led-disabled');
      }

      /* Divide Led */
      $led = this.renderer.$el.find('#pms-menu #btn_action_divide button .led');
      if (active_calendar.getSelectionMode() === HotelCalendar.ACTION.DIVIDE) {
          $led.removeClass('led-disabled').addClass('led-enabled');
      } else {
          $led.removeClass('led-enabled').addClass('led-disabled');
      }

      /* Unify Led */
      $led = this.renderer.$el.find('#pms-menu #btn_action_unify button .led');
      if (active_calendar.getSelectionMode() === HotelCalendar.ACTION.UNIFY) {
          $led.removeClass('led-disabled').addClass('led-enabled');
      } else {
          $led.removeClass('led-enabled').addClass('led-disabled');
      }

      /* Calendar Record */
      var active_calendar_record = this._multi_calendar.get_calendar_record(active_index);
      var $calendar_name = this.renderer.$el.find('#pms-menu .menu-filter-box #calendar_name');
      $calendar_name.val(active_calendar_record['name']);

      /* Calendar Filters */
      this._refresh_filters(this._multi_calendar.get_active_filters());
    },

    _refresh_filters: function(calendar_filters) {
        var $segmentation = this.renderer.$el.find('#pms-menu #type_list');
        var $location = this.renderer.$el.find('#pms-menu #floor_list');
        var $amenities = this.renderer.$el.find('#pms-menu #amenities_list');
        var $types = this.renderer.$el.find('#pms-menu #virtual_list');
        $segmentation.val(calendar_filters['class_id']);
        $segmentation.trigger('change');
        $location.val(calendar_filters['floor_id']);
        $location.trigger('change');
        $amenities.val(calendar_filters['amenities']);
        $amenities.trigger('change');
        $types.val(calendar_filters['room_type_id']);
        $types.trigger('change');
    },

    //--------------------------------------------------------------------------
    // Helpers
    //--------------------------------------------------------------------------
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
    },
});

return PMSCalendarController;

});
