odoo.define('hotel.SwitchHotelMenu', function(require) {
"use strict";

var config = require('web.config');
var core = require('web.core');
var session = require('web.session');
var SystrayMenu = require('web.SystrayMenu');
var Widget = require('web.Widget');

var _t = core._t;

var SwitchHotelMenu = Widget.extend({
    template: 'hotel.SwitchHotelMenu',
    willStart: function() {
        this.isMobile = config.device.isMobile;
        if (!session.user_hotels) {
            return $.Deferred().reject();
        }
        return this._super();
    },
    start: function() {
        var self = this;
        this.$el.on('click', '.dropdown-menu li a[data-menu]', _.debounce(function(ev) {
            ev.preventDefault();
            var hotel_id = $(ev.currentTarget).data('hotel-id');
            self._rpc({
                    model: 'res.users',
                    method: 'write',
                    args: [[session.uid], {'hotel_id': hotel_id}],
                })
                .then(function() {
                    location.reload();
                });
        }, 1500, true));

        var hotels_list = '';
        if (this.isMobile) {
            hotels_list = '<li class="bg-info">' + _t('Tap on the list to change hotel') + '</li>';
        }
        else {
            self.$('.oe_topbar_name').text(session.user_hotels.current_hotel[1]);
        }
        _.each(session.user_hotels.allowed_hotels, function(hotel) {
            var a = '';
            if (hotel[0] === session.user_hotels.current_hotel[0]) {
                a = '<i class="fa fa-check mr8"></i>';
            } else {
                a = '<span class="mr24"/>';
            }
            hotels_list += '<li><a href="#" data-menu="hotel" data-hotel-id="' + hotel[0] + '">' + a + hotel[1] + '</a></li>';
        });
        self.$('.dropdown-menu').html(hotels_list);
        return this._super();
    },
});

SystrayMenu.Items.push(SwitchHotelMenu);

return SwitchHotelMenu;

});
