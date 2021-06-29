# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ChannelWubookPmsReservationBinding(models.AbstractModel):
    _name = "channel.wubook.pms.reservation"
    _inherit = "channel.wubook.binding"
    _inherits = {"pms.reservation": "odoo_id"}

    odoo_id = fields.Many2one(
        comodel_name="pms.reservation",
        string="Odoo ID",
        required=True,
        ondelete="cascade",
    )
