/** @odoo-module **/

import {debounce} from "@web/core/utils/timing";

import {isConnectionError} from "point_of_sale.utils";
import {onWillUnmount, useRef} from "@odoo/owl";
import PosComponent from "point_of_sale.PosComponent";
import Registries from "point_of_sale.Registries";
import {useAsyncLockedMethod} from "point_of_sale.custom_hooks";
import {useAutofocus, useListener} from "@web/core/utils/hooks";

class ReservationListScreen extends PosComponent {
    setup() {
        super.setup();
        useAutofocus({refName: "search-word-input-reservation"});
        // UseListener("click-save", () => this.env.bus.trigger("save-partner"));
        // useListener("click-edit", () => this.editReservation());
        useListener("save-changes", useAsyncLockedMethod(this.saveChanges));
        this.searchWordInputRef = useRef("search-word-input-reservation");

        // We are not using useState here because the object
        // passed to useState converts the object and its contents
        // to Observer proxy. Not sure of the side-effects of making
        // a persistent object, such as pos, into Observer. But it
        // is better to be safe.
        this.state = {
            query: null,
            selectedReservation: this.props.reservation,
            detailIsShown: false,
            isEditMode: false,
            editModeProps: {
                reservation: null,
            },
            previousQuery: "",
            currentOffset: 0,
        };
        this.updateReservationList = debounce(this.updateReservationList, 70);
        onWillUnmount(this.updateReservationList.cancel);
    }

    // Lifecycle hooks
    back() {
        if (this.state.detailIsShown) {
            this.state.detailIsShown = false;
            this.render(true);
        } else {
            this.props.resolve({confirmed: false, payload: false});
            this.trigger("close-temp-screen");
        }
    }
    confirm() {
        this.props.resolve({confirmed: true, payload: this.state.selectedReservation});
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

    clickNext() {
        this.state.selectedReservation =
            this.nextButton.command === "set" ? this.state.selectedReservation : null;
        this.confirm();
    }
    // Methods

    _clearSearch() {
        this.searchWordInputRef.el.value = "";
        this.state.query = "";
        this.render(true);
    }

    // We declare this event handler as a debounce function in
    // order to lower its trigger rate.
    async updateReservationList(event) {
        this.state.query = event.target.value;
        this.render(true);
    }

    clickReservation(reservation) {
        if (this.state.selectedReservation === reservation) {
            this.state.selectedCReservation = null;
        } else {
            this.state.selectedReservation = reservation;
        }
        this.render(true);
    }

    editReservation(reservation) {
        this.state.editModeProps.reservation = reservation;
        this.activateEditMode();
    }

    activateEditMode() {
        this.state.detailIsShown = true;
        this.render(true);
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

    async saveChanges(event) {
        try {
            const reservartionId = await this.rpc({
                model: "pm.reservation",
                method: "create_from_ui",
                args: [event.detail.processedChanges],
            });
            await this.env.pos._load([reservartionId]);
            this.state.selectedReservation =
                this.env.pos.db.get_reservation_by_id(reservartionId);
            this.confirm();
        } catch (error) {
            if (isConnectionError(error)) {
                await this.showPopup("OfflineErrorPopup", {
                    title: this.env._t("Offline"),
                    body: this.env._t("Unable to save changes."),
                });
            } else {
                throw error;
            }
        }
    }

    async searchReservation() {
        if (this.state.previousQuery != this.state.query) {
            this.state.currentOffset = 0;
        }
        const result = await this.getNewReservations();
        this.env.pos.addReservations(result);
        this.render(true);
        if (this.state.previousQuery == this.state.query) {
            this.state.currentOffset += result.length;
        } else {
            this.state.previousQuery = this.state.query;
            this.state.currentOffset = result.length;
        }
        return result;
    }
}

ReservationListScreen.template = "ReservationListScreen";

Registries.Component.add(ReservationListScreen);
