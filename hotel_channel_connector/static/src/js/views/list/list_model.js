odoo.define('hotel_channel_connector.ListModel', function(require) {
'use strict';
/*
 * Hotel Channel Connector
 * GNU Public License
 * Alexandre Díaz <dev@redneboa.es>
 */

var BasicModel = require('web.BasicModel'),
    Session = require('web.session');

return BasicModel.extend({

    import_reservations: function() {
        return this._rpc({
            model: 'hotel.folio',
            method: 'import_reservations',
            args: undefined,
            context: Session.user_context,
        });
    },

});

});
