from datetime import datetime, timedelta

from odoo import _, fields
from odoo.exceptions import MissingError

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component

from ..pms_api_rest_utils import pms_api_check_access


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
        pms_property = (
            self.env["pms.property"].sudo().browse(avails_search_param.pmsPropertyId)
        )
        pms_api_check_access(user=self.env.user, records=pms_property)
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

    @restapi.method(
        [
            (
                [
                    "/count-free-rooms",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.avail.search.param"),
        output_param=Datamodel("pms.avail.info.room.type", is_list=True),
        auth="jwt_api_pms",
    )
    def get_count_free_rooms(self, avails_search_param):
        domain = []
        room_type_dict = {}
        if avails_search_param.pmsPropertyId:
            domain.append(("pms_property_id", "=", avails_search_param.pmsPropertyId))
        if (
            avails_search_param.availabilityFrom
            and avails_search_param.availabilityTo
            and avails_search_param.pmsPropertyId
        ):
            date_from = datetime.strptime(
                avails_search_param.availabilityFrom, "%Y-%m-%d"
            ).date()
            date_to = datetime.strptime(
                avails_search_param.availabilityTo, "%Y-%m-%d"
            ).date()
            pms_property = (
                self.env["pms.property"]
                .sudo()
                .browse(avails_search_param.pmsPropertyId)
            )
            pms_api_check_access(user=self.env.user, records=pms_property)
            room_types = pms_property.room_ids.mapped("room_type_id")
            for room_type in room_types:
                if avails_search_param.pricelistId:
                    apply_availability_rules = (
                        self.env.registry["ir.config_parameter"]
                        .sudo()
                        .get_param(
                            "apply_internal_availability_rules",
                            default=False,
                        )
                    )
                    pms_property = pms_property.with_context(
                        checkin=date_from,
                        checkout=date_to,
                        room_type_id=room_type.id,
                        pricelist_id=avails_search_param.pricelistId,
                        real_avail=False if apply_availability_rules else True,
                    )
                else:
                    pms_property = pms_property.with_context(
                        checkin=date_from,
                        checkout=date_to,
                        room_type_id=room_type.id,
                        real_avail=True,
                    )
                room_type_dict[room_type.id] = pms_property.availability

        result_rooms = []
        PmsAvailInfoRoomType = self.env.datamodels["pms.avail.info.room.type"]
        for room_type_id, count in room_type_dict.items():
            result_rooms.append(
                PmsAvailInfoRoomType(
                    roomTypeId=room_type_id,
                    count=count,
                )
            )
        return result_rooms
