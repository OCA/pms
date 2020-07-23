odoo.define('pms.SwitchPmsMenu', function(require) {
"use strict";

var config = require('web.config');
var core = require('web.core');
var session = require('web.session');
var SystrayMenu = require('web.SystrayMenu');
var Widget = require('web.Widget');

var _t = core._t;

var SwitchPmsMenu = Widget.extend({
    template: 'pms.SwitchPmsMenu',
    willStart: function() {
        this.isMobile = config.device.isMobile;
        if (!session.user_pms) {
            return $.Deferred().reject();
        }
        return this._super();
    },
    start: function() {
        var self = this;
        this.$el.on('click', '.dropdown-menu li a[data-menu]', _.debounce(function(ev) {
            ev.preventDefault();
            var pms_property_id = $(ev.currentTarget).data('property-id');
            self._rpc({
                    model: 'res.users',
                    method: 'write',
                    args: [[session.uid], {'pms_property_id': pms_property_id}],
                })
                .then(function() {
                    location.reload();
                });
        }, 1500, true));

        var properties_list = '';
        if (this.isMobile) {
            propertiess_list = '<li class="bg-info">' + _t('Tap on the list to change property') + '</li>';
        }
        else {
            self.$('.oe_topbar_name').text(session.user_properties.current_property[1]);
        }
        _.each(session.user_properties.allowed_propierties, function(property) {
            var a = '';
            if (property[0] === session.user_properties.current_property[0]) {
                a = '<i class="fa fa-check mr8"></i>';
            } else {
                a = '<span class="mr24"/>';
            }
            properties_list += '<li><a href="#" data-menu="property" data-property-id="' + property[0] + '">' + a + property[1] + '</a></li>';
        });
        self.$('.dropdown-menu').html(properties_list);
        return this._super();
    },
});

SystrayMenu.Items.push(SwitchPmsMenu);

return SwitchPmsMenu;

});
