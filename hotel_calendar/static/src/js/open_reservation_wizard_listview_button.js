// Copyright 2018 Alexandre Díaz <dev@redneboa.es>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
odoo.define('hotel_calendar.listview_button_open_reservation_wizard', function(require) {
'use strict';

var ListView = require('web.ListView'),
    Core = require('web.core'),

    _t = Core._t;


ListView.include({
    render_buttons: function () {
        var self = this;
        this._super.apply(this, arguments); // Sets this.$buttons

        if (this.dataset.model == 'hotel.reservation') {
            this.$buttons.append("<button class='oe_button oe_open_reservation_wizard oe_highlight' type='button'>"+_t('Open Wizard')+"</button>");
            this.$buttons.find('.oe_open_reservation_wizard').on('click', function(){
                self.do_action('hotel_calendar.open_wizard_reservations');
            });
        }
    }
});

return ListView;

});
