# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    # Fields declaration
    main_partner_id = fields.Many2one(
        "res.partner", string="Destination Partner fusion"
    )
    reservations_count = fields.Integer(
        "Reservations", compute="_compute_reservations_count"
    )
    folios_count = fields.Integer("Folios", compute="_compute_folios_count")
    unconfirmed = fields.Boolean("Unconfirmed", default=True)
    is_agency = fields.Boolean("Is Agency")

    # Compute and Search methods
    def _compute_reservations_count(self):
        pms_reservation_obj = self.env["pms.reservation"]
        for record in self:
            record.reservations_count = pms_reservation_obj.search_count(
                [("partner_id.id", "=", record.id)]
            )

    def _compute_folios_count(self):
        pms_folio_obj = self.env["pms.folio"]
        for record in self:
            record.folios_count = pms_folio_obj.search_count(
                [("partner_id.id", "=", record.id)]
            )

    # ORM Overrides
    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        if not args:
            args = []
        domain = [
            "|",
            "|",
            ("phone", operator, name),
            ("mobile", operator, name),
            ("email", operator, name),
        ]
        partners = self.search(
            domain + args,
            limit=limit,
        )
        res = partners.name_get()
        if limit:
            limit_rest = limit - len(partners)
        else:
            limit_rest = limit
        if limit_rest or not limit:
            args += [("id", "not in", partners.ids)]
            res += super(ResPartner, self).name_search(
                name, args=args, operator=operator, limit=limit_rest
            )
        return res
