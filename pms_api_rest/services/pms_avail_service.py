from datetime import datetime, timedelta

from odoo import _, fields
from odoo.exceptions import MissingError

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsAvailService(Component):
    _inherit = "base.rest.service"
    _name = "pms.avail.service"
    _usage = "avails"
    _collection = "pms.services"

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.avail.search.param"),
        output_param=Datamodel("pms.avail.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_avails(self, avails_search_param):
        if not (
            avails_search_param.availabilityFrom
            and avails_search_param.availabilityTo
            and avails_search_param.pmsPropertyId
        ):
            raise MissingError(_("Missing required parameters"))
        pricelist_id = avails_search_param.pricelistId or False
        room_type_id = avails_search_param.roomTypeId or False
        pms_property = self.env["pms.property"].browse(
            avails_search_param.pmsPropertyId
        )
        PmsAvailInfo = self.env.datamodels["pms.avail.info"]
        result_avails = []
        date_from = fields.Date.from_string(avails_search_param.availabilityFrom)
        date_to = fields.Date.from_string(avails_search_param.availabilityTo)
        dates = [
            date_from + timedelta(days=x)
            for x in range(0, (date_to - date_from).days + 1)
        ]
        for item_date in dates:
            pms_property = pms_property.with_context(
                checkin=item_date,
                checkout=item_date + timedelta(days=1),
                room_type_id=room_type_id,
                current_lines=avails_search_param.currentLines or False,
                pricelist_id=pricelist_id,
                real_avail=True,
            )
            result_avails.append(
                PmsAvailInfo(
                    date=datetime.combine(item_date, datetime.min.time()).isoformat(),
                    roomIds=pms_property.free_room_ids.ids,
                )
            )
        return result_avails
