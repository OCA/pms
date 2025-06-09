odoo.define("pms.payment_form", (require) => {
    "use strict";

    const checkoutForm = require("payment.checkout_form");
    const manageForm = require("payment.manage_form");

    const pmsPaymentMixin = {
        // --------------------------------------------------------------------------
        // Private
        // --------------------------------------------------------------------------

        /**
         * Add `pms_folio_id` to the transaction route params if it is provided.
         *
         * @override method from payment.payment_form_mixin
         * @private
         * @param {String} code - The code of the selected payment option's provider
         * @param {Number} paymentOptionId - The id of the selected payment option
         * @param {String} flow - The online payment flow of the selected payment option
         * @returns {Object} The extended transaction route params
         */
        _prepareTransactionRouteParams: function (code, paymentOptionId, flow) {
            const transactionRouteParams = this._super(code, paymentOptionId, flow);
            return {
                ...transactionRouteParams,
                pms_folio_id: this.txContext.pmsFolioId
                    ? parseInt(this.txContext.pmsFolioId, 10)
                    : undefined,
            };
        },
    };

    checkoutForm.include(pmsPaymentMixin);
    manageForm.include(pmsPaymentMixin);
});
