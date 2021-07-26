from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsReservationService(Component):
    _inherit = "base.rest.service"
    _name = "pms.reservation.service"
    _usage = "reservations"
    _collection = "pms.reservation.service"

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "GET"
            )
        ],
        input_param=Datamodel("pms.reservation.search.param"),
        output_param=Datamodel("pms.reservation.short.info", is_list=True),
        auth="public",
    )
    def search(self, reservation_search_param):
        domain = []
        if reservation_search_param.name:
            domain.append(("name", "like", reservation_search_param.name))
        if reservation_search_param.id:
            domain.append(("id", "=", reservation_search_param.id))
        res = []
        PmsReservationShortInfo = self.env.datamodels["pms.reservation.short.info"]
        for reservation in self.env["pms.reservation"].sudo().search(
            domain,
        ):
            res.append(
                PmsReservationShortInfo(
                    id=reservation.id,
                    partner=reservation.partner_id.name,
                    checkin=str(reservation.checkin),
                    checkout=str(reservation.checkout),
                    preferred_room_id=reservation.preferred_room_id.name
                    if reservation.preferred_room_id
                    else "",
                    room_type_id=reservation.room_type_id.name
                    if reservation.room_type_id
                    else "",
                    name=reservation.name,
                )
            )
        return res
