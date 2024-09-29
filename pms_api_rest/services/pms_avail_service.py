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

    @restapi.method(
        [
            (
                [
                    "/bookia",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("bookia.avail.search.param"),
        output_param=Datamodel("bookia.avail.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_bookia_avails(self, bookia_avail_search):
        if not (
            bookia_avail_search.checkin
            and bookia_avail_search.checkout
            and bookia_avail_search.pmsPropertyId
            and bookia_avail_search.occupancy
        ):
            raise MissingError(
                _(
                    """Missing required parameters:
                    availabilityFrom, availabilityTo, pmsPropertyId"""
                )
            )
        pms_property = self.env["pms.property"].browse(
            bookia_avail_search.pmsPropertyId
        )
        checkin = fields.Date.from_string(bookia_avail_search.checkin)
        checkout = fields.Date.from_string(bookia_avail_search.checkout)
        pricelist = pms_property.default_pricelist_id
        PmsAvailInfo = self.env.datamodels["bookia.avail.info"]
        rooms = self.env["pms.room"].search(
            [
                ("pms_property_id", "=", pms_property.id),
                ("capacity", ">=", bookia_avail_search.occupancy),
            ]
        )
        room_types = rooms.mapped("room_type_id").filtered(lambda x: x.overnight_room)
        bookia_avails = []
        for room_type in room_types:
            pms_property = pms_property.with_context(
                checkin=checkin,
                checkout=checkout,
                room_type_id=room_type.id,
                pricelist_id=pricelist.id,
            )
            avail = pms_property.availability
            if not avail:
                continue
            product_context = dict(
                self.env.context,
                date=datetime.today().date(),
                pricelist=pricelist.id,
                uom=room_type.product_id.uom_id.id,
                fiscal_position=False,
                property=pms_property.id,
            )
            total_price = 0
            dates = [
                checkin + timedelta(days=x) for x in range(0, (checkout - checkin).days)
            ]
            for date in dates:
                product_context["consumption_date"] = date
                product = room_type.product_id.with_context(product_context)
                total_price += self.env["account.tax"]._fix_tax_included_price_company(
                    self.env["product.product"]._pms_get_display_price(
                        pricelist_id=pricelist.id,
                        product=product,
                        company_id=pms_property.company_id.id,
                        product_qty=1,
                        partner_id=False,
                    ),
                    room_type.product_id.taxes_id,
                    room_type.product_id.taxes_id,
                    pms_property.company_id,
                )
            bookia_avails.append(
                PmsAvailInfo(
                    roomTypeId=room_type.id,
                    roomTypeName=room_type.name,
                    avail=avail,
                    price=round(total_price, 2),
                )
            )
        return bookia_avails
