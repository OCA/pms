odoo.define("pms_helpdesk_mgmt.hotel_on_company", function (require) {
    "use strict";

    var publicWidget = require("web.public.widget");
    var core = require("web.core");

    publicWidget.registry.HotelOnCompany = publicWidget.Widget.extend({
        selector: 'form[action="/submitted/ticket"]',
        events: {
            'change select[name="company_id"]': "_onCompanyChange",
            'change select[name="pms_property_id"]': "_onPropertyChange",
        },

        _onCompanyChange: function (ev) {
            var self = this;
            var companyId = $(ev.currentTarget).val();
            var $propertySelect = this.$('select[name="pms_property_id"]');

            if (companyId) {
                this._rpc({
                    route: "/get_properties",
                    params: {
                        company_id: companyId,
                    },
                }).then(function (result) {
                    $propertySelect.empty();
                    $propertySelect.append(
                        '<option value="">Select a Property</option>'
                    );

                    _.each(result.properties, function (property) {
                        $propertySelect.append(
                            '<option value="' +
                                property.id +
                                '">' +
                                property.name +
                                "</option>"
                        );
                    });
                });
            } else {
                $propertySelect.empty();
                $propertySelect.append('<option value="">Select a Property</option>');
            }
        },

        _onPropertyChange: function (ev) {
            var self = this;
            var propertyId = $(ev.currentTarget).val();
            var $roomSelect = this.$('select[name="room_id"]');

            if (propertyId) {
                this._rpc({
                    route: "/get_rooms",
                    params: {
                        property_id: propertyId,
                    },
                }).then(function (result) {
                    $roomSelect.empty();
                    $roomSelect.append('<option value="">Select a Room</option>');

                    _.each(result.rooms, function (room) {
                        $roomSelect.append(
                            '<option value="' + room.id + '">' + room.name + "</option>"
                        );
                    });
                });
            } else {
                $roomSelect.empty();
                $roomSelect.append('<option value="">Select a Room</option>');
            }
        },
    });
});
