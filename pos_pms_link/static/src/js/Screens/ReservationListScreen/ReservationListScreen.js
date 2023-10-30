odoo.define("pos_pms_link.ReservationListScreen", function (require) {
    "use strict";

    const {debounce} = owl.utils;
    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");
    const {useListener} = require("web.custom_hooks");
    const {isRpcError} = require("point_of_sale.utils");
    const {useAsyncLockedMethod} = require("point_of_sale.custom_hooks");

    /**
     * Render this screen using `showTempScreen` to select client.
     * When the shown screen is confirmed ('Set Customer' or 'Deselect Customer'
     * button is clicked), the call to `showTempScreen` resolves to the
     * selected client. E.g.
     *
     * ```js
     * const { confirmed, payload: selectedClient } = await showTempScreen('ClientListScreen');
     * if (confirmed) {
     *   // do something with the selectedClient
     * }
     * ```
     *
     * @props client - originally selected client
     */
    class ReservationListScreen extends PosComponent {
        constructor() {
            super(...arguments);
            this.lockedSaveChanges = useAsyncLockedMethod(this.saveChanges);
            useListener("click-save", () => this.env.bus.trigger("save-customer"));
            useListener("click-edit", () => this.editReservation());
            useListener("save-changes", this.lockedSaveChanges);

            // We are not using useState here because the object
            // passed to useState converts the object and its contents
            // to Observer proxy. Not sure of the side-effects of making
            // a persistent object, such as pos, into owl.Observer. But it
            // is better to be safe.
            this.state = {
                query: null,
                selectedReservation: this.props.reservation,
                detailIsShown: false,
                isEditMode: false,
                editModeProps: {
                    reservation: {},
                },
            };
            this.updateReservationList = debounce(this.updateReservationList, 70);
        }

        // Lifecycle hooks
        back() {
            if (this.state.detailIsShown) {
                this.state.detailIsShown = false;
                this.render();
            } else {
                this.props.resolve({confirmed: false, payload: false});
                this.trigger("close-temp-screen");
            }
        }
        confirm() {
            this.props.resolve({
                confirmed: true,
                payload: this.state.selectedReservation,
            });
            this.trigger("close-temp-screen");
        }
        // Getters

        get currentOrder() {
            return this.env.pos.get_order();
        }

        get reservations() {
            if (this.state.query && this.state.query.trim() !== "") {
                return this.env.pos.db.search_reservation(this.state.query.trim());
            }
            return this.env.pos.db.get_reservations_sorted(1000);
        }
        get isNextButtonVisible() {
            return Boolean(this.state.selectedReservation);
        }
        /**
         * Returns the text and command of the next button.
         * The command field is used by the clickNext call.
         */
        get nextButton() {
            if (!this.props.reservation) {
                return {command: "set", text: this.env._t("Set Reservation")};
            } else if (
                this.props.reservation &&
                this.props.reservation === this.state.selectedReservation
            ) {
                return {command: "deselect", text: this.env._t("Deselect Reservation")};
            }
            return {command: "set", text: this.env._t("Change Reservation")};
        }

        // Methods

        // We declare this event handler as a debounce function in
        // order to lower its trigger rate.
        updateReservationList(event) {
            this.state.query = event.target.value;
            const reservations = this.reservations;
            if (event.code === "Enter" && reservations.length === 1) {
                this.state.selectedReservation = reservations[0];
                this.clickNext();
            } else {
                this.render();
            }
        }
        clickReservation(event) {
            const reservation = event.detail.reservation;
            if (this.state.selectedReservation === reservation) {
                this.state.selectedCReservation = null;
            } else {
                this.state.selectedReservation = reservation;
            }
            this.render();
        }
        editReservation() {
            this.state.editModeProps = {
                reservation: this.state.selectedReservation,
            };
            this.state.detailIsShown = true;
            this.render();
        }
        clickNext() {
            this.state.selectedReservation =
                this.nextButton.command === "set"
                    ? this.state.selectedReservation
                    : null;
            this.confirm();
        }
        activateEditMode(event) {
            const {isNewReservation} = event.detail;
            this.state.isEditMode = true;
            this.state.detailIsShown = true;
            this.state.isNewReservation = isNewReservation;
            if (!isNewReservation) {
                this.state.editModeProps = {
                    reservation: this.state.selectedReservation,
                };
            }
            this.render();
        }
        deactivateEditMode() {
            this.state.isEditMode = false;
            this.state.editModeProps = {
                reservation: {},
            };
            this.render();
        }
        cancelEdit() {
            this.deactivateEditMode();
        }
    }
    ReservationListScreen.template = "ReservationListScreen";

    Registries.Component.add(ReservationListScreen);

    return ReservationListScreen;
});
