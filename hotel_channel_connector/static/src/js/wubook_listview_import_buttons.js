odoo.define('hotel_channel_connector.listview_button_import_rooms', function(require) {
'use strict';
/*
 * Hotel Channel Connector
 * GNU Public License
 * Alexandre Díaz <dev@redneboa.es>
 */

var ListView = require('web.ListView');
var Core = require('web.core');
var Model = require('web.DataModel');

var _t = Core._t;

function import_rooms(){
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
}

function import_reservations(){
	var self = this;
	this.dataset._model.call('import_reservations', [false]).then(function(results){
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
}

function import_price_plans(){
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
}


function push_price_plans(){
	var self = this;
	new Model('wubook').call('push_priceplans', [false]).then(function(results){
			self.do_notify(_t('Operation Success'), _t('Price Plans successfully pushed'), false);
	}).fail(function(){
		self.do_warn(_t('Operation Errors'), _t('Errors while pushing price plans to WuBook. See issues log.'), true);
	});

	return false;
}

function import_channels_info(){
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
}

function import_restriction_plans(){
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
}

function push_restriction_plans(){
	var self = this;
	new Model('wubook').call('push_restrictions', [false]).then(function(results){
			self.do_notify(_t('Operation Success'), _t('Restrictions successfully pushed'), false);
	}).fail(function(){
		self.do_warn(_t('Operation Errors'), _t('Errors while pushing restrictions to WuBook. See issues log.'), true);
	});

	return false;
}

function import_availability(){
  this.do_action('hotel_wubook_proto.action_wubook_import_availability');
	return false;
}


function push_availability(){
	var self = this;
	new Model('wubook').call('push_availability', [false]).then(function(results){
			self.do_notify(_t('Operation Success'), _t('Availability successfully pushed'), false);
	}).fail(function(){
		self.do_warn(_t('Operation Errors'), _t('Errors while pushing availability to Channel. See issues log.'), true);
	});

	return false;
}

ListView.include({
	render_buttons: function () {
		this._super.apply(this, arguments); // Sets this.$buttons

		if (this.dataset.model === 'hotel.room.type') {
	    	this.$buttons.append("<button class='oe_button oe_channel_connector_import_rooms oe_highlight' type='button'>"+_t('Fetch from Channel')+"</button>");
	    	this.$buttons.find('.oe_channel_connector_import_rooms').on('click', import_rooms.bind(this));
    } else if (this.dataset.model === 'hotel.folio') {
    	this.$buttons.append("<button class='oe_button oe_channel_connector_import_reservations oe_highlight' type='button'>"+_t('Fetch from Channel')+"</button>");
    	this.$buttons.find('.oe_channel_connector_import_reservations').on('click', import_reservations.bind(this));
    } else if (this.dataset.model === 'product.pricelist') {
    	this.$buttons.append("<button class='oe_button oe_channel_connector_import_price_plans oe_highlight' type='button'>"+_t('Fetch from Channel')+"</button>");
    	this.$buttons.find('.oe_channel_connector_import_price_plans').on('click', import_price_plans.bind(this));
			this.$buttons.append("<button class='oe_button oe_channel_connector_push_price_plans' style='background-color:red; color:white;' type='button'>"+_t('Push to Channel')+"</button>");
    	this.$buttons.find('.oe_channel_connector_push_price_plans').on('click', push_price_plans.bind(this));
    } else if (this.dataset.model === 'wubook.channel.info') {
    	this.$buttons.append("<button class='oe_button oe_channel_connector_import_channels_info oe_highlight' type='button'>"+_t('Fetch from Channel')+"</button>");
    	this.$buttons.find('.oe_channel_connector_import_channels_info').on('click', import_channels_info.bind(this));
    } else if (this.dataset.model === 'hotel.virtual.room.restriction') {
    	this.$buttons.append("<button class='oe_button oe_channel_connector_import_restriction_plans oe_highlight' type='button'>"+_t('Fetch from Channel')+"</button>");
    	this.$buttons.find('.oe_channel_connector_import_restriction_plans').on('click', import_restriction_plans.bind(this));
			this.$buttons.append("<button class='oe_button oe_channel_connector_push_restriction_plans' style='background-color:red; color:white;' type='button'>"+_t('Push to Channel')+"</button>");
			this.$buttons.find('.oe_channel_connector_push_restriction_plans').on('click', push_restriction_plans.bind(this));
		} else if (this.dataset.model === 'hotel.virtual.room.availability') {
    	this.$buttons.append("<button class='oe_button oe_channel_connector_import_availability oe_highlight' type='button'>"+_t('Fetch from Channel')+"</button>");
    	this.$buttons.find('.oe_channel_connector_import_availability').on('click', import_availability.bind(this));
			this.$buttons.append("<button class='oe_button oe_channel_connector_push_availability' style='background-color:red; color:white;' type='button'>"+_t('Push to Channel')+"</button>");
    	this.$buttons.find('.oe_channel_connector_push_availability').on('click', push_availability.bind(this));
		}
  }
});

});
