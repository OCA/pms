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
                // Hacer una llamada AJAX para obtener las propiedades de la compañía seleccionada
                this._rpc({
                    route: "/get_properties",
                    params: {
                        company_id: companyId,
                    },
                }).then(function (result) {
                    // Limpiar el select de propiedades
                    $propertySelect.empty();
                    $propertySelect.append(
                        '<option value="">Select a Property</option>'
                    );

                    // Agregar las propiedades obtenidas al select
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
                // Limpiar el select de propiedades si no hay compañía seleccionada
                $propertySelect.empty();
                $propertySelect.append('<option value="">Select a Property</option>');
            }
        },

        _onPropertyChange: function (ev) {
            var self = this;
            var propertyId = $(ev.currentTarget).val();
            var $roomSelect = this.$('select[name="room_id"]');

            if (propertyId) {
                // Hacer una llamada AJAX para obtener las habitaciones de la propiedad seleccionada
                this._rpc({
                    route: "/get_rooms",
                    params: {
                        property_id: propertyId,
                    },
                }).then(function (result) {
                    // Limpiar el select de habitaciones
                    $roomSelect.empty();
                    $roomSelect.append('<option value="">Select a Room</option>');

                    // Agregar las habitaciones obtenidas al select
                    _.each(result.rooms, function (room) {
                        $roomSelect.append(
                            '<option value="' + room.id + '">' + room.name + "</option>"
                        );
                    });
                });
            } else {
                // Limpiar el select de habitaciones si no hay propiedad seleccionada
                $roomSelect.empty();
                $roomSelect.append('<option value="">Select a Room</option>');
            }
        },
    });
});
