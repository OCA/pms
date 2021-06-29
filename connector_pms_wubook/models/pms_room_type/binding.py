# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import random

from odoo import api, fields, models


class ChannelWubookPmsRoomTypeBinding(models.Model):
    _name = "channel.wubook.pms.room.type"
    _inherit = "channel.wubook.binding"
    _inherits = {"pms.room.type": "odoo_id"}

    # binding fields
    odoo_id = fields.Many2one(
        comodel_name="pms.room.type",
        string="Odoo ID",
        required=True,
        ondelete="cascade",
    )

    total_rooms_count = fields.Integer(
        string="Total Rooms Count",
        help="The number of rooms in a room type",
        compute="_compute_total_rooms_count",
        store=True,
    )

    @api.depends("room_ids", "room_ids.active", "room_ids.pms_property_id")
    def _compute_total_rooms_count(self):
        for record in self:
            record.total_rooms_count = len(
                record.room_ids.filtered(
                    lambda x: x.pms_property_id == self.backend_id.pms_property_id
                )
            )

    default_quota = fields.Integer(
        string="Default Quota",
        help="Quota assigned to the channel given no availability rules. "
        "Use `-1` for managing no quota.",
        required=True,
        default=-1,
    )
    default_max_avail = fields.Integer(
        string="Default Max. Availability",
        compute="_compute_default_max_avail",
        required=False,
        readonly=False,
        store=True,
        help="Maximum simultaneous availability given no availability rules. "
        "Use `-1` for using maximum simultaneous availability.",
    )

    @api.depends("total_rooms_count")
    def _compute_default_max_avail(self):
        for rec in self:
            if rec.default_max_avail > rec.total_rooms_count:
                rec.default_max_avail = rec.total_rooms_count or -1

    default_availability = fields.Integer(
        string="Default Availability",
        compute="_compute_default_availability",
        inverse="_inverse_default_availability",
        required=True,
        readonly=False,
        store=True,
        help="Default availability for OTAs. "
        "The availability is calculated based on the quota, "
        "the maximum simultaneous availability and "
        "the total room count for the given room type.",
    )

    @api.depends("default_quota", "default_max_avail", "total_rooms_count")
    def _compute_default_availability(self):
        for rec in self:
            rec.default_availability = min(
                filter(
                    lambda x: x != -1,
                    [rec.default_quota, rec.default_max_avail, rec.total_rooms_count],
                )
            )

    def _inverse_default_availability(self):
        for rec in self:
            diff_rooms = rec.default_availability - rec.total_rooms_count
            if diff_rooms < 0 or rec.default_availability == 0:
                rec.default_max_avail = rec.default_availability
            elif diff_rooms > 0:
                rec.default_max_avail = -1
                rec.default_quota = -1
                rec.room_ids = [
                    (
                        0,
                        0,
                        {
                            "name": "TEMP-%s"
                            % format(random.randint(0, 0xFFFFFFFF), "x"),
                            "pms_property_id": rec.backend_record.pms_property_id.id,
                            "capacity": rec.occupancy,
                        },
                    )
                    for _ in range(diff_rooms)
                ]
            else:
                rec.default_max_avail = -1
                rec.default_quota = -1

    occupancy = fields.Integer(
        string="Occupancy",
        default=1,
        help="The occupancy/capacity/beds of the rooms (children included)",
    )
    min_price = fields.Float(
        "Min. Price",
        default=5.0,
        digits="Product Price",
        help="Setup the min price to prevent incidents while editing your prices.",
    )
    max_price = fields.Float(
        "Max. Price",
        default=200.0,
        digits="Product Price",
        help="Setup the max price to prevent incidents while editing your prices.",
    )

    @api.model
    def export_data(self, backend_record=None):
        """ Prepare the batch export of Room Types to Channel """
        room_types = self.odoo_id.get_room_types_by_property(
            backend_record.pms_property_id.id
        )
        return self.export_batch(
            backend_record=backend_record,
            domain=[
                ("id", "in", room_types.ids),
                # ("default_code", "=", "ECO")
            ],
        )
