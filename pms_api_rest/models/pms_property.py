import datetime
import json
import logging

import requests

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


class PmsProperty(models.Model):
    _inherit = "pms.property"

    color_option_config = fields.Selection(
        string="Color Option Configuration",
        help="Configuration of the color code for the planning.",
        selection=[("simple", "Simple"), ("advanced", "Advanced")],
        default="simple",
    )

    simple_out_color = fields.Char(
        string="Reservations Outside",
        help="Color for done reservations in the planning.",
        default="rgba(94,208,236)",
    )

    simple_in_color = fields.Char(
        string="Reservations Inside",
        help="Color for onboard and departure_delayed reservations in the planning.",
        default="rgba(0,146,183)",
    )

    simple_future_color = fields.Char(
        string="Future Reservations",
        help="Color for confirm, arrival_delayed and draft reservations in the planning.",
        default="rgba(1,182,227)",
    )

    pre_reservation_color = fields.Char(
        string="Pre-Reservation",
        help="Color for draft reservations in the planning.",
        default="rgba(162,70,128)",
    )

    confirmed_reservation_color = fields.Char(
        string="Confirmed Reservation",
        default="rgba(1,182,227)",
        help="Color for confirm reservations in the planning.",
    )

    paid_reservation_color = fields.Char(
        string="Paid Reservation",
        help="Color for done paid reservations in the planning.",
        default="rgba(126,126,126)",
    )

    on_board_reservation_color = fields.Char(
        string="Checkin",
        help="Color for onboard not paid reservations in the planning.",
        default="rgba(255,64,64)",
    )

    paid_checkin_reservation_color = fields.Char(
        string="Paid Checkin",
        help="Color for onboard paid reservations in the planning.",
        default="rgba(130,191,7)",
    )

    out_reservation_color = fields.Char(
        string="Checkout",
        help="Color for done not paid reservations in the planning.",
        default="rgba(88,77,118)",
    )

    staff_reservation_color = fields.Char(
        string="Staff",
        help="Color for staff reservations in the planning.",
        default="rgba(192,134,134)",
    )

    to_assign_reservation_color = fields.Char(
        string="OTA Reservation To Assign",
        help="Color for to_assign reservations in the planning.",
        default="rgba(237,114,46)",
    )

    pending_payment_reservation_color = fields.Char(
        string="Payment Pending",
        help="Color for pending payment reservations in the planning.",
        default="rgba(162,70,137)",
    )

    overpayment_reservation_color = fields.Char(
        string="Overpayment",
        help="Color for pending payment reservations in the planning.",
        default="rgba(4, 95, 118)",
    )

    hotel_image_pms_api_rest = fields.Image(
        string="Hotel image",
        store=True,
    )

    ota_property_settings_ids = fields.One2many(
        string="OTA Property Settings",
        help="OTA Property Settings",
        comodel_name="ota.property.settings",
        inverse_name="pms_property_id",
    )

    ocr_checkin_supplier = fields.Selection(
        string="OCR Checkin Supplier",
        help="Select ocr supplier for checkin documents",
        selection=[],
    )

    # PUSH API NOTIFICATIONS
    def get_payload_avail(self, avails, client):
        self.ensure_one()
        endpoint = client.url_endpoint_availability
        pms_property_id = self.id
        avails_dict = {"pmsPropertyId": pms_property_id, "avails": []}
        room_type_ids = avails.mapped("room_type_id.id")
        property_client_conf = self.env["ota.property.settings"].search(
            [
                ("pms_property_id", "=", self.id),
                ("agency_id", "=", client.partner_id.id),
            ]
        )
        plan_avail = property_client_conf.main_avail_plan_id
        for room_type_id in room_type_ids:
            room_type_avails = sorted(
                avails.filtered(lambda r: r.room_type_id.id == room_type_id),
                key=lambda r: r.date,
            )
            avail_room_type_index = {}
            for record_avail in room_type_avails:
                avail_rule = record_avail.avail_rule_ids.filtered(
                    lambda r: r.availability_plan_id == plan_avail
                )
                if avail_rule:
                    avail = avail_rule.plan_avail
                else:
                    room_type = avail_rule.room_type_id
                    avail = min(
                        [
                            record_avail.real_avail,
                            room_type.default_max_avail
                            if room_type.default_max_avail >= 0
                            else record_avail.real_avail,
                            room_type.default_quota
                            if room_type.default_quota >= 0
                            else record_avail.real_avail,
                        ]
                    )
                previus_date = record_avail.date - datetime.timedelta(days=1)
                avail_index = avail_room_type_index.get(previus_date)
                if avail_index and avail_index["avail"] == avail:
                    avail_room_type_index[record_avail.date] = {
                        "date_from": avail_index["date_from"],
                        "date_to": datetime.datetime.strftime(
                            record_avail.date, "%Y-%m-%d"
                        ),
                        "roomTypeId": room_type_id,
                        "avail": avail,
                    }
                    avail_room_type_index.pop(previus_date)
                else:
                    avail_room_type_index[record_avail.date] = {
                        "date_from": datetime.datetime.strftime(
                            record_avail.date, "%Y-%m-%d"
                        ),
                        "date_to": datetime.datetime.strftime(
                            record_avail.date, "%Y-%m-%d"
                        ),
                        "roomTypeId": room_type_id,
                        "avail": avail,
                    }
            avails_dict["avails"].extend(avail_room_type_index.values())
        return avails_dict, endpoint

    def get_payload_prices(self, prices, client):
        self.ensure_one()
        endpoint = client.url_endpoint_prices
        pms_property_id = self.id
        prices_dict = {"pmsPropertyId": pms_property_id, "prices": []}
        product_ids = prices.mapped("product_id.id")
        for product_id in product_ids:
            room_type_id = (
                self.env["pms.room.type"].search([("product_id", "=", product_id)]).id
            )
            product_prices = sorted(
                prices.filtered(lambda r: r.product_id.id == product_id),
                key=lambda r: r.date_end_consumption,
            )
            price_product_index = {}
            for price in product_prices:
                previus_date = price.date_end_consumption - datetime.timedelta(days=1)
                price_index = price_product_index.get(previus_date)
                if price_index and round(price_index["price"], 2) == round(
                    price.fixed_price, 2
                ):
                    price_product_index[price.date_end_consumption] = {
                        "date_from": price_index["date_from"],
                        "date_to": datetime.datetime.strftime(
                            price.date_end_consumption, "%Y-%m-%d"
                        ),
                        "roomTypeId": room_type_id,
                        "price": price.fixed_price,
                    }
                    price_product_index.pop(previus_date)
                else:
                    price_product_index[price.date_end_consumption] = {
                        "date_from": datetime.datetime.strftime(
                            price.date_end_consumption, "%Y-%m-%d"
                        ),
                        "date_to": datetime.datetime.strftime(
                            price.date_end_consumption, "%Y-%m-%d"
                        ),
                        "roomTypeId": room_type_id,
                        "price": price.fixed_price,
                    }
            prices_dict["prices"].extend(price_product_index.values())
        return prices_dict, endpoint

    def get_payload_rules(self, rules, client):
        self.ensure_one()
        endpoint = client.url_endpoint_rules
        pms_property_id = self.id
        rules_dict = {"pmsPropertyId": pms_property_id, "rules": []}
        room_type_ids = rules.mapped("room_type_id.id")
        for room_type_id in room_type_ids:
            room_type_rules = sorted(
                rules.filtered(lambda r: r.room_type_id.id == room_type_id),
                key=lambda r: r.date,
            )
            rules_room_type_index = {}
            for rule in room_type_rules:
                previus_date = rule.date - datetime.timedelta(days=1)
                avail_index = rules_room_type_index.get(previus_date)
                if (
                    avail_index
                    and avail_index["min_stay"] == rule.min_stay
                    and avail_index["max_stay"] == rule.max_stay
                    and avail_index["closed"] == rule.closed
                    and avail_index["closed_arrival"] == rule.closed_arrival
                    and avail_index["closed_departure"] == rule.closed_departure
                ):
                    rules_room_type_index[rule.date] = {
                        "date_from": avail_index["date_from"],
                        "date_to": datetime.datetime.strftime(rule.date, "%Y-%m-%d"),
                        "roomTypeId": room_type_id,
                        "min_stay": rule.min_stay,
                        "max_stay": rule.max_stay,
                        "closed": rule.closed,
                        "closed_arrival": rule.closed_arrival,
                        "closed_departure": rule.closed_departure,
                    }
                    rules_room_type_index.pop(previus_date)
                else:
                    rules_room_type_index[rule.date] = {
                        "date_from": datetime.datetime.strftime(rule.date, "%Y-%m-%d"),
                        "date_to": datetime.datetime.strftime(rule.date, "%Y-%m-%d"),
                        "roomTypeId": room_type_id,
                        "min_stay": rule.min_stay,
                        "max_stay": rule.max_stay,
                        "closed": rule.closed,
                        "closed_arrival": rule.closed_arrival,
                        "closed_departure": rule.closed_departure,
                    }
            rules_dict["rules"].extend(rules_room_type_index.values())
        return rules_dict, endpoint

    def pms_api_push_payload(self, payload, endpoint, client):
        token = client.external_public_token
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "accept": "text/json",
        }
        response = requests.post(endpoint, headers=headers, data=json.dumps(payload))
        return response

    def generate_availability_json(
        self, date_from, date_to, pms_property_id, room_type_id, client
    ):
        avail_records = self.env["pms.availability"].search(
            [
                ("date", ">=", date_from),
                ("date", "<=", date_to),
                ("pms_property_id", "=", pms_property_id),
                ("room_type_id", "=", room_type_id),
            ],
            order="date",
        )
        avail_data = []
        current_avail = None
        current_date_from = None
        current_date_to = None
        all_dates = [
            date_from + datetime.timedelta(days=x)
            for x in range((date_to - date_from).days + 1)
        ]
        property_client_conf = self.env["ota.property.settings"].search(
            [
                ("pms_property_id", "=", pms_property_id),
                ("agency_id", "=", client.partner_id.id),
            ]
        )
        plan_avail = property_client_conf.main_avail_plan_id
        for date in all_dates:
            avail_record = avail_records.filtered(lambda r: r.date == date)
            if avail_record:
                avail_rule = avail_record.avail_rule_ids.filtered(
                    lambda r: r.availability_plan_id == plan_avail
                )
                if avail_rule:
                    avail = avail_rule.plan_avail
                else:
                    room_type = avail_rule.room_type_id
                    avail = min(
                        [
                            avail_record.real_avail,
                            room_type.default_max_avail
                            if room_type.default_max_avail >= 0
                            else avail_record.real_avail,
                            room_type.default_quota
                            if room_type.default_quota >= 0
                            else avail_record.real_avail,
                        ]
                    )
            else:
                room_type = self.env["pms.room.type"].browse(room_type_id)
                avail = min(
                    [
                        len(
                            room_type.room_ids.filtered(
                                lambda r: r.active
                                and r.pms_property_id.id == pms_property_id
                            )
                        ),
                        room_type.default_max_avail
                        if room_type.default_max_avail >= 0
                        else avail_record.real_avail,
                        room_type.default_quota
                        if room_type.default_quota >= 0
                        else avail_record.real_avail,
                    ]
                )
            if current_avail is None:
                current_avail = avail
                current_date_from = date
                current_date_to = date
            elif current_avail == avail:
                current_date_to = date
            else:
                avail_data.append(
                    {
                        "date_from": datetime.datetime.strftime(
                            current_date_from, "%Y-%m-%d"
                        ),
                        "date_to": datetime.datetime.strftime(
                            current_date_to, "%Y-%m-%d"
                        ),
                        "roomTypeId": room_type_id,
                        "avail": current_avail,
                    }
                )
                current_avail = avail
                current_date_from = date
                current_date_to = date
        if current_avail is not None:
            avail_data.append(
                {
                    "date_from": datetime.datetime.strftime(
                        current_date_from, "%Y-%m-%d"
                    ),
                    "date_to": datetime.datetime.strftime(current_date_to, "%Y-%m-%d"),
                    "roomTypeId": room_type_id,
                    "avail": current_avail,
                }
            )
        return avail_data

    def generate_restrictions_json(
        self, date_from, date_to, pms_property_id, room_type_id, client
    ):
        """
        Group by range of dates with the same restrictions
        Output format:
        rules_data: [
                {
                    'date_from': '2023-08-01',
                    'date_to': '2023-08-30',
                    'roomTypeId': 2,
                    'min_stay': 2,
                    'max_stay': 6,
                    'closed': false,
                    'closed_arrival': false,
                    'closed_departure': false
                }
            ]
        """
        property_client_conf = self.env["ota.property.settings"].search(
            [
                ("pms_property_id", "=", pms_property_id),
                ("agency_id", "=", client.partner_id.id),
            ]
        )
        rules_records = self.env["pms.availability.plan.rule"].search(
            [
                ("date", ">=", date_from),
                ("date", "<=", date_to),
                ("pms_property_id", "=", pms_property_id),
                ("room_type_id", "=", room_type_id),
                (
                    "availability_plan_id",
                    "=",
                    property_client_conf.main_avail_plan_id.id,
                ),
            ],
            order="date",
        )
        rules_data = []
        current_rule = None
        current_date_from = None
        current_date_to = None
        all_dates = [
            date_from + datetime.timedelta(days=x)
            for x in range((date_to - date_from).days + 1)
        ]
        for date in all_dates:
            rules_record = rules_records.filtered(lambda r: r.date == date)
            if rules_record:
                rule = rules_record[0]
            else:
                rule = None
            if current_rule is None:
                current_rule = rule
                current_date_from = date
                current_date_to = date
            elif (
                rule
                and current_rule.min_stay == rule.min_stay
                and current_rule.max_stay == rule.max_stay
                and current_rule.closed == rule.closed
                and current_rule.closed_arrival == rule.closed_arrival
                and current_rule.closed_departure == rule.closed_departure
            ):
                current_date_to = date
            else:
                if current_rule:
                    rules_data.append(
                        {
                            "date_from": datetime.datetime.strftime(
                                current_date_from, "%Y-%m-%d"
                            ),
                            "date_to": datetime.datetime.strftime(
                                current_date_to, "%Y-%m-%d"
                            ),
                            "roomTypeId": room_type_id,
                            "min_stay": current_rule.min_stay,
                            "max_stay": current_rule.max_stay,
                            "closed": current_rule.closed,
                            "closed_arrival": current_rule.closed_arrival,
                            "closed_departure": current_rule.closed_departure,
                        }
                    )
                current_rule = rule
                current_date_from = date
                current_date_to = date
        return rules_data

    def generate_prices_json(
        self, date_from, date_to, pms_property_id, room_type_id, client
    ):
        """
        prices: [
            {
                'date_from': '2023-07-02',
                'date_to': '2023-07-05',
                'roomTypeId': 2,
                'price': 50
            }
        ]
        """
        all_dates = [
            date_from + datetime.timedelta(days=x)
            for x in range((date_to - date_from).days + 1)
        ]
        product = self.env["pms.room.type"].browse(room_type_id).product_id
        property_client_conf = self.env["ota.property.settings"].search(
            [
                ("pms_property_id", "=", pms_property_id),
                ("agency_id", "=", client.partner_id.id),
            ]
        )
        pms_property = self.env["pms.property"].browse(pms_property_id)
        pricelist = property_client_conf.main_pricelist_id
        product_context = dict(
            self.env.context,
            date=datetime.datetime.today().date(),
            pricelist=3,  # self.get_default_pricelist(),
            uom=product.uom_id.id,
            fiscal_position=False,
            property=pms_property_id,
        )
        prices_data = []
        current_price = None
        current_date_from = None
        current_date_to = None
        for index, date in enumerate(all_dates):
            product_context["consumption_date"] = date
            product = product.with_context(product_context)
            price = round(
                self.env["account.tax"]._fix_tax_included_price_company(
                    self.env["product.product"]._pms_get_display_price(
                        pricelist_id=pricelist.id,
                        product=product,
                        company_id=pms_property.company_id.id,
                        product_qty=1,
                        partner_id=False,
                    ),
                    product.taxes_id,
                    product.taxes_id,
                    pms_property.company_id,
                ),
                2,
            )
            if current_price is None:
                current_price = price
                current_date_from = date
                current_date_to = date
            elif current_price == price and index < len(all_dates) - 1:
                current_date_to = date
            else:
                prices_data.append(
                    {
                        "date_from": datetime.datetime.strftime(
                            current_date_from, "%Y-%m-%d"
                        ),
                        "date_to": datetime.datetime.strftime(
                            current_date_to, "%Y-%m-%d"
                        ),
                        "roomTypeId": room_type_id,
                        "price": current_price,
                    }
                )
                current_price = price
                current_date_from = date
                current_date_to = date
        if current_price is not None:
            prices_data.append(
                {
                    "date_from": datetime.datetime.strftime(
                        current_date_from, "%Y-%m-%d"
                    ),
                    "date_to": datetime.datetime.strftime(current_date_to, "%Y-%m-%d"),
                    "roomTypeId": room_type_id,
                    "price": current_price,
                }
            )
        return prices_data

    @api.model
    def pms_api_push_batch(
        self,
        call_type,
        date_from=lambda: datetime.datetime.today().date(),
        date_to=lambda: datetime.datetime.today().date() + datetime.timedelta(days=365),
        filter_room_type_id=False,
        pms_property_codes=False,
        client=False,
    ):
        if client:
            clients = client
        else:
            clients = self.env["res.users"].search([("pms_api_client", "=", True)])
        room_type_ids = []
        endpoint = ""
        response = None
        _logger.info("PMS API push batch")
        if isinstance(date_from, str):
            date_from = datetime.datetime.strptime(date_from, "%Y-%m-%d").date()
            if date_from < datetime.datetime.today().date():
                date_from = datetime.datetime.today().date()
        if isinstance(date_to, str):
            date_to = datetime.datetime.strptime(date_to, "%Y-%m-%d").date()
            if date_to <= date_from:
                date_to = date_from
        for client in clients:
            if not pms_property_codes:
                pms_properties = client.pms_property_ids
            else:
                pms_properties = self.env["pms.property"].search(
                    [
                        ("pms_property_code", "in", pms_property_codes),
                        ("id", "in", client.pms_property_ids.ids),
                    ]
                )
            for pms_property in pms_properties:
                try:
                    property_client_conf = (
                        self.env["ota.property.settings"]
                        .sudo()
                        .search(
                            [
                                ("pms_property_id", "=", pms_property.id),
                                ("agency_id", "=", client.partner_id.id),
                            ]
                        )
                    )
                    pms_property_id = pms_property.id
                    room_type_ids = (
                        [filter_room_type_id]
                        if filter_room_type_id
                        else self.env["pms.room"]
                        .search([("pms_property_id", "=", pms_property_id)])
                        .mapped("room_type_id")
                        .filtered(
                            lambda r: r.id
                            not in property_client_conf.excluded_room_type_ids.ids
                        )
                        .ids
                    )
                    payload = {
                        "pmsPropertyId": pms_property_id,
                    }
                    data = []
                    for room_type_id in room_type_ids:
                        if call_type == "availability":
                            endpoint = client.url_endpoint_availability
                            data.extend(
                                pms_property.generate_availability_json(
                                    date_from=date_from,
                                    date_to=date_to,
                                    pms_property_id=pms_property_id,
                                    room_type_id=room_type_id,
                                    client=client,
                                )
                            )
                            key_data = "avails"
                        elif call_type == "restrictions":
                            endpoint = client.url_endpoint_rules
                            data.extend(
                                pms_property.generate_restrictions_json(
                                    date_from=date_from,
                                    date_to=date_to,
                                    pms_property_id=pms_property_id,
                                    room_type_id=room_type_id,
                                    client=client,
                                )
                            )
                            key_data = "rules"
                        elif call_type == "prices":
                            endpoint = client.url_endpoint_prices
                            data.extend(
                                pms_property.generate_prices_json(
                                    date_from=date_from,
                                    date_to=date_to,
                                    pms_property_id=pms_property_id,
                                    room_type_id=room_type_id,
                                    client=client,
                                )
                            )
                            key_data = "prices"
                        else:
                            raise ValidationError(_("Invalid call type"))
                    if data:
                        payload[key_data] = data
                        response = self.pms_api_push_payload(payload, endpoint, client)
                        _logger.info(
                            f"""PMS API push batch response to
                            {endpoint}: {response.status_code} - {response.text}"""
                        )
                    self.invalidate_cache()
                    self.env["pms.api.log"].sudo().create(
                        {
                            "pms_property_id": pms_property_id,
                            "client_id": client.id,
                            "request": payload,
                            "response": str(response),
                            "status": "success" if response.ok else "error",
                            "request_date": fields.Datetime.now(),
                            "method": "PUSH",
                            "endpoint": endpoint,
                            "target_date_from": date_from,
                            "target_date_to": date_to,
                            "request_type": call_type,
                            "room_type_ids": room_type_ids,
                        }
                    )
                except Exception as e:
                    _logger.error(f"""PMS API push batch error: {e}""")
                    self.env["pms.api.log"].sudo().create(
                        {
                            "pms_property_id": pms_property_id,
                            "client_id": client.id,
                            "request": payload,
                            "response": str(e),
                            "status": "error",
                            "request_date": fields.Datetime.now(),
                            "method": "PUSH",
                            "endpoint": endpoint,
                            "target_date_from": date_from,
                            "target_date_to": date_to,
                            "request_type": call_type,
                            "room_type_ids": room_type_ids,
                        }
                    )
