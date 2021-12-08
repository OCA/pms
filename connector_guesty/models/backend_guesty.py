# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
import json
import logging

import requests

from odoo import _, fields, models
from odoo.exceptions import UserError, ValidationError

_log = logging.getLogger(__name__)


class BackendGuesty(models.Model):
    _name = "backend.guesty"
    _description = "Guesty Backend"

    name = fields.Char(required=True)
    api_key = fields.Char(required=True)
    api_secret = fields.Char(required=True)
    api_url = fields.Char(required=True)
    reservation_pull_start_date = fields.Datetime()

    cleaning_product_id = fields.Many2one("product.product")
    extra_product_id = fields.Many2one("product.product")

    def check_credentials(self):
        # url to validate the credentials
        # this endpoint will search a list of users, it may be empty if the api key
        # does not have permissions to list the users, but it should be a 200 response
        # Note: Guesty does not provide a way to validate credentials
        success, result = self.call_get_request("search", limit=1)
        if success:
            raise UserError(
                _("Connection Test Succeeded! Everything seems properly set up!")
            )
        else:
            raise UserError(_("Connection Test Failed!"))

    def action_test_guest(self):
        self.guesty_search_customer("61ba45ea91a58a00328beca4")

    def guesty_search_create_customer(self, partner):
        guesty_partner = self.env["res.partner.guesty"].search(
            [("partner_id", "=", partner.id)], limit=1
        )
        if not guesty_partner:
            # create on guesty
            body = {
                "fullName": partner.name,
                "email": partner.email,
                "phone": partner.phone,
            }
            success, res = self.call_post_request(url_path="guests", body=body)

            if not success:
                raise UserError(_("Unable to create customer"))

            guesty_id = res.get("_id")
            customer = self.env["res.partner.guesty"].create(
                {"partner_id": partner.id, "guesty_id": guesty_id}
            )

            return customer
        else:
            return guesty_partner

    def guesty_search_pull_customer(self, guesty_id):
        """
        Method to search a guesty customer into odoo
        Docs: https://docs.guesty.com/#retrieve-a-guest
        :param str guesty_id: Guesty customer ID
        :return models.Model(res.partner.guesty):
        """
        # search for a guesty customer in the odoo database into the res.partner.guesty
        # model if we don't found them, we request to get the customer data from guesty
        # and store it into odoo
        if guesty_id is None:
            return

        guesty_partner = self.env["res.partner.guesty"].search(
            [("guesty_id", "=", guesty_id)], limit=1
        )
        if not guesty_partner:
            # get data from guesty
            success, res = self.call_get_request(url_path="guests/{}".format(guesty_id))

            if not success:
                raise UserError(_("Failed to get customer data from guesty"))

            customer_name = res.get("fullName")
            if not customer_name:
                customer_name = res.get("firstName")
                if customer_name and res.get("lastName"):
                    customer_name = "{} {}".format(customer_name, res.get("lastName"))

            if not customer_name:
                customer_name = "Anonymous Customer"

            body_payload = {
                "name": customer_name,
                "email": res.get("email"),
                "phone": res.get("phone"),
            }

            hometown = res.get("hometown")
            if hometown:
                home_town_split = hometown.split(", ")
                if len(home_town_split) >= 2:
                    city, country_name = home_town_split[0:2]
                    country = self.env["res.country"].search(
                        [("name", "=", country_name)], limit=1
                    )
                    body_payload["country_id"] = country.id
                else:
                    city = hometown
                body_payload["city"] = city

            if "city" not in body_payload:
                body_payload["city"] = "ND"

            if "country_id" not in body_payload:
                body_payload["country_id"] = self.env.ref(
                    "base.mx", raise_if_not_found=False
                ).id

            base_partner = self.env["res.partner"].create(body_payload)

            customer = self.env["res.partner.guesty"].create(
                {"partner_id": base_partner.id, "guesty_id": guesty_id}
            )

            return customer
        else:
            return guesty_partner

    def download_reservations(self):
        """
        Method to download reservations from guesty
        Docs: https://docs.guesty.com/#search-reservations
        :return:
        """
        reservation_status = [
            "inquiry",
            "declined",
            "expired",
            "canceled",
            "closed",
            "reserved",
            "confirmed",
            "checked_in",
            "checked_out",
            "awaiting_payment",
        ]
        filters = [{"field": "status", "operator": "$in", "value": reservation_status}]
        if self.reservation_pull_start_date:
            filters.append(
                {
                    "field": "lastUpdatedAt",
                    "operator": "$gte",
                    "value": self.reservation_pull_start_date.strftime(
                        "%Y-%m-%dT%H:%M:%S"
                    ),
                }
            )

        params = {
            "filters": json.dumps(filters),
            "sort": "lastUpdatedAt",
            "fields": " ".join(
                [
                    "status",
                    "checkIn",
                    "checkOut",
                    "listingId",
                    "guestId",
                    "listing.nickname",
                    "lastUpdatedAt",
                    "money",
                    "nightsCount",
                ]
            ),
        }

        success, res = self.call_get_request(url_path="reservations", params=params)

        if not success:
            _log.error(res.content)
            raise ValidationError(_("Unable to sync data"))

        records = res.get("results", [])
        reservation_last_date = None
        for reservation in records:
            self.env["pms.reservation"].with_delay().guesty_pull_reservation(
                self, reservation
            )
            _reservation_update_date = reservation.get("lastUpdatedAt")
            if _reservation_update_date:
                _reservation_update_date = _reservation_update_date[0:19]
                _reservation_update_date = datetime.datetime.strptime(
                    _reservation_update_date, "%Y-%m-%dT%H:%M:%S"
                )
                if (
                    not reservation_last_date
                    or _reservation_update_date > reservation_last_date
                ):
                    reservation_last_date = _reservation_update_date

        if reservation_last_date:
            self.reservation_pull_start_date = reservation_last_date

    def download_calendars(self):
        properties = self.env["pms.property"].search([("guesty_id", "!=", False)])
        for property_id in properties:
            self.env["pms.guesty.calendar"].with_delay().guesty_pull_calendar(
                self, property_id, "2021-12-01", "2022-12-31"
            )

    def call_get_request(
        self, url_path, params=None, skip=0, limit=25, success_codes=None
    ):
        if success_codes is None:
            success_codes = [200, 201]

        if params is None:
            params = {}

        params.update({"skip": str(skip), "limit": str(limit)})

        url = "{}/{}".format(self.api_url, url_path)
        result = requests.get(
            url=url, params=params, auth=(self.api_key, self.api_secret)
        )

        if result.status_code in success_codes:
            return True, result.json()

        _log.error(result.content)
        return False, None

    def call_post_request(self, url_path, body):
        url = "{}/{}".format(self.api_url, url_path)
        result = requests.post(url=url, json=body, auth=(self.api_key, self.api_secret))

        if result.status_code == 200:
            return True, result.json()
        else:
            _log.error(result.content)
            return False, None

    def call_put_request(self, url_path, body):
        url = "{}/{}".format(self.api_url, url_path)
        result = requests.put(url=url, json=body, auth=(self.api_key, self.api_secret))

        if result.status_code == 200:
            if result.content.decode("utf-8") == "ok":
                return True, result.content.decode("utf-8")
            else:
                return True, result.json()
        else:
            _log.error(result.content)
            return False, None

    def download_properties(self):
        property_ids = self.env["pms.property"].sudo().search([])

        skip = 0
        while True:
            success, res = self.call_get_request(
                url_path="listings",
                params={"city": "Ciudad de México"},
                limit=100,
                skip=skip,
            )

            skip += 100

            if success:
                result = res.get("results", [])
                for record in result:
                    property_id = property_ids.filtered(
                        lambda s: s.ref == record.get("nickname")
                    )
                    if property_id and len(property_id) == 1:
                        property_id.write(
                            {
                                "guesty_id": record.get("_id"),
                                "name": "{} / {}".format(
                                    record.get("nickname"), record.get("title")
                                ),
                            }
                        )
                    else:
                        _log.info("Not found: {}".format(record.get("nickname")))

                if len(result) == 0:
                    break
            else:
                break
