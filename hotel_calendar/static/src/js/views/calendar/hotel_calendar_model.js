// Copyright 2018 Alexandre Díaz <dev@redneboa.es>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
odoo.define('hotel_calendar.PMSCalendarModel', function (require) {
"use strict";

var AbstractModel = require('web.AbstractModel'),
    Context = require('web.Context'),
    Core = require('web.core'),
    FieldUtils = require('web.field_utils'),
    Session = require('web.session');


return AbstractModel.extend({
    init: function () {
        this._super.apply(this, arguments);
    },

    load: function (params) {
        this.modelName = params.modelName;
        this.modelManagementName = 'hotel.calendar.management'
    },

    swap_reservations: function(fromIds, toIds) {
        return this._rpc({
            model: this.modelName,
            method: 'swap_reservations',
            args: [fromIds, toIds],
            context: Session.user_context,
        });
    },

    get_calendar_data: function(oparams) {
        var dialog = bootbox.dialog({
            message: '<div class="text-center"><i class="fa fa-spin fa-spinner"></i> Getting Calendar Data From Server...</div>',
            onEscape: false,
            closeButton: false,
            size: 'small',
            backdrop: false,
        });
        return this._rpc({
            model: this.modelName,
            method: 'get_hcalendar_all_data',
            args: oparams,
            context: Session.user_context,
        }, {
            xhr: function () {
                var xhr = new window.XMLHttpRequest();
                //Download progress
                xhr.addEventListener("readystatechange", function() {
                    if (this.readyState == this.DONE) {
                        console.log(`[HotelCalendar] Downloaded ${(parseInt(xhr.getResponseHeader("Content-Length"), 10)/1024).toFixed(3)}KiB of data`);
                    }
                }, false);
                return xhr;
            },
            success: function() {
                dialog.modal('hide');
            },
            shadow: true,
        });
    },

    get_hcalendar_settings: function() {
        return this._rpc({
            model: this.modelName,
            method: 'get_hcalendar_settings',
            args: [false],
        });
    },

    get_room_types: function() {
        return this._rpc({
            model: 'hotel.room.type',
            method: 'search_read',
            args: [false, ['id','name']],
            context: Session.user_context,
        });
    },
    get_floors: function() {
        return this._rpc({
            model: 'hotel.floor',
            method: 'search_read',
            args: [false, ['id','name']],
            context: Session.user_context,
        });
    },
    get_amenities: function() {
        return this._rpc({
            model: 'hotel.amenity',
            method: 'search_read',
            args: [false, ['id','name']],
            context: Session.user_context,
        });
    },
    get_room_type_class: function() {
        return this._rpc({
            model: 'hotel.room.type.class',
            method: 'search_read',
            args: [false, ['id','name']],
            context: Session.user_context,
        });
    },

    search_count: function(domain) {
        return this._rpc({
            model: this.modelName,
            method: 'search_count',
            args: [domain],
            context: Session.user_context,
        });
    },

    update_records: function(ids, vals) {
        return this._rpc({
            model: this.modelName,
            method: 'write',
            args: [ids, vals],
            context: Session.user_context,
        });
    },

    update_or_create_calendar_record: function(ids, vals) {
        if (!ids) {
            return this._rpc({
                model: 'hotel.calendar',
                method: 'create',
                args: [vals],
                context: Session.user_context,
            });
        }
        return this._rpc({
            model: 'hotel.calendar',
            method: 'write',
            args: [ids, vals],
            context: Session.user_context,
        });
    },

    folio_search_count: function(domain) {
        return this._rpc({
            model: 'hotel.folio',
            method: 'search_count',
            args: [domain],
            context: Session.user_context,
        });
    },

    split_reservation: function(id, nights) {
        return this._rpc({
            model: this.modelName,
            method: 'split',
            args: [[id], nights],
            context: Session.user_context,
        })
    },

    unify_reservations: function(reserv_ids) {
        return this._rpc({
            model: this.modelName,
            method: 'unify_ids',
            args: [reserv_ids],
            context: Session.user_context,
        })
    },

    save_changes: function(params) {
      params.splice(0, 0, false); // FIXME: ID=False because first parameter its an integer
      return this._rpc({
          model: 'hotel.calendar.management',
          method: 'save_changes',
          args: params,
          //context: Session.user_context,
      })
    }
});

});
