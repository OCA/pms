# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
import logging

import pytz

from odoo import _, fields, models

_log = logging.getLogger(__name__)


class WizCrmLeadNewReservation(models.TransientModel):
    _name = "wiz.crm.lead.new.reservation"
    _description = "New Reservation Wizard"

    crm_lead_id = fields.Many2one("crm.lead")
    check_in = fields.Date(required=True)
    check_out = fields.Date(required=True)
    price_list_id = fields.Many2one("product.pricelist", required=True)

    state = fields.Selection(
        [("new", _("New")), ("availability", _("Check Availability"))], default="new"
    )

    discount = fields.Float(string="Discount %")
    cleaning_fee_price = fields.Float(string="Cleaning Fee $")

    available_ids = fields.Many2many("crm.listing.availability")

    def action_cancel_soft_reset(self):
        self.write({"state": "new"})

        action = self.crm_lead_id.action_new_quotation_reservation()
        action["res_id"] = self.id
        return action

    def action_check_availability(self):
        guesty_listing_list = self.execute_availability_query()
        _search_props = self.env["pms.property"].search(
            [("guesty_id", "!=", False), ("guesty_id", "in", guesty_listing_list)]
        )

        calendar_result = self.env.company.guesty_backend_id.guesty_get_calendar_info(
            self.check_in, self.check_out, _search_props
        )

        calendar = [
            {"listing": key, "info": calendar_result[key]}
            for key in calendar_result
            if len(calendar_result[key]["status"]) == 1
            and "available" in calendar_result[key]["status"]
        ]

        calendar_ids = [a["listing"] for a in calendar]
        _search_props = self.env["pms.property"].search(
            [("guesty_id", "!=", False), ("guesty_id", "in", calendar_ids)]
        )

        self.env["crm.listing.availability"].sudo().search(
            [("crm_lead_id", "=", self.crm_lead_id.id)]
        ).unlink()

        no_nights = (self.check_out - self.check_in).days

        for _prop in _search_props:
            _product = (
                self.env.company.guesty_backend_id.reservation_product_id.with_context(
                    pricelist=self.price_list_id.id,
                    property_id=_prop,
                    reservation_start=self.check_in,
                    reservation_stop=self.check_out,
                    reservation_date=datetime.datetime.now(),
                )
            )

            # noinspection PyProtectedMember
            _product._compute_product_price()
            custom_price = _product.price

            self.env["crm.listing.availability"].sudo().create(
                {
                    "crm_lead_id": self.crm_lead_id.id,
                    "property_id": _prop.id,
                    "price": custom_price,
                    "currency": self.price_list_id.currency_id.name,
                    "no_nights": no_nights,
                    "total_price": no_nights * custom_price,
                }
            )

        self.write({"state": "availability"})
        action = self.crm_lead_id.action_new_quotation_reservation()
        action["res_id"] = self.id
        return action

    def execute_availability_query(self):
        query = """
        select count(*)     as no_states,
               t.listing_id,
               min(t.state) as first_state,
               max(t.state) as last_state
        from (
                 select calendar.listing_id, calendar.state
                 from pms_guesty_calendar calendar
                 where calendar.listing_date between %(check_in)s and %(check_out)s
                 group by calendar.listing_id, calendar.state
             ) as t
        group by t.listing_id
                """

        real_end_date = self.check_out - datetime.timedelta(days=1)
        data = {"check_in": self.check_in, "check_out": real_end_date}
        self.env.cr.execute(query, data)
        res = self.env.cr.dictfetchall()

        return [
            a["listing_id"]
            for a in res
            if a["no_states"] == 1
            and a["first_state"] == "available"
            and a["last_state"] == "available"
        ]

    def action_create_quotation(self):
        _log.info(self.available_ids)
        so_ids = []
        for _self in self.available_ids:
            backend = _self.env.company.guesty_backend_id
            reservation_product_id = backend.reservation_product_id

            if _self.property_id.reservation_ids:
                guesty_price_id = _self.property_id.reservation_ids.filtered(
                    lambda s: s.currency_id.id == backend.currency_id.id
                )
                utc = pytz.UTC
                tz = pytz.timezone(backend.timezone)
                ci = datetime.datetime.combine(
                    self.check_in, datetime.datetime.min.time()
                )
                ci = tz.localize(ci).astimezone(utc).replace(tzinfo=None)

                co = datetime.datetime.combine(
                    self.check_out, datetime.datetime.min.time()
                )
                co = tz.localize(co).astimezone(utc).replace(tzinfo=None)

                if reservation_product_id:
                    order_lines = [
                        (
                            0,
                            False,
                            {
                                "product_uom_qty": _self.no_nights,
                                "price_unit": _self.price,
                                "product_id": reservation_product_id.id,
                                "reservation_id": guesty_price_id.id,
                                "property_id": _self.property_id.id,
                                "start": ci,
                                "stop": co,
                                "discount": self.discount,
                            },
                        )
                    ]

                    if self.cleaning_fee_price > 0:
                        order_lines.append(
                            (
                                0,
                                False,
                                {
                                    "product_id": backend.cleaning_product_id.id,
                                    "name": backend.cleaning_product_id.name,
                                    "product_uom_qty": 1,
                                    "price_unit": self.cleaning_fee_price,
                                },
                            )
                        )

                    so = self.env["sale.order"].create(
                        {
                            "partner_id": _self.crm_lead_id.partner_id.id,
                            "opportunity_id": _self.crm_lead_id.id,
                            "pricelist_id": self.price_list_id.id,
                            "order_line": order_lines,
                        }
                    )

                    so_ids.append(so.id)

        return {
            "type": "ir.actions.act_window",
            "name": _("Quotations"),
            "res_model": "sale.order",
            "view_mode": "tree,form",
            "domain": [("id", "in", so_ids)],
        }


class CRMListingAvailability(models.Model):
    _name = "crm.listing.availability"
    _description = "Listing Availability"

    crm_lead_id = fields.Many2one("crm.lead")
    property_id = fields.Many2one("pms.property")

    # related
    city = fields.Char(related="property_id.city", store=True)
    country_id = fields.Many2one(
        "res.country", related="property_id.country_id", store=True
    )

    price = fields.Float()
    currency = fields.Char()
    no_nights = fields.Integer()
    total_price = fields.Float()
