odoo.define('pms', function (require) {
'use strict';

var core = require('web.core');
var _t = core._t;
var utils = require('web.utils');
var publicWidget = require('web.public.widget');

publicWidget.registry.SendInvitationData = publicWidget.Widget.extend({
    selector: '.o_send_invitation_js',
    events: {
        'click': '_onReminderToggleClick',
    },

    /**
     * @override
     */
//    init: function () {
//        this._super.apply(this, arguments);
//        this._onReminderToggleClick = _.debounce(this._onReminderToggleClick, 500, true);
//    },

    //--------------------------------------------------------------------------
    // Handlers
    //-------------------------------------------------------------------------

    /**
     * @private
     * @param {Event} ev
     */
    _onReminderToggleClick: function (ev) {
//        var self = this;
//        var $checkinPartner = $(ev.currentTarget).find('i');

        this._rpc({
            route: '/my/precheckin/send_invitation',
            params: {
                checkin_partner_id: $checkinPartner.data('checkin_partner_id'),
            },
            })/*.then(function (result) {*/
//            if (result.error && result.error === 'ignored') {
//                self.displayNotification({
//                    type: 'info',
//                    title: _t('Error'),
//                    message: _.str.sprintf(_t('Talk already in your Favorites')),
//                });
//            } else {
//                self.reminderOn = reminderOnValue;
//                var reminderText = self.reminderOn ? _t('Favorite On') : _t('Set Favorite');
//                self.$('.o_wetrack_js_reminder_text').text(reminderText);
//                self._updateDisplay();
//                var message = self.reminderOn ? _t('Talk added to your Favorites') : _t('Talk removed from your Favorites');
//                self.displayNotification({
//                    type: 'info',
//                    title: message
//                });
//            }
//            if (result.visitor_uuid) {
//                utils.set_cookie('visitor_uuid', result.visitor_uuid);
//            }
//        });
    },


});
return publicWidget.registry.SendInvitationData;

});
