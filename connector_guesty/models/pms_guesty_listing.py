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
    active = fields.Boolean(string="Active", default=True)
    external_id = fields.Char(string="External ID", required=True)
    guesty_account_id = fields.Char(string="Guesty Account ID", required=True)

    _sql_constraints = [
        ("unique_external_id", "unique(external_id)", "Listing already exists")
    ]

    def guesty_pull_listing(self, payload):
        _id = payload.get("_id")
        listing_id = self.search([("external_id", "=", _id)], limit=1)
        record_data = {
            "name": payload["nickname"],
            "title": payload["title"] if "title" in payload else payload["nickname"],
            "city": payload["address"]["city"]
            if "address" in payload and "city" in payload["address"]
            else None,
            "active": payload["active"],
            "guesty_account_id": payload["accountId"],
            "external_id": payload["_id"],
        }

        if not listing_id:
            self.sudo().create(record_data)
        else:
            listing_id.sudo().write(record_data)
