// Copyright 2018 Alexandre Díaz <dev@redneboa.es>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
odoo.define('hotel_calendar.PMSCalendarController', function (require) {
"use strict";

var AbstractController = require('web.AbstractController'),
    Core = require('web.core'),
    Bus = require('bus.bus').bus,
    HotelConstants = require('hotel_calendar.Constants'),
    MultiCalendar = require('hotel_calendar.MultiCalendar'),

    _t = Core._t,
    QWeb = Core.qweb;

var PMSCalendarController = AbstractController.extend({
    custom_events: _.extend({}, AbstractController.prototype.custom_events, {
      onLoadCalendar: '_onLoadCalendar',
      onLoadCalendarSettings: '_onLoadCalendarSettings',
      onLoadViewFilters: '_onLoadViewFilters',
      onUpdateButtonsCounter: '_onUpdateButtonsCounter',
      onReloadCalendar: '_onReloadCalendar',
      onUpdateReservations: '_onUpdateReservations',
      onSwapReservations: '_onSwapReservations',
      onSaveChanges: '_onSaveChanges',
      onViewAttached: '_onViewAttached',
    }),

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

      this._multi_calendar.setElement(this.renderer.$el.find('#hcal_widget'));
      this._multi_calendar.start();
      this._assign_multi_calendar_events();
      this._load_calendars();
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------
    savePricelist: function (calendar, pricelist_id, pricelist) {
      var self = this;
      var oparams = [pricelist_id, false, pricelist, {}, {}];
      this.model.save_changes(oparams).then(function(results){
        $(calendar.btnSaveChanges).removeClass('need-save');
        calendar.$el.find('.hcal-input-changed').removeClass('hcal-input-changed');
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
            'class_name': r['class_name']
          });
          rooms.push(nroom);
        }

        // TODO: Not read this... do the change!!
        var reservs = [];
        for (var r of results['reservations']) {
          var nreserv = new HReservation({
            'id': r[1],
            'room_id': r[0],
            'title': r[2],
            'adults': r[3],
            'childrens': r[4],
            'startDate': HotelCalendar.toMomentUTC(r[5], HotelConstants.ODOO_DATETIME_MOMENT_FORMAT),
            'endDate': HotelCalendar.toMomentUTC(r[6], HotelConstants.ODOO_DATETIME_MOMENT_FORMAT),
            'color': r[8],
            'colorText': r[9],
            'splitted': r[10],
            'readOnly': r[12],
            'fixDays': r[13],
            'fixRooms': r[14],
            'unusedZone': false,
            'linkedId': false,
            'overbooking': r[15],
          });
          nreserv.addUserData({'folio_id': r[7]});
          nreserv.addUserData({'parent_reservation': r[11]});
          reservs.push(nreserv);
        }

        var options = {
          startDate: HotelCalendar.toMomentUTC(self.renderer._last_dates[0], HotelConstants.ODOO_DATETIME_MOMENT_FORMAT),
          days: self._view_options['days'] + 1,
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

        for (var calendar of results['calendars']) {
          self._multi_calendar.create_calendar(calendar['name']);
        }
      });
    },

    _assign_multi_calendar_events: function() {
        var self = this;
        this._multi_calendar.on('hcalOnSavePricelist', function(ev){
          self.savePricelist(ev.calendar, ev.detail.pricelist_id, ev.detail.pricelist);
        });
        this._multi_calendar.on('hcalOnMouseEnterReservation', function(ev){
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
        this._multi_calendar.on('hcalOnClickReservation', function(ev){
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
        this._multi_calendar.on('hcalOnSwapReservations', function(ev){
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
        this._multi_calendar.on('hcalOnCancelSwapReservations', function(ev){
          $("#btn_swap span.ntext").html(_t("START SWAP"));
          $("#btn_swap").css({
            'backgroundColor': '',
            'fontWeight': 'normal'
          });
        });
        this._multi_calendar.on('hcalOnChangeReservation', function(ev){
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
        this._multi_calendar.on('hcalOnUpdateSelection', function(ev){
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
        this._multi_calendar.on('hcalOnChangeSelection', function(ev){
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

        this._multi_calendar.on('hcalOnDateChanged', function(ev){
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

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------
    _onUpdateReservations: function (ev) {
      var self = this;
      return this.model.update_records(ev.data.ids, ev.data.values).then(function(result){
        // Remove OB Room Row?
        if (ev.data.oldReservation.room.overbooking) {
          self.renderer._hcalendar.removeOBRoomRow(ev.data.oldReservation);
        }
      }).fail(function(err, errev){
        self.renderer._hcalendar.replaceReservation(ev.data.newReservation, ev.data.oldReservation);
      });
    },

    _onSwapReservations: function (ev) {
      var self = this;
      return this.model.swap_reservations(ev.data.fromIds, ev.data.toIds).then(function(results){
        var allReservs = ev.data.detail.inReservs.concat(ev.data.detail.outReservs);
        for (var nreserv of allReservs) {
          self.renderer.$el.find(nreserv._html).stop(true);
        }
      }).fail(function(err, errev){
        for (var nreserv of ev.data.detail.inReservs) {
          self.renderer.$el.find(nreserv._html).animate({'top': refFromReservDiv.style.top}, 'fast');
        }
        for (var nreserv of ev.detail.outReservs) {
          self.renderer.$el.find(nreserv._html).animate({'top': refToReservDiv.style.top}, 'fast');
        }

        self.renderer.$el._hcalendar.swapReservations(ev.data.detail.outReservs, ev.data.detail.inReservs);
      });
    },

    _onLoadCalendarSettings: function  (ev) {
      var self = this;
      return this.model.get_hcalendar_settings().then(function(options){
        self._view_options = options;
        var date_begin = moment().startOf('day');
        if (['xs', 'md'].indexOf(self._find_bootstrap_environment()) >= 0) {
          self._view_options['days'] = 7;
        } else {
          self._view_options['days'] = (self._view_options['days'] !== 'month')?parseInt(self._view_options['days']):date_begin.daysInMonth();
        }
        self.renderer.load_hcalendar_options(self._view_options);
      });
    },

    _onViewAttached: function (ev) {
      this._multi_calendar.recalculate_reservation_positions();
    },

    _onReloadCalendar: function (ev) {
      this.model.get_calendar_data(ev.data.oparams).then(function(results){
        this.renderer._merge_days_tooltips(results['events']);
        this.renderer._reserv_tooltips = _.extend(this.renderer._reserv_tooltips, results['tooltips']);
        var reservs = [];
        for (var r of results['reservations']) {
          var nreserv = new HReservation({
            'id': r[1],
            'room_id': r[15],
            'title': r[2],
            'adults': r[3],
            'childrens': r[4],
            'startDate': HotelCalendar.toMomentUTC(r[5], HotelConstants.ODOO_DATETIME_MOMENT_FORMAT),
            'endDate': HotelCalendar.toMomentUTC(r[6], HotelConstants.ODOO_DATETIME_MOMENT_FORMAT),
            'color': r[8],
            'colorText': r[9],
            'splitted': r[10],
            'readOnly': r[12] || false,
            'fixDays': r[13] || false,
            'fixRooms': r[14] || false,
            'unusedZone': false,
            'linkedId': false,
            'overbooking': r[15],
          });
          nreserv.addUserData({'folio_id': r[7]});
          nreserv.addUserData({'parent_reservation': r[11]});
          reservs.push(nreserv);
        }

        this.renderer._hcalendar.addPricelist(results['pricelist']);
        this.renderer._hcalendar.addRestrictions(results['restrictions']);
        if (ev.data.clearReservations) {
          this.renderer._hcalendar.setReservations(reservs);
        } else {
          this.renderer._hcalendar.addReservations(reservs);
        }

        this.renderer._assign_extra_info();
      }.bind(this));
    },

    _onUpdateButtonsCounter: function (ev) {
      var self = this;
      var domain_checkouts = [['checkout', '=', moment().format(HotelConstants.ODOO_DATETIME_MOMENT_FORMAT)]];
      var domain_checkins = [['checkin', '=', moment().format(HotelConstants.ODOO_DATETIME_MOMENT_FORMAT)]];
      var domain_overbookings = [['overbooking', '=', true], ['state', 'not in', ['cancelled']]];
      $.when(
        this.model.search_count(domain_checkouts),
        this.model.search_count(domain_checkins),
        this.model.search_count(domain_overbookings),
      ).then(function(a1, a2, a3){
        self.renderer.update_buttons_counter(a1, a2, a3);
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
      if (!this.renderer._hcalendar) {
        return;
      }
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
              if (notif[1]['action'] === 'unlink' || reserv['state'] === 'cancelled') {
                this.renderer._hcalendar.removeReservation(reserv['reserv_id'], true);
                this.renderer._reserv_tooltips = _.pick(this.renderer._reserv_tooltips, function(value, key, obj){ return key != reserv['reserv_id']; });
                nreservs = _.reject(nreservs, function(item){ return item.id == reserv['reserv_id']; });
              } else {
                nreservs = _.reject(nreservs, {'id': reserv['reserv_id']}); // Only like last changes
                var room = this.renderer._hcalendar.getRoom(reserv['room_id'], reserv['overbooking'], reserv['reserv_id']);
                // need create a overbooking row?
                if (!room && reserv['overbooking']) {
                  room = this.renderer._hcalendar.createOBRoom(this.renderer._hcalendar.getRoom(reserv['room_id']), reserv['reserv_id']);
                  this.renderer._hcalendar.createOBRoomRow(room);
                }
                if (!room) {
                  console.warn(`Can't found a room for the reservation '${reserv['reserv_id']}'!`);
                  continue;
                }
                if (room) {
                  var nreserv = new HReservation({
                    'id': reserv['reserv_id'],
                    'room': room,
                    'title': reserv['partner_name'],
                    'adults': reserv['adults'],
                    'childrens': reserv['children'],
                    'startDate': HotelCalendar.toMomentUTC(reserv['checkin'], HotelConstants.ODOO_DATETIME_MOMENT_FORMAT),
                    'endDate': HotelCalendar.toMomentUTC(reserv['checkout'], HotelConstants.ODOO_DATETIME_MOMENT_FORMAT),
                    'color': reserv['reserve_color'],
                    'colorText': reserv['reserve_color_text'],
                    'splitted': reserv['splitted'],
                    'readOnly': reserv['read_only'],
                    'fixDays': reserv['fix_days'],
                    'fixRooms': reserv['fix_rooms'],
                    'unusedZone': false,
                    'linkedId': false,
                    'overbooking': reserv['overbooking'],
                  });
                  nreserv.addUserData({'folio_id': reserv['folio_id']});
                  nreserv.addUserData({'parent_reservation': reserv['parent_reservation']});
                  this.renderer._reserv_tooltips[reserv['reserv_id']] = notif[1]['tooltip'];
                  nreservs.push(nreserv);
                }
              }
              need_update_counters = true;
              break;
            case 'pricelist':
              this.renderer._hcalendar.addPricelist(notif[1]['price']);
              break;
            case 'restriction':
              this.renderer._hcalendar.addRestrictions(notif[1]['restriction']);
              break;
            default:
              // Do Nothing
          }
        }
      }
      if (nreservs.length > 0) {
        this.renderer._hcalendar.addReservations(nreservs);
      }
      if (need_update_counters) {
        this._onUpdateButtonsCounter();
      }
    },

    _assign_hcalendar_events: function() {
      var self = this;
      this._multi_calendar.on('hcalOnSavePricelist', function(ev){
        var oparams = [ev.detail.pricelist_id, false, ev.detail.pricelist, {}, {}];
        self.savePricelist(ev.calendar, ev.detail.pricelist_id, ev.detail.pricelist);
      });
      this._multi_calendar.on('hcalOnMouseEnterReservation', function(ev){
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
      this._multi_calendar.on('hcalOnClickReservation', function(ev){
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
      this._multi_calendar.on('hcalOnSwapReservations', function(ev){
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
      this._multi_calendar.on('hcalOnCancelSwapReservations', function(ev){
        $("#btn_swap span.ntext").html(_t("START SWAP"));
        $("#btn_swap").css({
          'backgroundColor': '',
          'fontWeight': 'normal'
        });
      });
      this._multi_calendar.on('hcalOnChangeReservation', function(ev){
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
      this._multi_calendar.on('hcalOnUpdateSelection', function(ev){
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
      this._multi_calendar.on('hcalOnChangeSelection', function(ev){
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

      this._multi_calendar.on('hcalOnDateChanged', function(ev){
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
