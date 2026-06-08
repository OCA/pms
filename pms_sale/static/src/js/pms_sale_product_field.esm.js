/** @odoo-module **/
// Copyright (c) 2021 Gray Matter Logic
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import {SaleOrderLineProductField} from "@sale/js/sale_product_field";
import {patch} from "@web/core/utils/patch";
import {useService} from "@web/core/utils/hooks";

patch(SaleOrderLineProductField.prototype, {
    setup() {
        super.setup();
        this.action = useService("action");
    },
    get isPmsReservation() {
        return Boolean(this.props.record.data.reservation_ok);
    },
    get hasConfigurationButton() {
        return super.hasConfigurationButton || this.isPmsReservation;
    },
    onEditConfiguration() {
        if (this.isPmsReservation) {
            this._openPmsConfigurator();
        } else {
            super.onEditConfiguration();
        }
    },
    _onProductUpdate() {
        if (this.isPmsReservation) {
            this._openPmsConfigurator();
        } else {
            super._onProductUpdate();
        }
    },
    _openPmsConfigurator() {
        const record = this.props.record;
        const data = record.data;
        const saleOrder = record.model.root.data;
        const actionContext = {
            default_product_id: data.product_id?.id,
        };
        if (data.pms_reservation_id?.id) {
            actionContext.default_existing_reservation_id = data.pms_reservation_id.id;
        }
        if (saleOrder.currency_id?.id) {
            actionContext.default_currency_id = saleOrder.currency_id.id;
        }
        if (saleOrder.partner_id?.id) {
            actionContext.web_partner_id = saleOrder.partner_id.id;
        }
        this.action.doAction("pms_sale.pms_configurator_action", {
            additionalContext: actionContext,
            onClose: async (closeInfo) => {
                if (
                    !closeInfo?.ReservationConfiguration ||
                    closeInfo.special ||
                    closeInfo.dismiss
                ) {
                    if (!data.pms_reservation_id?.id) {
                        record.update({[this.props.name]: undefined});
                    }
                } else {
                    record.update(closeInfo.ReservationConfiguration);
                }
            },
        });
    },
});
