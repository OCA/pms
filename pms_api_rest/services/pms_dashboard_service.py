from odoo.addons.component.core import Component
from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo import fields
from datetime import datetime



class PmsDashboardServices(Component):
    _inherit = "base.rest.service"
    _name = "pms.dashboard.service"
    _usage = "dashboard"
    _collection = "pms.services"

    @restapi.method(
        [
            (
                [
                    "/pending-checkins",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.dashboard.pending.reservations.search.param"),
        output_param=Datamodel("pms.dashboard.pending.reservations"),
        auth="jwt_api_pms",
    )
    def get_pending_checkin_reservations(self, pms_reservations_search_param):
        date = fields.Date.from_string(pms_reservations_search_param.date)


        pendingReservations = self.env["pms.reservation"].search_count(
            [
                ("checkin", "=", date),
                ("state", "in", ("confirm", "arrival_delayed")),
                ("reservation_type", "!=", "out")
            ]
        )
        completedReservations = self.env["pms.reservation"].search_count(
            [
                ("checkin", "=", date),
                ("state", "=", "onboard"),
            ]
        )
        PmsDashboardPendingReservations = self.env.datamodels["pms.dashboard.pending.reservations"]

        return PmsDashboardPendingReservations(
            pendingReservations=pendingReservations,
            completedReservations=completedReservations,
        )

    @restapi.method(
        [
            (
                [
                    "/pending-checkouts",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.dashboard.pending.reservations.search.param"),
        output_param=Datamodel("pms.dashboard.pending.reservations"),
        auth="jwt_api_pms",
    )
    def get_pending_checkout_reservations(self, pms_reservations_search_param):
        date = fields.Date.from_string(pms_reservations_search_param.date)


        pending_reservations = self.env["pms.reservation"].search_count(
            [
                ("checkout", "=", date),
                ("state", "in", ("onboard", "departure_delayed")),
                ("reservation_type", "!=", "out"),
            ]
        )
        completed_reservations = self.env["pms.reservation"].search_count(
            [
                ("checkout", "=", date),
                ("state", "=", "done"),
            ]
        )
        PmsDashboardPendingReservations = self.env.datamodels["pms.dashboard.pending.reservations"]

        return PmsDashboardPendingReservations(
            pendingReservations=pending_reservations,
            completedReservations=completed_reservations,
        )


