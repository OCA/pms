odoo.define('hotel_channel_connector.ListView', function(require) {
'use strict';
/*
 * Hotel Channel Connector
 * GNU Public License
 * Alexandre Díaz <dev@redneboa.es>
 */

var ListView = require('web.ListView'),
    ListModel = require('hotel_channel_connector.ListModel');

ListView.include({
    config: _.extend({}, ListView.prototype.config, {
        Model: ListModel,
    }),
});

});
