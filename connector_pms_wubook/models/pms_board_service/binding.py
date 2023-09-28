# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ChannelWubookPmsBoardServiceBinding(models.Model):
    _name = "channel.wubook.pms.board.service"
    _inherit = "channel.wubook.binding"
    _inherits = {"pms.board.service": "odoo_id"}

    # override default Integer external ID
    external_id = fields.Char(
        string="External ID",
    )

    # binding fields
    odoo_id = fields.Many2one(
        comodel_name="pms.board.service",
        string="Odoo ID",
        required=True,
        ondelete="cascade",
    )
