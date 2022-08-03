# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import fields, models

_log = logging.getLogger(__name__)


class PmsGuestyListing(models.Model):
    _name = "pms.guesty.listing"
    _description = "Guesty Listing"

    name = fields.Char(string="Name", required=True)
    title = fields.Char(string="Title", required=True)
    city = fields.Char(string="City", required=False)

    bedrooms = fields.Integer(string="Num Bedrooms")
    bathrooms = fields.Integer(string="Num Bathrooms")
    timezone = fields.Char(string="Timezone")

    active = fields.Boolean(string="Active", default=True)
    external_id = fields.Char(string="External ID", required=True)
    guesty_account_id = fields.Char(string="Guesty Account ID", required=True)
    json_data = fields.Text()

    _sql_constraints = [
        ("unique_external_id", "unique(external_id)", "Listing already exists")
    ]

    def guesty_pull_listing(self, payload):
        _id = payload.get("_id")
        listing_id = self.search(
            [("external_id", "=", _id), ("active", "in", [True, False])], limit=1
        )

        city = None
        if "address" in payload:
            if "city" in payload["address"]:
                city = payload["address"]["city"]

        record_data = {
            "name": payload["nickname"],
            "title": payload["title"] if "title" in payload else payload["nickname"],
            "city": city,
            "active": payload["active"],
            "bathrooms": payload.get("bathrooms", 0),
            "bedrooms": payload.get("bedrooms", 0),
            "timezone": payload.get("timezone"),
            "guesty_account_id": payload["accountId"],
            "external_id": payload["_id"],
            "json_data": payload,
        }

        if not listing_id:
            self.sudo().create(record_data)
        else:
            listing_id.sudo().write(record_data)

    def create_pms_property(self):
        pms_property = (
            self.env["pms.property"]
            .sudo()
            .search([("guesty_id", "=", self.external_id)])
        )

        payload = {
            "name": self.title,
            "ref": self.name,
            "tz": self.timezone,
            "guesty_id": self.external_id,
            "owner_id": 1,  # fix to the correct one
            "guesty_listing_ids": [(4, self.id)],
        }

        if not pms_property:
            pms_property = self.env["pms.property"].sudo().create(payload)
        else:
            pms_property.write(payload)

        return pms_property
