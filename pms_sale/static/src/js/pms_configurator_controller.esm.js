/** @odoo-module **/
// Copyright (c) 2021 Gray Matter Logic
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import {serializeDateTime} from "@web/core/l10n/dates";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {formView} from "@web/views/form/form_view";

export class PMSConfiguratorFormController extends formView.Controller {
    setup() {
        super.setup();
        this.action = useService("action");
        this.orm = useService("orm");
    }

    async onRecordSaved(record) {
        await super.onRecordSaved(...arguments);
        const data = record.data;
        const guestCommands = [[5, 0, 0]];
        for (const guestRecord of data.guest_ids?.records || []) {
            const d = guestRecord.data;
            if (d?.name) {
                guestCommands.push([
                    0,
                    0,
                    {
                        name: d.name,
                        partner_id: d.partner_id ? d.partner_id.id : false,
                        phone: d.phone || false,
                        email: d.email || false,
                    },
                ]);
            }
        }
        const reservationVals = {
            property_id: data.property_id?.id || false,
            reservation_type_id: data.reservation_id?.id || false,
            start: data.start ? serializeDateTime(data.start) : false,
            stop: data.stop ? serializeDateTime(data.stop) : false,
            no_of_guests: data.no_of_guests || 0,
            guest_ids: guestCommands,
        };
        let reservationId = data.existing_reservation_id;
        if (reservationId) {
            await this.orm.write("pms.reservation", [reservationId], reservationVals);
        } else {
            [reservationId] = await this.orm.create("pms.reservation", [
                reservationVals,
            ]);
        }
        return this.action.doAction({
            type: "ir.actions.act_window_close",
            infos: {
                ReservationConfiguration: {
                    product_uom_qty: data.duration,
                    price_unit: data.price || 0,
                    pms_reservation_id: {id: reservationId},
                },
            },
        });
    }
}

registry.category("views").add("pms_configurator_form", {
    ...formView,
    Controller: PMSConfiguratorFormController,
});
