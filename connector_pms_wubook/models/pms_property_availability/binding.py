# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

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

    @api.model
    def export_data(self, backend_record=None):
        """ Prepare the export of Availability to Channel """
        return (
            self.env["channel.wubook.pms.property.availability"]
            .with_delay()
            .export_record(backend_record, backend_record.pms_property_id)
        )
