from datetime import datetime

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsCalendarService(Component):
    _inherit = "base.rest.service"
    _name = "pms.calendar.service"
    _usage = "calendar"
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
        input_param=Datamodel("pms.calendar.search.param"),
        output_param=Datamodel("pms.calendar.short.info", is_list=True),
        auth="public",
    )
    def get_calendar(self, calendar_search_param):
        domain = list()
        domain.append(("date", ">=", datetime.fromisoformat(calendar_search_param.date_from)))
        domain.append(("date", "<=", datetime.fromisoformat(calendar_search_param.date_to)))
        result_lines = []
        PmsCalendarShortInfo = self.env.datamodels["pms.calendar.short.info"]
        for line in (
            self.env["pms.reservation.line"]
            .sudo()
            .search(
                domain,
            )
        ):
            result_lines.append(
                PmsCalendarShortInfo(
                    id=line.id,
                    roomId=line.room_id.id,
                    date=datetime.combine(line.date, datetime.min.time()).isoformat(),
                    partnerId=line.reservation_id.partner_id.id,
                    reservationId=line.reservation_id,
                )
            )
        return result_lines
