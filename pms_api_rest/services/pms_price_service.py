from datetime import datetime, timedelta

from odoo import _, fields
from odoo.exceptions import MissingError, ValidationError

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component

from ..pms_api_rest_utils import pms_api_check_access


class PmsPriceService(Component):
    _inherit = "base.rest.service"
    _name = "pms.price.service"
    _usage = "prices"
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
        input_param=Datamodel("pms.price.search.param"),
        output_param=Datamodel("pms.price.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_prices(self, prices_search_param):
        product = room_type = board_service_room_type = False

        if prices_search_param.roomTypeId:
            room_type = (
                self.env["pms.room.type"]
                .sudo()
                .search([("id", "=", prices_search_param.roomTypeId)])
            )
            pms_api_check_access(user=self.env.user, records=room_type)
        elif prices_search_param.productId:
            product = (
                self.env["product.product"]
                .sudo()
                .search([("id", "=", prices_search_param.productId)])
            )
            pms_api_check_access(user=self.env.user, records=product)
        elif (
            prices_search_param.boardServiceLineId
            and not prices_search_param.boardServiceId
        ):
            raise ValidationError(
                _("Mandatory board service id is missing for board service line")
            )
        elif prices_search_param.boardServiceId:
            if prices_search_param.isAdults and prices_search_param.isChildren:
                raise ValidationError(
                    _(
                        "It is not allowed to filter by adults and children simultaneously"
                    )
                )
            if (
                not prices_search_param.isAdults
                and not prices_search_param.isChildren
                and not prices_search_param.boardServiceLineId
            ):
                raise ValidationError(
                    _(
                        """
                    It is necessary to indicate whether
                    the board service is for adults or children.
                    """
                    )
                )
            board_service_room_type = (
                self.env["pms.board.service.room.type"]
                .sudo()
                .search([("id", "=", prices_search_param.boardServiceId)])
            )
            pms_api_check_access(user=self.env.user, records=board_service_room_type)
        else:
            raise MissingError(_("Wrong input param"))

        PmsPriceInfo = self.env.datamodels["pms.price.info"]
        result_prices = []
        date_from = fields.Date.from_string(prices_search_param.dateFrom)
        date_to = fields.Date.from_string(prices_search_param.dateTo)
        dates = [
            date_from + timedelta(days=x)
            for x in range(0, (date_to - date_from).days + 1)
        ]
        for price_date in dates:
            if board_service_room_type:
                result_prices.append(
                    PmsPriceInfo(
                        date=datetime.combine(
                            price_date, datetime.min.time()
                        ).isoformat(),
                        price=round(
                            self._get_board_service_price(
                                board_service=board_service_room_type,
                                board_type="adults"
                                if prices_search_param.isAdults
                                else "children",
                                pms_property_id=prices_search_param.pmsPropertyId,
                                pricelist_id=prices_search_param.pricelistId,
                                partner_id=prices_search_param.partnerId,
                                product_qty=prices_search_param.productQty,
                                date_consumption=price_date,
                                board_service_line_id=prices_search_param.boardServiceLineId
                                or False,
                            ),
                            2,
                        ),
                    )
                )
            else:
                result_prices.append(
                    PmsPriceInfo(
                        date=datetime.combine(
                            price_date, datetime.min.time()
                        ).isoformat(),
                        price=round(
                            self._get_product_price(
                                product=product if product else room_type.product_id,
                                pms_property_id=prices_search_param.pmsPropertyId,
                                pricelist_id=prices_search_param.pricelistId,
                                partner_id=prices_search_param.partnerId,
                                product_qty=prices_search_param.productQty,
                                date_consumption=price_date,
                            ),
                            2,
                        ),
                    )
                )
        return result_prices

    def _get_product_price(
        self,
        product,
        pms_property_id,
        pricelist_id=False,
        partner_id=False,
        product_qty=False,
        date_consumption=False,
        board_service_id=False,
        board_service_line_id=False,
    ):
        pms_property = self.env["pms.property"].sudo().browse(pms_property_id)
        pms_api_check_access(user=self.env.user, records=pms_property)
        product_context = dict(
            self.env.context,
            date=datetime.today().date(),
            pricelist=pricelist_id,
            uom=product.uom_id.id,
            fiscal_position=False,
            property=pms_property_id,
        )
        if date_consumption:
            product_context["consumption_date"] = date_consumption
        if board_service_line_id:
            product_context["board_service_line_id"] = board_service_line_id
        product = product.with_context(product_context)
        return self.env["account.tax"]._fix_tax_included_price_company(
            self.env["product.product"]
            .sudo()
            ._pms_get_display_price(
                pricelist_id=pricelist_id,
                product=product,
                company_id=pms_property.company_id.id,
                product_qty=product_qty or 1,
                partner_id=partner_id,
            ),
            product.taxes_id,
            product.taxes_id,  # Not exist service line, we repeat product taxes
            pms_property.company_id,
        )

    def _get_board_service_price(
        self,
        board_service,
        board_type,
        pms_property_id,
        pricelist_id=False,
        partner_id=False,
        product_qty=False,
        date_consumption=False,
        board_service_line_id=False,
    ):
        pms_property = self.env["pms.property"].sudo().browse(pms_property_id)
        pms_api_check_access(user=self.env.user, records=pms_property)
        price = 0
        if board_service_line_id:
            lines = (
                self.env["pms.board.service.room.type.line"]
                .sudo()
                .browse()
                .browse(board_service_line_id)
            )
        else:
            lines = board_service.board_service_line_ids.filtered(
                lambda line: line.adults if board_type == "adults" else line.children
            )
        for line in lines:
            price += self._get_product_price(
                product=line.product_id,
                pms_property_id=pms_property_id,
                pricelist_id=pricelist_id,
                partner_id=partner_id,
                product_qty=product_qty or 1,
                date_consumption=date_consumption,
                board_service_id=board_service.id,
                board_service_line_id=line.id,
            )
        return price
