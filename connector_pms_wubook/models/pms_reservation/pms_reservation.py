# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.osv import expression


class PmsReservation(models.Model):
    _inherit = "pms.reservation"

    channel_external_ids = fields.Char(
        string="External IDs",
        compute="_compute_channel_external_ids",
        search="_search_channel_external_ids",
    )

    def _compute_channel_external_ids(self):
        for record in self:
            record.channel_external_ids = ",".join(
                record.folio_id.channel_wubook_bind_ids.mapped("external_id")
            )

    def _search_channel_external_ids(self, operator, value):
        folios = self.env["pms.folio"].search(
            [("channel_wubook_bind_ids.external_id", operator, value)]
        )
        return [("folio_id", "in", folios.ids)]

    @api.model
    def _name_search(
        self, name="", args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        args = args or []
        domain = []
        if name:
            domain = [
                "|",
                "|",
                ("name", operator, name),
                ("reservation_origin_code", operator, name),
                ("channel_wubook_bind_ids.external_id", operator, name),
            ]
        return self._search(
            expression.AND([domain + args]), limit=limit, access_rights_uid=name_get_uid
        )
