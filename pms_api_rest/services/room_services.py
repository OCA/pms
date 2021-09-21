from datetime import datetime

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsFolioService(Component):
    _inherit = "base.rest.service"
    _name = "pms.room.service"
    _usage = "rooms"
    _collection = "pms.reservation.service"

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.folio.search.param"),
        output_param=Datamodel("pms.folio.short.info", is_list=True),
        auth="public",
    )
    def get_rooms(self, room_search_param):
        domain = []
        if room_search_param.name:
            domain.append(("name", "like", room_search_param.name))
        if room_search_param.id:
            domain.append(("id", "=", room_search_param.id))
        result_rooms = []
        PmsRoomShortInfo = self.env.datamodels["pms.room.short.info"]
        for room in (
            self.env["pms.room"]
            .sudo()
            .search(
                domain,
            )
        ):

            result_rooms.append(
                PmsRoomShortInfo(
                    id=room.id,
                    name=room.name,
                )
            )
        return result_rooms
