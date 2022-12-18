# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class ChannelWubookPmsPropertyAvailabilityBinding(models.Model):
    _name = "channel.wubook.pms.property.availability"
    _inherit = "channel.wubook.binding"
    _inherits = {"pms.property": "odoo_id"}

    external_id = fields.Char(string="External ID")

    odoo_id = fields.Many2one(
        comodel_name="pms.property",
        string="Odoo ID",
        required=True,
        ondelete="cascade",
    )

    channel_wubook_availability_ids = fields.One2many(
        string="Wubook Availability",
        help="Property availability",
        comodel_name="channel.wubook.pms.availability",
        inverse_name="channel_wubook_property_availability_id",
    )

    def _is_synced_export(self):
        synced = super()._is_synced_export()
        if not synced:
            return False
        wubook_date_valid = fields.Date.today() - relativedelta(days=2)
        room_types_ids = (
            self.env["pms.room.type"]
            .search(
                [
                    ("channel_wubook_bind_ids.backend_id", "=", self.backend_id.id),
                ]
            )
            .ids
        )
        self.env.cr.execute(
            """
            SELECT avail.id
            FROM pms_availability AS avail
                LEFT JOIN channel_wubook_pms_availability AS binding
                    ON binding.odoo_id = avail.id
            WHERE avail.date >= %s
            AND avail.pms_property_id = %s
            AND avail.room_type_id IN %s
            AND (
                    (
                        binding.backend_id IS NULL
                        OR binding.backend_id != %s
                    )
                OR
                    (
                        binding.backend_id = %s
                        AND (
                            binding.sync_date_export IS NULL
                            OR binding.sync_date_export < binding.actual_write_date
                        )
                    )
                )
            """,
            (
                wubook_date_valid,
                self.backend_id.pms_property_id.id,
                tuple(room_types_ids) if room_types_ids else (0,),
                self.backend_id.id,
                self.backend_id.id,
            ),
        )
        avails_to_export = self.env.cr.fetchone()
        if avails_to_export:
            return False
        return True

    @api.model
    def export_data(self, backend_record=None):
        """Prepare the export of Availability to Channel"""
        return (
            self.env["channel.wubook.pms.property.availability"]
            .with_delay()
            .export_record(backend_record, backend_record.pms_property_id)
        )
