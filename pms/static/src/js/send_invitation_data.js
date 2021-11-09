odoo.define("pms.SendInvitationData", function (require) {
    "use strict";

    require("web.dom_ready");
    var publicWidget = require("web.public.widget");

    publicWidget.registry.SendInvitationData = publicWidget.Widget.extend({
        selector: ".o_send_invitation_js",
        events: {
            click: "_onReminderToggleClick",
        },

        _onReminderToggleClick: function (ev) {
            ev.preventDefault();
            var checkinPartnerId = $(ev.currentTarget)
                .parent()
                .parent()
                .parent()
                .find("input[name=checkin_partner_id]")
                .val();
            var firstname = $(ev.currentTarget)
                .parent()
                .parent()
                .find("input[name=invitation_firstname]")
                .val();
            var email = $(ev.currentTarget)
                .parent()
                .parent()
                .find("input[name=invitation_email]")
                .val();
            var error_firstname = $(ev.currentTarget)
                .parent()
                .parent()
                .find("span:first");
            var error_email = $(ev.currentTarget)
                .parent()
                .parent()
                .find("input[name=invitation_email]")
                .siblings("span");
            console.log(error_firstname);
            console.log(error_email);
            if (firstname === "" || email === "") {
                if (firstname === "") {
                    error_firstname.removeClass("d-none");
                } else {
                    error_firstname.addClass("d-none");
                }
                if (email === "") {
                    error_email.removeClass("d-none");
                } else {
                    error_email.addClass("d-none");
                }
            } else {
                error_firstname.addClass("d-none");
                error_email.addClass("d-none");
                this._rpc({
                    route: "/my/precheckin/send_invitation",
                    params: {
                        checkin_partner_id: checkinPartnerId,
                        firstname: firstname,
                        email: email,
                    },
                });
            }
        },
    });
    return publicWidget.registry.SendInvitationData;
});
