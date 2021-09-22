# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

NOSYNC = "-1"


class ChannelWubookBackendTypeRoomTypeClass(models.Model):
    _name = "channel.wubook.backend.type.room.type.class"
    _description = "Channel Wubook PMS Backend Type Room Type Class Map"

    backend_type_id = fields.Many2one(
        comodel_name="channel.wubook.backend.type",
        required=True,
        ondelete="cascade",
    )

    wubook_room_type = fields.Selection(
        string="Wubook Room Type",
        required=True,
        selection=[
            (NOSYNC, "--- Don't Sync ---"),
            ("1", "Room"),
            ("2", "Apartment"),
            ("3", "Bed"),
            ("4", "Unit"),
            ("5", "Bungalow"),
            ("6", "Tent"),
            ("7", "Villa"),
            ("8", "Chalet"),
            ("9", "RV park"),
        ],
    )
    room_type_shortname = fields.Char(
        string="Room Type Shortname",
    )

    _sql_constraints = [
        (
            "uniq",
            "unique(backend_type_id,wubook_room_type,room_type_shortname)",
            "Room Type and Shortname already used in another map line",
        ),
        (
            "room_type_shortname_uniq",
            "unique(backend_type_id,room_type_shortname)",
            "Shortname already used in another map line",
        ),
    ]

    def _filter_by_sync(self, sync=None):
        return self.filtered(
            lambda x: sync is None
            or not sync
            and x.wubook_room_type == NOSYNC
            or x.wubook_room_type != NOSYNC
        )

    def get_nosync_shortnames(self):
        return self._filter_by_sync(False).mapped("room_type_shortname")

    @api.constrains("backend_type_id", "wubook_room_type")
    def check_room_type_class_mapping(self):
        for rec in self:
            other = self.search(
                [
                    ("id", "not in", rec.ids),
                    ("wubook_room_type", "!=", NOSYNC),
                    ("backend_type_id", "=", rec.backend_type_id.id),
                    ("wubook_room_type", "=", rec.wubook_room_type),
                ]
            )
            if other:
                raise ValidationError(_("Room Type already used in another map line"))
