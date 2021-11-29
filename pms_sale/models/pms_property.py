# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import datetime

from odoo import api, fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    checkin = fields.Float(string="Checkin")
    checkout = fields.Float(string="Checkout")
    reservation_ids = fields.One2many(
        "pms.property.reservation", "property_id", string="Reservation Types"
    )
    pms_mail_ids = fields.One2many("pms.mail", "property_id", string="Communication")
    no_of_guests = fields.Integer("Number of Guests")
    min_nights = fields.Integer("Minimum Nights")
    max_nights = fields.Integer("Maximum Nights")
    listing_type = fields.Selection(
        string="Listing Type",
        selection=[
            ("private_room", "Private Room"),
            ("entire_home", "Entire Home"),
            ("shared_room", "Shared Room"),
        ],
    )

    @api.model
    def get_property_information(self, vals, domain=False):
        domain = domain or []
        domain.append(("property_child_ids", "=", False))
        if vals.get("city_value") and vals.get("city_value") != "Select City":
            domain += [("city", "=", vals.get("city_value"))]
        if vals.get("bedrooms_value") and vals.get("bedrooms_value") != 0:
            domain += [("qty_bedroom", ">=", vals.get("bedrooms_value"))]
        if vals.get("datepicker_value"):
            date_range = vals.get("datepicker_value").split("-")
            start = date_range[0].strip() + " 00:00:00"
            end = date_range[1].strip() + " 23:59:59"
            start = datetime.strptime(start, "%m/%d/%Y %H:%M:%S")
            end = datetime.strptime(end, "%m/%d/%Y %H:%M:%S")
            reservation_ids = self.env["pms.reservation"].search(
                [
                    ("start", "<", end),
                    ("stop", ">", start),
                ]
            )
            property_ids = reservation_ids.mapped("property_id")
            # Remove all the properties with reservations in the date range to only
            # show the ones available
            domain += [("id", "not in", property_ids.ids)]
        return self.search_read(domain, ["ref", "name"])
