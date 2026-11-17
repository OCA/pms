# Copyright (c) 2021 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import datetime, time

from odoo import api, fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    checkin = fields.Float()
    checkout = fields.Float()
    reservation_ids = fields.One2many(
        "pms.property.reservation", "property_id", string="Reservation Types"
    )
    pms_mail_ids = fields.One2many("pms.mail", "property_id", string="Communication")
    no_of_guests = fields.Integer("Number of Guests")
    min_nights = fields.Integer("Minimum Nights")
    max_nights = fields.Integer("Maximum Nights")
    listing_type = fields.Selection(
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
        if vals.get("city_value"):
            domain += [("city", "=", vals.get("city_value"))]
        if vals.get("bedrooms_value"):
            domain += [("qty_bedroom", ">=", int(vals.get("bedrooms_value")))]
        date_from = fields.Date.to_date(vals.get("date_from"))
        date_to = fields.Date.to_date(vals.get("date_to"))
        if date_from or date_to:
            # A single date means "available on that day"
            date_from = date_from or date_to
            date_to = date_to or date_from
            reservation_ids = self.env["pms.reservation"].search(
                [
                    ("start", "<", datetime.combine(date_to, time.max)),
                    ("stop", ">", datetime.combine(date_from, time.min)),
                ]
            )
            # Remove all the properties with reservations in the date range to only
            # show the ones available
            domain += [("id", "not in", reservation_ids.property_id.ids)]
        return self.search_read(domain, ["ref", "name"])
