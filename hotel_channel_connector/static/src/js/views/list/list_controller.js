odoo.define('hotel_channel_connector.ListController', function(require) {
'use strict';
/*
 * Hotel Channel Connector
 * GNU Public License
 * Alexandre Díaz <dev@redneboa.es>
 */

var ListController = require('web.ListController');
var Core = require('web.core');

var _t = Core._t;

ListController.include({

    renderButtons: function () {
        this._super.apply(this, arguments); // Sets this.$buttons

        if (this.modelName === 'hotel.room.type') {
            this.$buttons.append("<button class='btn btm-sm o_channel_connector_import_rooms' type='button'>"+_t('Fetch from Channel')+"</button>");
            this.$buttons.find('.o_channel_connector_import_rooms').on('click', this._importRooms.bind(this));
        } else if (this.modelName === 'hotel.folio') {
            this.$buttons.append("<button class='btn btm-sm o_channel_connector_import_reservations' type='button'>"+_t('Fetch from Channel')+"</button>");
            this.$buttons.find('.o_channel_connector_import_reservations').on('click', this._importReservations.bind(this));
        } else if (this.modelName === 'product.pricelist') {
            this.$buttons.append("<button class='btn btm-sm o_channel_connector_import_price_plans' type='button'>"+_t('Fetch from Channel')+"</button>");
            this.$buttons.find('.o_channel_connector_import_price_plans').on('click', this._importPricePlans.bind(this));
            this.$buttons.append("<button class='btn btm-sm btn-danger o_channel_connector_push_price_plans' type='button'>"+_t('Push to Channel')+"</button>");
            this.$buttons.find('.o_channel_connector_push_price_plans').on('click', this._pushPricePlans.bind(this));
        } else if (this.modelName === 'wubook.channel.info') {
            this.$buttons.append("<button class='btn btm-sm o_channel_connector_import_channels_info' type='button'>"+_t('Fetch from Channel')+"</button>");
            this.$buttons.find('.o_channel_connector_import_channels_info').on('click', this._importChannelsInfo.bind(this));
        } else if (this.modelName === 'hotel.room.type.restriction') {
            this.$buttons.append("<button class='btn btm-sm o_channel_connector_import_restriction_plans' type='button'>"+_t('Fetch from Channel')+"</button>");
            this.$buttons.find('.o_channel_connector_import_restriction_plans').on('click', this._importRestrictionPlans.bind(this));
            this.$buttons.append("<button class='btn btm-sm btn-danger o_channel_connector_push_restriction_plans' type='button'>"+_t('Push to Channel')+"</button>");
            this.$buttons.find('.o_channel_connector_push_restriction_plans').on('click', this._pushRestrictionPlans.bind(this));
        } else if (this.modelName === 'hotel.room.type.availability') {
            this.$buttons.append("<button class='btn btm-sm o_channel_connector_import_availability' type='button'>"+_t('Fetch from Channel')+"</button>");
            this.$buttons.find('.o_channel_connector_import_availability').on('click', this._importAvailability.bind(this));
            this.$buttons.append("<button class='btn btm-sm btn-danger o_channel_connector_push_availability' type='button'>"+_t('Push to Channel')+"</button>");
            this.$buttons.find('.o_channel_connector_push_availability').on('click', this._pushAvailability.bind(this));
        }
    },

    _importRooms: function () {
        var self = this;
        this.dataset._model.call('import_rooms', [false]).then(function(results){
            if (!results[0]) {
                self.do_warn(_t('Operation Errors'), _t('Errors while importing rooms. See issues registry.'), true);
            }
            if (results[0] || results[1] > 0) {
                if (results[1] > 0) {
                    self.do_notify(_t('Operation Success'), `<b>${results[1]}</b>` + ' ' + _t('Rooms successfully imported'), false);
                } else {
                    self.do_notify(_t('Operation Success'), _t('No new rooms found. Everything is done.'), false);
                }
                var active_view = self.ViewManager.active_view;
                active_view.controller.reload(); // list view only has reload
            }
        });

        return false;
    },

    _importReservations: function () {
        var self = this;
        console.log(this);
        this.model.import_reservations().then(function(results){
            console.log(results);
            if (!results[0]) {
                self.do_warn(_t('Operation Errors'), _t('Errors while importing reservations. See issues registry.'), true);
            }
            if (results[0] || results[1] > 0) {
                if (results[1] > 0) {
                    self.do_notify(_t('Operation Success'), `<b>${results[1]}</b>` + ' ' + _t('Reservations successfully imported'), false);
                } else {
                    self.do_notify(_t('Operation Success'), _t('No new reservations found. Everything is done.'), false);
                }
                var active_view = self.ViewManager.active_view;
                active_view.controller.reload(); // list view only has reload
            }
        });

        return false;
    },

    _importPricePlans: function () {
        var self = this;
        this.dataset._model.call('import_price_plans', [false]).then(function(results){
            if (!results[0]) {
                self.do_warn(_t('Operation Errors'), _t('Errors while importing price plans from WuBook. See issues log.'), true);
            }
            if (results[0] || results[1] > 0) {
                if (results[1] > 0) {
                    self.do_notify(_t('Operation Success'), `<b>${results[1]}</b>` + ' ' + _t('Price Plans successfully imported'), false);
                } else {
                    self.do_notify(_t('Operation Success'), _t('No new price plans found. Everything is done.'), false);
                }
                var active_view = self.ViewManager.active_view;
                active_view.controller.reload(); // list view only has reload
            }
        });

        return false;
    },

    _pushPricePlans: function () {
        var self = this;
        new Model('wubook').call('push_priceplans', [false]).then(function(results){
            self.do_notify(_t('Operation Success'), _t('Price Plans successfully pushed'), false);
        }).fail(function(){
            self.do_warn(_t('Operation Errors'), _t('Errors while pushing price plans to WuBook. See issues log.'), true);
        });

        return false;
    },

    _importChannelsInfo: function () {
        var self = this;
        this.dataset._model.call('import_channels_info', [false]).then(function(results){
            if (!results[0]) {
                self.do_warn(_t('Operation Errors'), _t('Errors while importing channels info from WuBook. See issues log.'), true);
            }
            if (results[0] || results[1] > 0) {
                if (results[1] > 0) {
                    self.do_notify(_t('Operation Success'), `<b>${results[1]}</b>` + ' ' + _t('Channels Info successfully imported'), false);
                } else {
                    self.do_notify(_t('Operation Success'), _t('No new channels info found. Everything is done.'), false);
                }
                var active_view = self.ViewManager.active_view;
                active_view.controller.reload(); // list view only has reload
            }
        });

        return false;
    },

    _importRestrictionPlans: function () {
        var self = this;
        this.dataset._model.call('import_restriction_plans', [false]).then(function(results){
            if (!results[0]) {
                self.do_warn(_t('Operation Errors'), _t('Errors while importing restriction plans from WuBook. See issues log.'), true);
            }
            if (results[0] || results[1] > 0) {
                if (results[1] > 0) {
                    self.do_notify(_t('Operation Success'), `<b>${results[1]}</b>` + ' ' + _t('Restriction Plans successfully imported'), false);
                } else {
                    self.do_notify(_t('Operation Success'), _t('No new restriction plans found. Everything is done.'), false);
                }
                var active_view = self.ViewManager.active_view;
                active_view.controller.reload(); // list view only has reload
            }
        });

        return false;
    },

    _pushRestrictionPlans: function () {
        var self = this;
        new Model('wubook').call('push_restrictions', [false]).then(function(results){
            self.do_notify(_t('Operation Success'), _t('Restrictions successfully pushed'), false);
        }).fail(function(){
            self.do_warn(_t('Operation Errors'), _t('Errors while pushing restrictions to WuBook. See issues log.'), true);
        });

        return false;
    },

    _importAvailability: function () {
        this.do_action('hotel_wubook_proto.action_wubook_import_availability');
        return false;
    },

    _pushAvailability: function () {
        var self = this;
        new Model('wubook').call('push_availability', [false]).then(function(results){
            self.do_notify(_t('Operation Success'), _t('Availability successfully pushed'), false);
        }).fail(function(){
            self.do_warn(_t('Operation Errors'), _t('Errors while pushing availability to Channel. See issues log.'), true);
        });

        return false;
    }
});

});
