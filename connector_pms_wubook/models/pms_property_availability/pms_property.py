# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PmsPropertyAvailability(models.Model):
    _inherit = "pms.property"

    channel_wubook_bind_ids = fields.One2many(
        comodel_name="channel.wubook.pms.property.availability",
        inverse_name="odoo_id",
        string="Channel Wubook PMS Bindings",
    )

    # TODO: move to pms???
    availability_ids = fields.One2many(
        string="Availability",
        comodel_name="pms.availability",
        inverse_name="pms_property_id",
    )
