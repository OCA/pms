# Copyright 2024 OsoTranquilo - José Luis Algara
# Copyright 2024 Irlui Ramírez
# From Consultores Hoteleros Integrales (ALDA Hotels) - 2024
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    tourist_rooms = fields.Integer(
        string="Tourist Rooms",
        help="Total Number of Registered Tourist Rooms (INE Listed)",
        store=True,
        readonly=True,
        compute="_compute_tourist_rooms",
    )

    property_rooms = fields.Integer(
        string="Total Rooms",
        help="Overall Count of Available Rooms in the Property",
        store=True,
        readonly=True,
        compute="_compute_property_rooms",
    )

    property_parkings = fields.Integer(
        string="Total Parkings",
        help="Total Number of Parking Spaces Available on the Property",
        store=True,
        readonly=True,
        compute="_compute_property_parkings",
    )

    property_halls = fields.Integer(
        string="Total Event Halls",
        help="Total Count of Event Halls and Meeting Rooms in the Property",
        store=True,
        readonly=True,
        compute="_compute_property_halls",
    )

    property_other_places = fields.Integer(
        string="Total Other Places",
        help="Total Count of Additional Facilities and Amenities on the Property",
        store=True,
        readonly=True,
        compute="_compute_other_places",
    )

    @api.depends("room_ids")
    def _compute_tourist_rooms(self):
        for record in self:
            tourist_rooms = len(record.room_ids.filtered(lambda r: r.in_ine))
            record.tourist_rooms = tourist_rooms

    @api.depends("room_ids")
    def _compute_property_rooms(self):
        for record in self:
            rooms = record.room_ids.filtered(
                lambda r: r.room_type_id.class_id.default_code in ["HAB", "APA"]
            )
            record.property_rooms = len(rooms)

    @api.depends("room_ids")
    def _compute_property_parkings(self):
        for record in self:
            rooms = record.room_ids.filtered(
                lambda r: r.room_type_id.class_id.default_code in ["PRK"]
            )
            record.property_parkings = len(rooms)

    @api.depends("room_ids")
    def _compute_property_halls(self):
        for record in self:
            rooms = record.room_ids.filtered(
                lambda r: r.room_type_id.class_id.default_code in ["SLA"]
            )
            record.property_halls = len(rooms)

    @api.depends("room_ids")
    def _compute_other_places(self):
        for record in self:
            rooms = record.room_ids.filtered(
                lambda r: r.room_type_id.class_id.default_code
                not in ["SLA", "PRK", "HAB", "APA"]
            )
            record.property_other_places = len(rooms)

    def init(self):
        properties = self.env["pms.property"].search([])
        for property in properties:
            property._compute_tourist_rooms()
            property._compute_property_rooms()
            property._compute_property_parkings()
            property._compute_property_halls()
            property._compute_other_places()
