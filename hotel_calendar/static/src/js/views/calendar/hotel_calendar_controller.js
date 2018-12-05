// Copyright 2018 Alexandre Díaz <dev@redneboa.es>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
odoo.define('hotel_calendar.PMSCalendarController', function (require) {
"use strict";

var AbstractController = require('web.AbstractController'),
    Core = require('web.core'),
    Bus = require('bus.bus').bus,
    HotelConstants = require('hotel_calendar.Constants'),

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
        onSaveChanges: '_onSaveChanges'
    }),

    init: function (parent, model, renderer, params) {
        this._super.apply(this, arguments);
        this.displayName = params.displayName;
        this.formViewId = params.formViewId;
        this.context = params.context;

        Bus.on("notification", this, this._onBusNotification);
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------


    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    _updateRecord: function (record) {
        return this.model.updateRecord(record).then(this.reload.bind(this));
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------
    _onSaveChanges: function (ev) {
        var self = this;
        this.model.save_changes(_.toArray(ev.data)).then(function(results){
            $(self.renderer._hcalendar.btnSaveChanges).removeClass('need-save');
            self.renderer.$el.find('.hcal-input-changed').removeClass('hcal-input-changed');
        });
    },

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
            self.renderer.load_hcalendar_options(options);
        });
    },

    _onLoadCalendar: function (ev) {
        var self = this;

        /** DO MAGIC **/
        var hcal_dates = this.renderer.get_view_filter_dates();
        var oparams = [
          hcal_dates[0].format(HotelConstants.ODOO_DATETIME_MOMENT_FORMAT),
          hcal_dates[1].format(HotelConstants.ODOO_DATETIME_MOMENT_FORMAT)
        ];
        this.model.get_calendar_data(oparams).then(function(results){

            self.renderer._days_tooltips = results['events'];
            self.renderer._reserv_tooltips = results['tooltips'];
            var rooms = [];
            for (var r of results['rooms']) {
                var nroom = new HRoom(
                    r['id'],
                    r['name'],
                    r['capacity'],
                    r['class_id'],
                    r['shared'],
                    r['price']
                );
                nroom.addUserData({
                    'room_type_name': r['room_type_name'],
                    'room_type_id': r['room_type_id'],
                    'floor_id': r['floor_id'],
                    'amenities': r['amenity_ids'],
                    'class_id': r['class_id']
                });
                rooms.push(nroom);
            }

            self.renderer.create_calendar('#hcal_widget', rooms, results['pricelist'], results['restrictions']);

            // TODO: Not read this... do the change!!
            var reservs = [];
            for (var r of results['reservations']) {
                var room = self.renderer._hcalendar.getRoom(r[0], r[15], r[1]);
                // need create a overbooking row?
                if (!room && r[15]) {
                  room = self.renderer._hcalendar.createOBRoom(self.renderer._hcalendar.getRoom(r[0]), r[1]);
                  self.renderer._hcalendar.createOBRoomRow(room);
                }
                if (!room) {
                  console.warn(`Can't found a room for the reservation '${r[0]}'!`);
                  continue;
                }

                var nreserv = new HReservation({
                  'id': r[1],
                  'room': room,
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
            self.renderer.load_reservations(reservs);
        });
    },

    _onReloadCalendar: function (ev) {
        this.model.get_calendar_data(ev.data.oparams).then(function(results){
            this.renderer._merge_days_tooltips(results['events']);
            this.renderer._reserv_tooltips = _.extend(this.renderer._reserv_tooltips, results['tooltips']);
            var reservs = [];
            for (var r of results['reservations']) {
              var room = this.renderer._hcalendar.getRoom(r[0], r[15], r[1]);
              // need create a overbooking row?
              if (!room && r[15]) {
                room = this.renderer._hcalendar.createOBRoom(this.renderer._hcalendar.getRoom(r[0]), r[1]);
                this.renderer._hcalendar.createOBRoomRow(room);
              }
              if (!room) {
                console.warn(`Can't found a room for the reservation '${r[0]}'!`);
                continue;
              }
              var nreserv = new HReservation({
                'id': r[1],
                'room': room,
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

});

return PMSCalendarController;

});
